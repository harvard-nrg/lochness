import lochness
import os
import shutil
from lochness.transfer import get_updated_files, compress_list_of_files
from lochness.transfer import compress_new_files, lochness_to_lochness_transfer
from lochness.transfer import decompress_transferred_file_and_copy
from lochness.transfer import lochness_to_lochness_transfer_receive
from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))
from lochness_create_template import create_lochness_template

import lochness.config as config
import pytest
from time import time
from datetime import timedelta
from datetime import datetime
import json
import pandas as pd
import cryptease as crypt
import tempfile as tf
import tarfile


class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA', 'StudyB']
        self.sources = ['Redcap', 'RPMS']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.lochness_to_lochness = True
        self.lochness_sync_receive = False
        self.lochness_sync_history_csv = 'lochness_sync_history.csv'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


def get_tokens():
    token_and_url_file = Path('token.txt')

    if token_and_url_file.is_file():
        df = pd.read_csv(token_and_url_file, index_col=0)
        host = df.loc['host', 'value']
        username = df.loc['username', 'value']
        password = df.loc['password', 'value']
        path_in_host = df.loc['path_in_host', 'value']
        port = df.loc['port', 'value']
    else:
        host = 'HOST'
        username = 'USERNAME'
        password = 'PASSWORD'
        path_in_host = 'PATH_IN_HOST'
        port = 'PORT'

    return host, username, password, path_in_host, port


def update_keyring_and_encrypt(tmp_lochness_dir: str):
    keyring_loc = Path(tmp_lochness_dir) / 'lochness.json'
    with open(keyring_loc, 'r') as f:
        keyring = json.load(f)

    keyring['rpms.StudyA']['RPMS_PATH'] = str(
            Path(tmp_lochness_dir).absolute().parent / 'RPMS_repo')

    host, username, password, path_in_host, port = get_tokens()
    keyring['lochness_to_lochness']['HOST'] = host
    keyring['lochness_to_lochness']['USERNAME'] = username
    keyring['lochness_to_lochness']['PASSWORD'] = password
    keyring['lochness_to_lochness']['PATH_IN_HOST'] = path_in_host
    keyring['lochness_to_lochness']['PORT'] = port

    with open(keyring_loc, 'w') as f:
        json.dump(keyring, f)
    
    keyring_content = open(keyring_loc, 'rb')
    key = crypt.kdf('')
    crypt.encrypt(keyring_content, key,
            filename=Path(tmp_lochness_dir) / '.lochness.enc')


@pytest.fixture
def Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    update_keyring_and_encrypt(args.outdir)

    lochness = config.load('tmp_lochness/config.yml', '')
    return lochness


def test_using_base_function(Lochness):
    print(Lochness)


def test_get_updated_files(Lochness):
    print(Lochness)

    timestamp_a_day_ago = datetime.timestamp(
            datetime.fromtimestamp(time()) - timedelta(days=1))

    posttime = time()

    file_lists = get_updated_files(Lochness['phoenix_root'],
                                   timestamp_a_day_ago,
                                   posttime)

    assert Path('PHOENIX/GENERAL/StudyA/StudyA_metadata.csv') in file_lists
    assert Path('PHOENIX/GENERAL/StudyB/StudyB_metadata.csv') in file_lists

    shutil.rmtree('tmp_lochness')

    print(file_lists)
    print(file_lists)


def show_tree_then_delete(tmp_dir):
    print()
    print('-'*75)
    print(f'Temporary directory structure : {tmp_dir}')
    print('-'*75)
    print(os.popen(f'tree {tmp_dir}').read())
    shutil.rmtree(tmp_dir)




def test_compress_list_of_files(Lochness):
    print()

    timestamp_a_day_ago = datetime.timestamp(
            datetime.fromtimestamp(time()) - timedelta(days=1))

    posttime = time()

    phoenix_root = Lochness['phoenix_root']
    file_lists = get_updated_files(phoenix_root,
                                   timestamp_a_day_ago,
                                   posttime)
    compress_list_of_files(phoenix_root, file_lists, 'prac.tar')

    shutil.rmtree('tmp_lochness')

    # shutil.rmtree('tmp_lochness')
    assert Path('prac.tar').is_file()

    os.popen('tar -xf prac.tar').read()
    show_tree_then_delete('PHOENIX')
    os.remove('prac.tar')


def test_compress_new_files(Lochness):
    print()

    phoenix_root = Lochness['phoenix_root']

    compress_new_files('nodb', phoenix_root, 'prac.tar')
    shutil.rmtree('tmp_lochness')

    # shutil.rmtree('tmp_lochness')
    assert Path('prac.tar').is_file()
    assert Path('nodb').is_file()

    with open('nodb', 'r') as f:
        print(f.read())

    os.popen('tar -xf prac.tar').read()
    os.remove('nodb')
    os.remove('prac.tar')

    show_tree_then_delete('PHOENIX')



def test_lochness_to_lochness_transfer(Lochness):
    print()
    protected_dir = Path(Lochness['phoenix_root']) / 'PROTECTED'

    for i in range(10):
        with tf.NamedTemporaryFile(suffix='tmp.text',
                                   delete=False,
                                   dir=protected_dir) as tmpfilename:

            with open(tmpfilename.name, 'w') as f:
                f.write('ha')


    lochness_to_lochness_transfer(Lochness)
    print(os.popen('tree').read())
    shutil.rmtree('tmp_lochness')

    compressed_file = list(Path('.').glob('tmp*tar'))[0]
    os.popen(f'tar -xf {compressed_file}').read()
    os.remove(str(compressed_file))

    show_tree_then_delete('PHOENIX')


def test_lochness_to_lochness_transfer_all(Lochness):
    print()

    protected_dir = Path(Lochness['phoenix_root']) / 'PROTECTED'

    for i in range(10):
        with tf.NamedTemporaryFile(suffix='tmp.text',
                                   delete=False,
                                   dir=protected_dir) as tmpfilename:

            with open(tmpfilename.name, 'w') as f:
                f.write('ha')


    #pull all
    # lochness_to_lochness_transfer(Lochness, general_only=False)

    with tf.NamedTemporaryFile(suffix='tmp.tar',
                               delete=False,
                               dir='.') as tmpfilename:
        # compress
        compress_new_files(Lochness['lochness_sync_history_csv'],
                           Lochness['phoenix_root'],
                           tmpfilename.name,
                           False)

    show_tree_then_delete('tmp_lochness')

    compressed_file = list(Path('.').glob('tmp*tar'))[0]
    os.popen(f'tar -xf {compressed_file}').read()
    # os.remove(str(compressed_file))

    show_tree_then_delete('PHOENIX')


def test_decompress_transferred_file_and_copy():
    target_phoenix_root = Path('DPACC_PHOENIX')

    tar_file_trasferred = list(Path('.').glob('tmp*tar'))[0]
    decompress_transferred_file_and_copy(target_phoenix_root,
                                         tar_file_trasferred)

    show_tree_then_delete(target_phoenix_root)


class DpaccArgs:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = []
        self.sources = []
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.lochness_to_lochness = False
        self.lochness_sync_receive = True
        self.lochness_sync_history_csv = 'lochness_sync_history.csv'
        self.det_csv = ''
        self.pii_csv = ''


def update_keyring_and_encrypt_DPACC(tmp_lochness_dir: str):
    keyring_loc = Path(tmp_lochness_dir) / 'lochness.json'
    with open(keyring_loc, 'r') as f:
        keyring = json.load(f)

    keyring['lochness_to_lochness_receive']['PATH_IN_HOST'] = '.'

    with open(keyring_loc, 'w') as f:
        json.dump(keyring, f)
    
    keyring_content = open(keyring_loc, 'rb')
    key = crypt.kdf('')
    crypt.encrypt(keyring_content, key,
                  filename=Path(tmp_lochness_dir) / '.lochness.enc')


def test_lochness_to_lochness_transfer_receive(Lochness):
    print()

    protected_dir = Path(Lochness['phoenix_root']) / 'PROTECTED'

    for i in range(10):
        with tf.NamedTemporaryFile(suffix='tmp.text',
                                   delete=False,
                                   dir=protected_dir) as tmpfilename:

            with open(tmpfilename.name, 'w') as f:
                f.write('ha')


    #pull all
    # lochness_to_lochness_transfer(Lochness, general_only=False)

    with tf.NamedTemporaryFile(suffix='tmp.tar',
                               delete=False,
                               dir='.') as tmpfilename:
        # compress
        compress_new_files(Lochness['lochness_sync_history_csv'],
                           Lochness['phoenix_root'],
                           tmpfilename.name,
                           False)

    show_tree_then_delete('tmp_lochness')

    compressed_file = list(Path('.').glob('tmp*tar'))[0]
    os.popen(f'tar -xf {compressed_file}').read()
    # os.remove(str(compressed_file))

    show_tree_then_delete('PHOENIX')


    out_dir = 'DPACC'
    args = DpaccArgs(out_dir)
    create_lochness_template(args)
    update_keyring_and_encrypt_DPACC(args.outdir)

    lochness = config.load(f'{out_dir}/config.yml', '')
    lochness_to_lochness_transfer_receive(lochness)


    show_tree_then_delete('DPACC')
    os.remove(tmpfilename.name)
