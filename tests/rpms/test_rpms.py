import lochness
import sys
from pathlib import Path
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

import cryptease as crypt
import lochness.config as config
import lochness.tree as tree
import lochness_create_template
from lochness_create_template import create_lochness_template
import pytest, shutil, os, sys, zipfile
import tempfile as tf
from subprocess import Popen
import time
import pandas as pd
import json

scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
from mock_args import mock_load

from lochness.rpms import initialize_metadata, sync



class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA']
        self.sources = ['Redcap', 'RPMS']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


@pytest.fixture
def args():
    return Args('test_lochness')

@pytest.fixture
def args_whole_process():
    return Args('tmp_lochness')

def create_fake_rpms_repo():
    # make REPO directory
    root = Path('RPMS_repo')
    root.mkdir(exist_ok=True)

    number_of_subjects = 5
    for subject_num in range(0, number_of_subjects):
        # create a data
        subject_dir = root / f'subject_{subject_num}'
        subject_dir.mkdir(exist_ok=True)

        df = pd.DataFrame({
            'record_id1': [f'subject_{subject_num}'],
            'Consent': '1988-09-16',
            'var1': f'var1_subject_{subject_num}',
            'var2': f'var2_subject_{subject_num}',
            'var3': f'var3_subject_{subject_num}',
            'xnat_id': f'StudyA:bwh:var3_subject_{subject_num}',
            'box_id': f'box.StudyA:var3_subject_{subject_num}',
            'last_modified': time.time()})

        df.to_csv(subject_dir / f'subject_{subject_num}.csv', index=False)


def test_updating_metadata_based_on_th_rpms(args):
    '''Test updating the metadata

    Current model
    =============

    - RPMS_PATH
        - subject01
          - subject01.csv
        - subject02
          - subject02.csv
        - subject03
          - subject03.csv
        - ...
    '''
    create_fake_rpms_repo()
    # create_lochness_template(args)
    dry = False
    Lochness = config.load('test_lochness/config.yml', '')
    # initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')



def test_create_lochness_template(args):
    create_fake_rpms_repo()
    # create_lochness_template(args)
    dry=False
    study_name = 'StudyA'
    Lochness = config.load('test_lochness/config.yml', '')

    initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        print(subject)
        for module in subject.rpms:
            print(module)
            break
        break


def test_sync(args):
    # create_lochness_template(args)
    dry=False
    study_name = 'StudyA'
    Lochness = config.load('test_lochness/config.yml', '')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        sync(Lochness, subject, dry)


def update_keyring_and_encrypt(tmp_lochness_dir: str):
    keyring_loc = Path(tmp_lochness_dir) / 'lochness.json'
    print(keyring_loc)
    with open(keyring_loc, 'r') as f:
        keyring = json.load(f)

    keyring['rpms.StudyA']['RPMS_PATH'] = str(
            Path(tmp_lochness_dir).absolute().parent / 'RPMS_repo')


    print(keyring)

    with open(keyring_loc, 'w') as f:
        json.dump(keyring, f)
    
    keyring_content = open(keyring_loc, 'rb')
    key = crypt.kdf('')
    crypt.encrypt(keyring_content, key,
            filename=Path(tmp_lochness_dir) / '.lochness.enc')


def test_sync_from_empty(args):
    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)
    update_keyring_and_encrypt(args.outdir)
    create_fake_rpms_repo()
    dry=False
    study_name = 'StudyA'
    Lochness = config.load(f'{args.outdir}/config.yml', '')
    initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        sync(Lochness, subject, dry)
    shutil.rmtree(args.outdir)


