import lochness.redcap
import pandas as pd
pd.set_option('max_columns', 50)
from lochness.redcap import check_if_modified, get_data_entry_trigger_df
import shutil
from lochness.redcap import iterate, redcap_projects, post_to_redcap
from lochness.redcap import update_study_metadata
import json
import re
import os
from lochness import tree
from lochness import config
from pathlib import Path
import pandas as pd
import tempfile
from typing import List

import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
from config.test_config import create_config
from mock_args import LochnessArgs, mock_load
from lochness import keyring


class Args():
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = scripts_dir / 'config.yml'
        self.archive_base = None
    def __str__(self):
        return 'haha'


class FakeSubject():
    def __init__(self, subject: 'Lochness.subject'):
        self.id = subject.id
        self.metadata_csv = subject.metadata_csv


def test_redcap_sync_module():
    print()
    args = Args()
    args.source = ['redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)
    Lochness['phoenix_root'] = '/Users/kc244/lochness/tests/PHOENIX'

    real_keyring = keyring.load_encrypted_keyring('/Users/kc244/.lochness.enc')
    Lochness['keyring'] = real_keyring

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        print(subject)
        for module in subject.redcap:
            dst_folder = tree.get('surveys', subject.protected_folder)
            # fname = os.path.join(dst_folder,
                                 # f'{redcap_subject}.{_redcap_project}.json')
            fname = os.path.join(dst_folder,
                                 'a.b.json')
            dst = os.path.join(dst_folder, fname)

            print(module)
            print(module)
            print(fname)
            print(dst_folder)
            print(dst)
            deidentify = lochness.redcap.deidentify_flag(Lochness, subject.study)

            # load dataframe for redcap data entry trigger
            db_df = get_data_entry_trigger_df(Lochness)
            for redcap_instance, redcap_subject in iterate(subject):
                for redcap_project, api_url, api_key in redcap_projects(
                        Lochness, subject.study, redcap_instance):
                    # process the response content
                    _redcap_project = re.sub(r'[\W]+', '_', redcap_project.strip())

                    # default location to protected folder
                    dst_folder = tree.get('surveys', subject.protected_folder)
                    fname = f'{redcap_subject}.{_redcap_project}.json'
                    dst = Path(dst_folder) / fname


                    _debug_tup = (redcap_instance, redcap_project, redcap_subject)

                    record_query = {
                        'token': api_key,
                        'content': 'record',
                        'format': 'json',
                        'records': redcap_subject
                    }

                    # post query to redcap
                    content = post_to_redcap(api_url, record_query, _debug_tup)
                    # print(content)

                    # if not os.path.exists(dst):
                        # lochness.atomic_write(dst, content)
                        # process_and_copy_json(Lochness, subject, dst,
                                              # redcap_subject,
                                              # _redcap_project)


def test_get_data_entry_trigger_df_existing_file():
    args = Args()
    args.source = ['redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)

    df = get_data_entry_trigger_df(Lochness)
    print(df)


def test_get_data_entry_trigger_df_missing_file():
    args = Args()
    args.source = ['redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)

    Lochness['redcap'].pop('data_entry_trigger_csv')
    df = get_data_entry_trigger_df(Lochness)
    print(df)


def test_check_if_modified():
    df = pd.DataFrame({'record':[1001], 'timestamp':10})
    df['record'] = df['record'].astype(str)

    with tempfile.NamedTemporaryFile(delete=False,
                                     suffix='tmp.json') as tmpfilename:
        with open(tmpfilename.name, 'w') as f:
            f.write('tmp.json')
        # higher the timestamp -> more recent update
        # lower the timestamp -> older update
        df.loc[1, 'record'] = 'hahaha'
        # redcap updated very recently
        df.loc[1, 'timestamp'] = Path(tmpfilename.name).stat().st_mtime + 100
        subject_id = 'hahaha'

        existing_json = tmpfilename.name
        assert check_if_modified(subject_id, existing_json, df)

    with tempfile.NamedTemporaryFile(delete=False,
                                     suffix='tmp.json') as tmpfilename:
        with open(tmpfilename.name, 'w') as f:
            f.write('tmp.json')

        # higher the timestamp -> more recent update
        # lower the timestamp -> older update
        df.loc[1, 'record'] = 'hahaha'
        # no redcap update after last download
        df.loc[1, 'timestamp'] = Path(tmpfilename.name).stat().st_mtime - 100
        subject_id = 'hahaha'

        existing_json = tmpfilename.name
        assert ~check_if_modified(subject_id, existing_json, df)


def test_check_if_modified_with_sync_execution():
    args = Args()
    args.source = ['redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)


    with tempfile.NamedTemporaryFile(delete=False,
                                     suffix='tmp.json') as tmpfilename:
        with open(tmpfilename.name, 'w') as f:
            f.write('tmp.json')

        df = pd.DataFrame({'record':[1001], 'timestamp':10})
        df['record'] = df['record'].astype(str)
        # higher the timestamp -> more recent update
        # lower the timestamp -> older update
        df.loc[1, 'record'] = 'hahaha'

        # no redcap update after last download
        df.loc[1, 'timestamp'] = Path(tmpfilename.name).stat().st_mtime - 100
        subject_id = 'hahaha'

        Lochness['redcap']['data_entry_trigger_csv']
        existing_json = tmpfilename.name
        assert ~check_if_modified(subject_id, existing_json, df)

    # execute sync
    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        # print(subject)
        for module in subject.redcap:
            lochness.redcap.sync(Lochness, subject, dry=True)



def test_update_metadata_after_pool():
    print()
    args = Args()
    args.source = ['redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)
    Lochness['phoenix_root'] = '/Users/kc244/lochness/tests/PHOENIX'

    real_keyring = keyring.load_encrypted_keyring('/Users/kc244/.lochness.enc')
    Lochness['keyring'] = real_keyring

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        for module in subject.redcap:
            dst_folder = tree.get('surveys', subject.protected_folder)
            # fname = os.path.join(dst_folder,
                                 # f'{redcap_subject}.{_redcap_project}.json')
            fname = os.path.join(dst_folder,
                                 'a.b.json')
            dst = os.path.join(dst_folder, fname)

            deidentify = lochness.redcap.deidentify_flag(Lochness, subject.study)

            # load dataframe for redcap data entry trigger
            db_df = get_data_entry_trigger_df(Lochness)
            for redcap_instance, redcap_subject in iterate(subject):
                for redcap_project, api_url, api_key in redcap_projects(
                        Lochness, subject.study, redcap_instance):
                    # process the response content
                    _redcap_project = re.sub(r'[\W]+', '_', redcap_project.strip())

                    # default location to protected folder
                    dst_folder = tree.get('surveys', subject.protected_folder)
                    fname = f'{redcap_subject}.{_redcap_project}.json'
                    dst = Path(dst_folder) / fname


                    _debug_tup = (redcap_instance, redcap_project, redcap_subject)

                    record_query = {
                        'token': api_key,
                        'content': 'record',
                        'format': 'json',
                        'records': redcap_subject
                    }

                    # post query to redcap
                    content = post_to_redcap(api_url, record_query, _debug_tup)
                    metadata = json.loads(content)
                    # print(metadata[0])
                    # print(metadata[0]['subject_id'])
                    if Lochness['redcap']['update_metadata']:
                        metadata[0]['Box_id'] = 'StudyA:1234'
                        metadata[0]['Mindlamp_id'] = 'StudyA:U12341234'
                        metadata[0]['Mediaflux_id'] = 'StudyA:haho'
                        metadata[0]['XNAT_id'] = 'StudyA:HCPEP-BWH:test'

                        tmp_metadata_csv_loc = 'tmp.csv'
                        shutil.copy(subject.metadata_csv,
                                    tmp_metadata_csv_loc)
                        fake_subject = FakeSubject(subject)
                        fake_subject.metadata_csv = tmp_metadata_csv_loc
                        update_study_metadata(fake_subject, metadata)


    tmp_created = pd.read_csv('tmp.csv')
    assert tmp_created.iloc[0]['XNAT'] == \
            f"xnat.{metadata[0]['XNAT_id']}"
    assert tmp_created.iloc[0]['Mediaflux'] == \
            f"mediaflux.{metadata[0]['Mediaflux_id']}"
    assert tmp_created.iloc[0]['Mindlamp'] == \
            f"mindlamp.{metadata[0]['Mindlamp_id']}"
    os.remove('tmp.csv')



def prac():
    {'Box_id':'StudyA:1234',
    'Mindlamp_id':'StudyA:U12341234',
    'Mediaflux_id':'StudyA:haho'}
    pass
