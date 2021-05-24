import lochness.mindlamp
from lochness import config
import os
from pathlib import Path
import pandas as pd
pd.set_option('max_columns', 50)
pd.set_option('max_rows', 500)

import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from test_lochness import Args, Tokens, KeyringAndEncrypt, args, SyncArgs
from test_lochness import show_tree_then_delete, config_load_test
from test_lochness import initialize_metadata_test
from lochness_create_template import create_lochness_template

from sync import do

# from config.test_config import create_config
import LAMP
from typing import Tuple, List
from lochness.mindlamp import get_study_lamp, get_participants_lamp
from lochness.mindlamp import get_activities_lamp, get_sensors_lamp
from lochness.mindlamp import get_activity_events_lamp
from lochness.mindlamp import get_sensor_events_lamp
from lochness.mindlamp import sync
import json



class TokensMindlamp(Tokens):
    def __init__(self):
        super().__init__()

    def get_mindlamp_token(self):
        if self.token_and_url_file.is_file():
            df = pd.read_csv(self.token_and_url_file)
            token = df.iloc[0]['token']
            access_key = df.iloc[0]['access_key']
            secret_key = df.iloc[0]['secret_key']
            api_url = df.iloc[0]['api_url']
        else:
            token = input('Enter token: ')
            access_key = input('Enter access_key: ')
            secret_key = input('Enter secret_key: ')
            api_url = input('Enter api_url: ')

        return token, access_key, secret_key, api_url


class KeyringAndEncryptMindlamp(KeyringAndEncrypt):
    def __init__(self, tmp_dir):
        super().__init__(tmp_dir)
        token = TokensMindlamp()
        mindlamp_token, access_key, secret_key, api_url = \
                token.get_mindlamp_token()

        self.keyring['mindlamp.StudyA'] = {}
        self.keyring['mindlamp.StudyA']['ACCESS_KEY'] = access_key
        self.keyring['mindlamp.StudyA']['SECRET_KEY'] = secret_key
        self.keyring['mindlamp.StudyA']['URL'] = api_url

        self.write_keyring_and_encrypt()


def test_lamp_modules():
    token = TokensMindlamp()
    mindlamp_token, access_key, secret_key, api_url = token.get_mindlamp_token()
    LAMP.connect(access_key, secret_key)
    study_id, study_name = get_study_lamp(LAMP)
    subject_ids = get_participants_lamp(LAMP, study_id)

    for subject_id in subject_ids:
        if subject_id == 'U7045332804':
            print(subject_id)
            # activity_dicts = get_activities_lamp(LAMP, subject_id)
            activity_dicts = get_activity_events_lamp(LAMP, subject_id)
            sensor_dicts = get_sensor_events_lamp(LAMP, subject_id)
            # print(activity_dicts)
            # print(sensor_dicts)

            # with open('activity_data.json', 'w') as f:
                # json.dump(activity_dicts, f)

            # with open('sensor_data.json', 'w') as f:
                # json.dump(sensor_dicts, f)
            # break

    # print(os.popen('tree').read())
    # os.remove('activity_data.json')
    # os.remove('seonsor_data.json')


def test_sync_mindlamp(args):
    syncArgs = SyncArgs(args.outdir)
    syncArgs.studies = ['StudyA']
    sources = ['mindlamp']
    syncArgs.update_source(sources)

    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    _ = KeyringAndEncryptMindlamp(args.outdir)


    phoenix_root = args.outdir / 'PHOENIX'
    information_to_add_to_metadata = {'mindlamp': {'subject_id': '1001',
                                                   'source_id': 'U7045332804'}}
    
    initialize_metadata_test(phoenix_root, 'StudyA',
                             information_to_add_to_metadata)
    Lochness = config_load_test(syncArgs.config)
    for subject in lochness.read_phoenix_metadata(Lochness, syncArgs.studies):
        sync(Lochness, subject, False)

    show_tree_then_delete('tmp_lochness')


def test_do_with_mindlamp(args):
    syncArgs = SyncArgs(args.outdir)
    sources = ['mindlamp']
    syncArgs.update_source(sources)

    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    _ = KeyringAndEncryptMindlamp(args.outdir)


    phoenix_root = args.outdir / 'PHOENIX'
    information_to_add_to_metadata = {'mindlamp': {'subject_id': '1001',
                                                   'source_id': 'U7045332804'}}
    initialize_metadata_test(phoenix_root, 'StudyA',
                             information_to_add_to_metadata)
    
    do(syncArgs)
    show_tree_then_delete('tmp_lochness')
