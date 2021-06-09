import os
import yaml
import lochness
import logging
import zipfile
import shutil
from pathlib import Path
import tempfile as tf
import collections as col
import lochness.net as net
import lochness.tree as tree
from typing import List, Dict
import pandas as pd
from lochness.redcap.process_piis import process_and_copy_db


yaml.SafeDumper.add_representer(
    col.OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
logger = logging.getLogger(__name__)


def get_rpms_database(rpms_root_path) -> Dict[str, pd.DataFrame]:
    '''Return dictionary of RPMS database in pandas dataframes

    Key arguments:
        rpms_root_path: root of the RPMS sync directory, str.

    Returns:
        all_df_dict: all measures loaded as pandas dataframe in dict.
                     key: name of the measure extracted from the file name.
                     value: pandas dataframe of the measure database
        
    '''
    rpms_root_path = 'RPMS_repo'

    all_df_dict = {}
    for measure_file in Path(rpms_root_path).glob('*csv'):
        measure_name = measure_file.name.split('.')[0]
        df_tmp = pd.read_csv(measure_file)
        all_df_dict[measure_name] = df_tmp

    return all_df_dict


def initialize_metadata(Lochness: 'Lochness object',
                        study_name: str,
                        rpms_id_colname: str,
                        rpms_consent_colname: str) -> None:
    '''Initialize metadata.csv by pulling data from RPMS

    Key arguments:
        Lochness: Lochness object
        study_name: Name of the study, str.
        rpms_id_colname: Name of the ID field name in RPMS, str.
        rpms_consent_colname: Name of the consent date field name in RPMS,
                                str.

    '''
    study_rpms = Lochness['keyring'][f'rpms.{study_name}']
    rpms_root_path = study_rpms['RPMS_PATH']

    source_source_name_dict = {
        'beiwe': 'Beiwe', 'xnat': 'XNAT', 'dropbox': 'Drpbox',
        'box': 'Box', 'mediaflux': 'Mediaflux',
        'mindlamp': 'Mindlamp', 'daris': 'Daris', 'rpms': 'RPMS'}

    # get list of csv files from the rpms root
    all_df_dict = get_rpms_database(rpms_root_path)

    df = pd.DataFrame()
    # for each record in pulled information, extract subject ID and source IDs
    for measure, df_measure in all_df_dict.items():
        subject_dict = {'Subject ID': df_measure[rpms_id_colname]}

        # Consent date
        try:
            subject_dict['Consent'] = df_measure[rpms_consent_colname]
        except:
            subject_dict['Consent'] = '1988-09-16'

        for source, source_name in source_source_name_dict.items():
            try:
                subject_dict[source_name] = df_measure[f'{source}_id']
            except:
                pass

        df_tmp = pd.DataFrame.from_dict(subject_dict, orient='index')
        df = pd.concat([df, df_tmp.T])

    # Each subject may have more than one arms, which will result in more than
    # single item for the subject in the RPMS pulled `content`
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


def get_subject_data(all_df_dict: Dict[str, pd.DataFrame],
                     subject: object) -> Dict[str, pd.DataFrame]:
    '''Get subject data from the pandas dataframes in the dictionary'''

    subject_df_dict = {}
    for measure, measure_df in all_df_dict.items():
        subject_df = measure_df[measure_df.record_id1 == subject.id]
        subject_df_dict[measure] = subject_df

    return subject_df_dict




@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    logger.debug(f'exploring {subject.study}/{subject.id}')

    # for each subject
    subject_id = subject.id
    study_name = subject.study
    study_rpms = Lochness['keyring'][f'rpms.{study_name}']
    rpms_root_path = study_rpms['RPMS_PATH']

    # source data
    all_df_dict = get_rpms_database(rpms_root_path)
    subject_df_dict = get_subject_data(all_df_dict, subject)

    for measure, source_df in subject_df_dict.items():
        # target data
        dirname = tree.get('surveys',
                           subject.protected_folder,
                           processed=False,
                           BIDS=Lochness['BIDS'])
        target_df_loc = Path(dirname) / f"{subject_id}_{measure}.csv"

        proc_folder = tree.get('surveys',
                               subject.general_folder,
                               processed=True,
                               BIDS=Lochness['BIDS'])
        proc_dst = Path(proc_folder) / f"{subject_id}_{measure}.csv"

        # load the time of the lastest data pull from daris
        # estimated from the mtime of the zip file downloaded
        if Path(target_df_loc).is_file():
            latest_pull_mtime = target_df_loc.stat().st_mtime
        else:
            latest_pull_mtime = 0

        # if last_modified date > latest_pull_mtime, pull the data
        if not source_df['last_modified'].max() > latest_pull_mtime:
            print('No new updates')
            break

        if not dry:
            Path(dirname).mkdir(exist_ok=True)
            os.chmod(dirname, 0o0755)
            source_df.to_csv(target_df_loc, index=False)
            os.chmod(target_df_loc, 0o0755)
            process_and_copy_db(Lochness, subject, target_df_loc, proc_dst)


def update_study_metadata(subject, content: List[dict]) -> None:
    '''update metadata csv based on the rpms content: source_id'''

    sources = ['XNAT', 'Box', 'Mindlamp', 'Mediaflux', 'Daris']

    orig_metadata_df = pd.read_csv(subject.metadata_csv)

    subject_bool = orig_metadata_df['Subject ID'] == subject.id
    subject_index = orig_metadata_df[subject_bool].index
    subject_series = orig_metadata_df.loc[subject_index]
    other_metadata_df = orig_metadata_df[~subject_bool]

    updated = False
    for source in sources:
        if f"{source.lower()}_id" in content[0]:  # exist in the rpms
            source_id = content[0][f"{source.lower()}_id"]
            if source not in subject_series:
                subject_series[source] = f'{source.lower()}.{source_id}'
                updated = True

            # subject already has the information
            elif subject_series.iloc[0][source] != f'{source.lower()}.{source_id}':
                subject_series.iloc[0][source] = \
                        f'{source.lower()}.{source_id}'
                updated = True
            else:
                pass

    if updated:
        new_metadata_df = pd.concat([other_metadata_df, subject_series])

        # overwrite metadata
        new_metadata_df.to_csv(subject.metadata_csv, index=False)

