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
from lochness.redcap.process_piis import load_raw_return_proc_json
from lochness.redcap.process_piis import read_pii_mapping_to_dict
from typing import List


logger = logging.getLogger(__name__)


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


def process_and_copy_json(Lochness, subject, dst,
                          redcap_subject, _redcap_project):
    '''Process PII and copy the json to GENERAL/survey/processed'''
    pii_table_loc = get_PII_table_loc(Lochness, subject.study)

    # don't run this if the pii_table in the config.yml is missing
    if pii_table_loc != False and pii_table_loc != '':
        # process PII here
        pii_str_proc_dict = read_pii_mapping_to_dict(pii_table_loc)
        processed_content = load_raw_return_proc_json(
                dst, pii_str_proc_dict, subject.id)

        # save processed content to general processed
        proc_folder = tree.get('surveys',
                               subject.general_folder,
                               processed=True)
        fname = f'{redcap_subject}.{_redcap_project}.json'
        proc_dst = Path(proc_folder) / fname

        # double check the pii string processing dict once more
        # if it's empty, don't copy it over to general
        if pii_str_proc_dict != {}:
            lochness.atomic_write(proc_dst, processed_content)


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
            dst_folder = tree.get('surveys', subject.protected_folder)
            fname = f'{redcap_subject}.{_redcap_project}.json'
            dst = Path(dst_folder) / fname


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
                    process_and_copy_json(Lochness, subject, dst,
                                          redcap_subject,
                                          _redcap_project)
                    update_study_metadata(subject, json.loads(content))
                    
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
                        process_and_copy_json(Lochness, subject, dst,
                                              redcap_subject,
                                              _redcap_project)
                        update_study_metadata(subject, json.loads(content))


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


def get_PII_table_loc(Lochness, study):
    ''' get study specific deidentify flag with a safe default '''
    value = Lochness.get('redcap', dict()) \
                    .get(study, dict()) \
                    .get('pii_table', False)

    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return ''
    return value


def iterate(subject):
    '''generator for redcap instance and subject'''
    for instance, ids in iter(subject.redcap.items()):
        for id_inst in ids:
            yield instance, id_inst



def update_study_metadata(subject, content: List[dict]) -> None:
    '''update metadata csv based on the redcap content: source_id'''


    sources = ['XNAT', 'Box', 'Mindlamp', 'Mediaflux']

    orig_metadata_df = pd.read_csv(subject.metadata_csv)

    subject_bool = orig_metadata_df['Subject ID'] == subject.id
    subject_series = orig_metadata_df[subject_bool]
    other_metadata_df = orig_metadata_df[~subject_bool]

    updated = False
    for source in sources:
        if f"{source.lower()}_id" in content[0]:  # exist in the redcap
            source_id = content[0][f"{source.lower()}_id"]
            if source not in subject_series:
                subject_series[source] = f'{source.lower()}.{source_id}'
                updated = True

            # subject already has the information
            elif subject_series[source][0] != f'{source.lower()}.{source_id}':
                subject_series[source] = \
                        f'{source.lower()}.{source_id}'
                updated = True
            else:
                pass

    if updated:
        new_metadata_df = pd.concat([other_metadata_df, subject_series])

        # overwrite metadata
        new_metadata_df.to_csv(subject.metadata_csv, index=False)
