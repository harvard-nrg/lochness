import os
import sys
import re
import json
import lochness
import logging
import requests
import lochness.net as net
import collections as col
import lochness.tree as tree
from pathlib import Path
import pandas as pd
import datetime
from typing import List
import tempfile as tf
from lochness.redcap.process_piis import process_and_copy_db


logger = logging.getLogger(__name__)


def get_field_names_from_redcap(api_url: str,
                                api_key: str,
                                study_name: str) -> list:
    '''Return all field names from redcap database'''

    record_query = {
        'token': api_key,
        'content': 'exportFieldNames',
        'format': 'json',
    }

    # pull field names from REDCap for the study
    content = post_to_redcap(api_url,
                             record_query,
                             f'initializing data {study_name}')

    # load pulled information as list of dictionary : data
    with tf.NamedTemporaryFile(suffix='tmp.json') as tmpfilename:
        lochness.atomic_write(tmpfilename.name, content)
        with open(tmpfilename.name, 'r') as f:
            data = json.load(f)

    field_names = []
    for item in data:
        field_names.append(item['original_field_name'])

    return field_names


def initialize_metadata(Lochness: 'Lochness object',
                        study_name: str,
                        redcap_id_colname: str,
                        redcap_consent_colname: str) -> None:
    '''Initialize metadata.csv by pulling data from REDCap

    Key arguments:
        Lochness: Lochness object
        study_name: Name of the study, str.
        redcap_id_colname: Name of the ID field name in REDCap, str.
        redcap_consent_colname: Name of the consent date field name in REDCap,
                                str.

    '''
    study_redcap = Lochness['keyring'][f'redcap.{study_name}']
    api_url = study_redcap['URL'] + '/api/'
    api_key = study_redcap['API_TOKEN'][study_name]

    source_source_name_dict = {
        'beiwe': 'Beiwe', 'xnat': 'XNAT', 'dropbox': 'Drpbox',
        'box': 'Box', 'mediaflux': 'Mediaflux',
        'mindlamp': 'Mindlamp', 'daris': 'Daris', 'rpms': 'RPMS'}

    record_query = {
        'token': api_key,
        'content': 'record',
        'format': 'json',
        'fields[0]': redcap_id_colname,
    }

    # # only pull source_names
    field_num = 2
    for source, source_name in source_source_name_dict.items():
        record_query[f"fields[{field_num}]"] = f"source_id"

    # pull all records from REDCap for the study
    try:
        content = post_to_redcap(api_url,
                                 record_query,
                                 f'initializing data {study_name}')
    except:  # field names are not set yet
        record_query = {
            'token': api_key,
            'content': 'record',
            'format': 'json',
        }
        content = post_to_redcap(api_url,
                                 record_query,
                                 f'initializing data {study_name}')

    # load pulled information as list of dictionary : data
    with tf.NamedTemporaryFile(suffix='tmp.json') as tmpfilename:
        lochness.atomic_write(tmpfilename.name, content)
        with open(tmpfilename.name, 'r') as f:
            data = json.load(f)

    df = pd.DataFrame()
    # for each record in pulled information, extract subject ID and source IDs
    for item in data:
        subject_dict = {'Subject ID': item[redcap_id_colname]}

        # Consent date
        try:
            subject_dict['Consent'] = item[redcap_consent_colname]
        except:
            subject_dict['Consent'] = '1988-09-16'

        for source, source_name in source_source_name_dict.items():
            try:
                subject_dict[source_name] = item[f'{source}_id']
            except:
                pass

        df_tmp = pd.DataFrame.from_dict(subject_dict, orient='index')
        df = pd.concat([df, df_tmp.T])

    # Each subject may have more than one arms, which will result in more than
    # single item for the subject in the redcap pulled `content`
    # remove empty lables
    df_final = pd.DataFrame()
    for _, table in df.groupby(['Subject ID']):
        pad_filled = table.fillna(
                method='ffill').fillna(method='bfill').iloc[0]
        df_final = pd.concat([df_final, pad_filled], axis=1)
    df_final = df_final.T

    # register all of the lables as active
    df_final['Active'] = 1

    # reorder columns
    main_cols = ['Active', 'Consent', 'Subject ID']
    df_final = df_final[main_cols + \
            [x for x in df_final.columns if x not in main_cols]]

    general_path = Path(Lochness['phoenix_root']) / 'GENERAL'
    metadata_study = general_path / study_name / f"{study_name}_metadata.csv"
    df_final.to_csv(metadata_study, index=False)



def check_if_modified(subject_id: str,
                      existing_json: str,
                      df: pd.DataFrame) -> bool:
    '''check if subject data has been modified in the data entry trigger db

    Comparing unix times of the json modification and lastest redcap update
    '''

    json_modified_time = Path(existing_json).stat().st_mtime  # in unix time

    subject_df = df[df.record == subject_id]

    # if the subject does not exist in the DET_DB, return False
    if len(subject_df) < 1:
        return False

    lastest_update_time = subject_df.loc[
            subject_df['timestamp'].idxmax()].timestamp

    if lastest_update_time > json_modified_time:
        return True
    else:
        return False


def get_data_entry_trigger_df(Lochness: 'Lochness') -> pd.DataFrame:
    '''Read Data Entry Trigger database as dataframe'''
    if 'redcap' in Lochness:
        if 'data_entry_trigger_csv' in Lochness['redcap']:
            db_loc = Lochness['redcap']['data_entry_trigger_csv']
            if Path(db_loc).is_file():
                db_df = pd.read_csv(db_loc)
                db_df['record'] = db_df['record'].astype(str)
                return db_df

    db_df = pd.DataFrame({'record':[]})
    # db_df = pd.DataFrame()
    return db_df


@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):

    # load dataframe for redcap data entry trigger
    db_df = get_data_entry_trigger_df(Lochness)

    logger.debug(f'exploring {subject.study}/{subject.id}')
    deidentify = deidentify_flag(Lochness, subject.study)

    logger.debug(f'deidentify for study {subject.study} is {deidentify}')

    for redcap_instance, redcap_subject in iterate(subject):
        for redcap_project, api_url, api_key in redcap_projects(
                Lochness, subject.study, redcap_instance):
            # process the response content
            _redcap_project = re.sub(r'[\W]+', '_', redcap_project.strip())

            # default location to protected folder
            dst_folder = tree.get('surveys',
                                  subject.protected_folder,
                                  processed=False)
            fname = f'{redcap_subject}.{_redcap_project}.json'
            dst = Path(dst_folder) / fname

            # PII processed content to general processed
            proc_folder = tree.get('surveys',
                                   subject.general_folder,
                                   processed=True)
            proc_dst = Path(proc_folder) / fname

            # check if the data has been updated by checking the redcap data
            # entry trigger db
            if dst.is_file():
                if check_if_modified(redcap_subject, dst, db_df):
                    pass  # if modified, carry on
                else:
                    print("\n----")
                    print("No updates - not downloading REDCap data")
                    print("----\n")
                    break  # if not modified break

            print("\n----")
            print("Downloading REDCap data")
            print("----\n")
            _debug_tup = (redcap_instance, redcap_project, redcap_subject)

            record_query = {
                'token': api_key,
                'content': 'record',
                'format': 'json',
                'records': redcap_subject
            }

            if deidentify:
                # get fields that aren't identifiable and narrow record query
                # by field name
                metadata_query = {
                    'token': api_key,
                    'content': 'metadata',
                    'format': 'json'
                }

                content = post_to_redcap(api_url, metadata_query, _debug_tup)
                metadata = json.loads(content)
                field_names = []
                for field in metadata:
                    if field['identifier'] != 'y':
                        field_names.append(field['field_name'])
                record_query['fields'] = ','.join(field_names)

            # post query to redcap
            content = post_to_redcap(api_url, record_query, _debug_tup)

            # check if response body is nothing but a sad empty array
            if content.strip() == '[]':
                logger.info(f'no redcap data for {redcap_subject}')
                continue

            if not dry:
                if not os.path.exists(dst):
                    logger.debug(f'saving {dst}')
                    lochness.atomic_write(dst, content)
                    process_and_copy_db(Lochness, subject, dst, proc_dst)
                    # update_study_metadata(subject, json.loads(content))
                    
                else:
                    # responses are not stored atomically in redcap
                    crc_src = lochness.crc32(content.decode('utf-8'))
                    crc_dst = lochness.crc32file(dst)

                    if crc_dst != crc_src:
                        print('different - crc32: downloading data')
                        logger.warn(f'file has changed {dst}')
                        lochness.backup(dst)
                        logger.debug(f'saving {dst}')
                        lochness.atomic_write(dst, content)
                        process_and_copy_db(Lochness, subject, dst, proc_dst)
                        # update_study_metadata(subject, json.loads(content))


class REDCapError(Exception):
    pass


def redcap_projects(Lochness, phoenix_study, redcap_instance):
    '''get redcap api_url and api_key for a phoenix study'''
    Keyring = Lochness['keyring']
    # check for mandatory keyring items
    if 'REDCAP' not in Keyring['lochness']:
        raise KeyringError("lochness > REDCAP not found in keyring")
    if redcap_instance not in Keyring:
        raise KeyringError(f"{redcap_instance} not found in keyring")
    if 'URL' not in Keyring[redcap_instance]:
        raise KeyringError(f"{redcap_instance} > URL not found in keyring")
    if 'API_TOKEN' not in Keyring[redcap_instance]:
        raise KeyringError(f"{redcap_instance} > API_TOKEN "
                           "not found in keyring")

    api_url = Keyring[redcap_instance]['URL'].rstrip('/') + '/api/'

    # check for soft keyring items
    if phoenix_study not in Keyring['lochness']['REDCAP']:
        logger.debug(f'lochness > REDCAP > {phoenix_study}'
                     'not found in keyring')
        return
    if redcap_instance not in Keyring['lochness']['REDCAP'][phoenix_study]:
        logger.debug(f'lochness > REDCAP > {phoenix_study} '
                     f'> {redcap_instance} not found in keyring')
        return

    # begin generating project,api_url,api_key tuples
    for project in Keyring['lochness']['REDCAP']\
            [phoenix_study][redcap_instance]:
        if project not in Keyring[redcap_instance]['API_TOKEN']:
            raise KeyringError(f"{redcap_instance} > API_TOKEN > {project}"
                               "not found in keyring")
        api_key = Keyring[redcap_instance]['API_TOKEN'][project]
        yield project, api_url, api_key


def post_to_redcap(api_url, data, debug_tup):
    r = requests.post(api_url, data=data, stream=True, verify=False)
    if r.status_code != requests.codes.OK:
        raise REDCapError(f'redcap url {r.url} responded {r.status_code}')
    content = r.content

    # you need the number bytes read before any decoding
    content_len = r.raw._fp_bytes_read

    # verify response content integrity
    if 'content-length' not in r.headers:
        logger.warn('server did not return a content-length header, '
                    f'can\'t verify response integrity for {debug_tup}')
    else:
        expected_len = int(r.headers['content-length'])
        if content_len != expected_len:
            raise REDCapError(
                    f'content length {content_len} does not match '
                    f'expected length {expected_len} for {debug_tup}')
    return content


class KeyringError(Exception):
    pass


def deidentify_flag(Lochness, study):
    ''' get study specific deidentify flag with a safe default '''
    value = Lochness.get('redcap', dict()) \
                    .get(study, dict()) \
                    .get('deidentify', False)

    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return False
    return value


def deidentify_flag(Lochness, study):
    ''' get study specific deidentify flag with a safe default '''
    value = Lochness.get('redcap', dict()) \
                    .get(study, dict()) \
                    .get('deidentify', False)

    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return False
    return value


def iterate(subject):
    '''generator for redcap instance and subject'''
    for instance, ids in iter(subject.redcap.items()):
        for id_inst in ids:
            yield instance, id_inst



def update_study_metadata(subject, content: List[dict]) -> None:
    '''update metadata csv based on the redcap content: source_id'''


    sources = ['XNAT', 'Box', 'Mindlamp', 'Mediaflux', 'Daris']

    orig_metadata_df = pd.read_csv(subject.metadata_csv)

    subject_bool = orig_metadata_df['Subject ID'] == subject.id
    subject_index = orig_metadata_df[subject_bool].index
    subject_series = orig_metadata_df.loc[subject_index]
    other_metadata_df = orig_metadata_df[~subject_bool]

    updated = False
    for source in sources:
        if f"{source.lower()}_id" in content[0]:  # exist in the redcap
            source_id = content[0][f"{source.lower()}_id"]
            if source not in subject_series:
                subject_series[source] = f'{source.lower()}.{source_id}'
                updated = True

            # subject already has the information
            elif subject_series.iloc[0][source] != \
                    f'{source.lower()}.{source_id}':
                subject_series.iloc[0][source] = \
                        f'{source.lower()}.{source_id}'
                updated = True
            else:
                pass

    if updated:
        new_metadata_df = pd.concat([other_metadata_df, subject_series])

        # overwrite metadata
        new_metadata_df.to_csv(subject.metadata_csv, index=False)
