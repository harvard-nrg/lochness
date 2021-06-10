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
        self.studies = ['StudyA']
        self.sources = ['Redcap', 'xNat', 'boX', 'mediaflux']
        self.poll_interval = 10


@pytest.fixture
def args():
    return Args('test_lochness')


class KeyringAndEncryptMediaflux(KeyringAndEncrypt):
    def __init__(self, tmp_dir):
        super().__init__(tmp_dir)
        token = Tokens()
        HOST, PORT, TRANSPORT, TOKEN, DOMAIN, USER, PASSWORD = \
                token.read_token_or_get_input('mediaflux')

        self.keyring['mediaflux.StudyA'] = {}
        self.keyring['mediaflux.StudyA']['HOST'] = HOST
        self.keyring['mediaflux.StudyA']['PORTJ'] = PORT
        self.keyring['mediaflux.StudyA']['TRANSPORT'] = TRANSPORT
        self.keyring['mediaflux.StudyA']['TOKEN'] = TOKEN
        self.keyring['mediaflux.StudyA']['DOMAIN'] = DOMAIN
        self.keyring['mediaflux.StudyA']['USER'] = USER
        self.keyring['mediaflux.StudyA']['PASSWORD'] = PASSWORD

        self.write_keyring_and_encrypt()



@pytest.fixture
def Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    KeyringAndEncryptMediaflux(args.outdir)

    lochness = config_load_test('tmp_lochness/config.yml', '')
    return lochness


def initialize_metadata(Lochness, study_name):
    df = pd.DataFrame({'Active': [1],
        'Consent': '1988.-09-16',
        'Subject ID': 'subject01',
        'Mediaflux': 'mediaflux.StudyA:5Yp0E'})
    df_loc = Path(Lochness['phoenix_root']) / 'GENERAL' / \
            study_name / f"{study_name}_metadata.csv"

    df.to_csv(df_loc, index=False)


def test_sync_from_empty(Lochness):
    dry=False
    study_name = 'StudyA'
    initialize_metadata(Lochness, study_name)

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=[study_name]):
        sync(Lochness, subject, dry)

    show_tree_then_delete('tmp_lochness')


