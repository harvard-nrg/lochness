import lochness
from lochness.daris import daris_download, collect_all_daris_metadata, sync
import lochness.config as config

from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

from lochness_create_template import create_lochness_template
import pytest
import shutil
import os

scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
import zipfile
import tempfile as tf
import json
import cryptease as crypt
import pandas as pd


class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA']
        self.sources = ['Redcap', 'xNat', 'boX', 'daris']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


@pytest.fixture
def args():
    return Args('test_lochness')


def test_daris_download():
    daris_uid = 'subject01'
    latest_pull_mtime = 0
    token, url, project_cid = get_token_url_project_cid()
    dst_zipfile = 'tmp.zip'

    daris_download(daris_uid, latest_pull_mtime, token,
                   project_cid, url, dst_zipfile)

    tmpdir = tf.mkdtemp(dir='.', prefix='.')
    with zipfile.ZipFile(dst_zipfile, 'r') as zip_ref:
        zip_ref.extractall(tmpdir)

    nfiles_in_dirs = []
    for root, dirs, files in os.walk(tmpdir):
        for directory in dirs:
            os.chmod(os.path.join(root, directory), 0o0755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o0755)
        nfiles_in_dirs.append(len(files))

    # if there is any new file downloaded save timestamp
    if any([x > 1 for x in nfiles_in_dirs]):
        print('Downloaded')
    else:
        print('No file downloaded')

    os.remove(dst_zipfile)
    shutil.rmtree(tmpdir)



def update_keyring_and_encrypt(tmp_lochness_dir: str):
    token, url, project_cid = get_token_url_project_cid()
    keyring_loc = Path(tmp_lochness_dir) / 'lochness.json'
    with open(keyring_loc, 'r') as f:
        keyring = json.load(f)

    keyring['daris.StudyA']['TOKEN'] = token
    keyring['daris.StudyA']['URL'] = url
    keyring['daris.StudyA']['PROJECT_CID'] = project_cid


    with open(keyring_loc, 'w') as f:
        json.dump(keyring, f)
    
    keyring_content = open(keyring_loc, 'rb')
    key = crypt.kdf('')
    crypt.encrypt(keyring_content, key,
            filename=Path(tmp_lochness_dir) / '.lochness.enc')


def initialize_metadata(Lochness, study_name):
    df = pd.DataFrame({'Active': [1],
        'Consent': '1988.-09-16',
        'Subject ID': 'subject01',
        'Daris': 'daris.StudyA:5Yp0E'})
    df_loc = Path(Lochness['phoenix_root']) / 'GENERAL' / \
            study_name / f"{study_name}_metadata.csv"

    df.to_csv(df_loc, index=False)


def get_token_url_project_cid():
    token_and_url_file = Path('token_and_url.txt')

    if token_and_url_file.is_file():
        df = pd.read_csv(token_and_url_file)
        token = df.iloc[0]['token']
        url = df.iloc[0]['url']
        project_cid = df.iloc[0]['project_id']
    else:
        token = input('Enter token: ')
        url = input('Enter URL: ')
        project_cid = input('Enter project CID: ')

    return token, url, project_cid


def test_sync_from_empty(args):
    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)
    update_keyring_and_encrypt(args.outdir)
    dry=False
    study_name = 'StudyA'
    Lochness = config.load(f'{args.outdir}/config.yml', '')
    initialize_metadata(Lochness, study_name)

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=[study_name]):
        sync(Lochness, subject, dry)
    shutil.rmtree(args.outdir)


