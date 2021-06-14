import lochness
from lochness.mediaflux import sync
import lochness.config as config

from pathlib import Path
import sys

import pytest
import shutil
import os

import zipfile
import tempfile as tf
import json
import cryptease as crypt
import pandas as pd

lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))
from lochness_create_template import create_lochness_template

from test_lochness import Args, Tokens, KeyringAndEncrypt, args, Lochness
from test_lochness import show_tree_then_delete, config_load_test


class Args(Args):
    def __init__(self, root_dir):
        super().__init__(root_dir)
        self.studies = ['PrescientAD']
        self.sources = ['Redcap', 'xNat', 'boX', 'mediaflux']
        self.poll_interval = 10


@pytest.fixture
def args():
    return Args('test_lochness')


class KeyringAndEncryptMediaflux(KeyringAndEncrypt):
    def __init__(self, tmp_dir, study):
        super().__init__(tmp_dir)
        token = Tokens()
        HOST, PORT, TRANSPORT, TOKEN, DOMAIN, USER, PASSWORD = \
                token.read_token_or_get_input('mediaflux')

        self.keyring[f'mediaflux.{study}'] = {}
        self.keyring[f'mediaflux.{study}']['HOST'] = HOST
        self.keyring[f'mediaflux.{study}']['PORT'] = PORT
        self.keyring[f'mediaflux.{study}']['TRANSPORT'] = TRANSPORT
        # self.keyring['mediaflux.StudyA']['TOKEN'] = TOKEN
        self.keyring[f'mediaflux.{study}']['DOMAIN'] = DOMAIN
        self.keyring[f'mediaflux.{study}']['USER'] = USER
        self.keyring[f'mediaflux.{study}']['PASSWORD'] = PASSWORD

        self.write_keyring_and_encrypt()


@pytest.fixture
def args_and_Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    for study in args.studies:
        KeyringAndEncryptMediaflux(args.outdir, study)

    lochness = config_load_test('tmp_lochness/config.yml', '')

    return args, lochness


def initialize_metadata(Lochness, study_name):
    df = pd.DataFrame({'Active': [1, 1, 1],
        'Consent': ['1988-09-16', '1988-09-16', '1988-09-16'],
        'Subject ID': ['subject01', 'subject02', 'subject03'],
        'Mediaflux': [f'mediaflux.{study_name}:AD123453',
                      f'mediaflux.{study_name}:AD124352',
                      f'mediaflux.{study_name}:AD124539']
        })

    df_loc = Path(Lochness['phoenix_root']) / 'GENERAL' / \
            study_name / f"{study_name}_metadata.csv"

    df.to_csv(df_loc, index=False)


def test_sync_from_empty(args_and_Lochness):
    args, Lochness = args_and_Lochness
    dry=False
    for study_name in args.studies:
        initialize_metadata(Lochness, study_name)
        Lochness['mediaflux'][study_name]['namespace'] = \
            '/projects/proj-5070_prescient-1128.4.380' \
            '/example_mediaflux_root/' + study_name

        for subject in lochness.read_phoenix_metadata(Lochness,
                                                      studies=[study_name]):
            sync(Lochness, subject, dry)

    show_tree_then_delete('tmp_lochness')

