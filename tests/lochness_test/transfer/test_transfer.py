import lochness
import os
import shutil
from lochness.transfer import get_updated_files, compress_list_of_files
from lochness.transfer import compress_new_files, lochness_to_lochness_transfer
from lochness.transfer import decompress_transferred_file_and_copy
from lochness.transfer import lochness_to_lochness_transfer_receive
from pathlib import Path

import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from test_lochness import Args, Tokens, KeyringAndEncrypt, args, SyncArgs
from test_lochness import show_tree_then_delete, config_load_test

from lochness_create_template import create_lochness_template


import pytest
from time import time
from datetime import timedelta
from datetime import datetime
import json
import pandas as pd
import cryptease as crypt
import tempfile as tf
import tarfile
import paramiko

from sync import do


class KeyringAndEncryptLochnessTransfer(KeyringAndEncrypt):
    def __init__(self, tmp_dir):
        super().__init__(tmp_dir)
        token = Tokens(test_dir / 'lochness_test' / 'transfer')
        host, username, password, path_in_host, port = \
                token.read_token_or_get_input()

        self.keyring['lochness_sync']['HOST'] = host
        self.keyring['lochness_sync']['USERNAME'] = username
        self.keyring['lochness_sync']['PASSWORD'] = password
        self.keyring['lochness_sync']['PATH_IN_HOST'] = path_in_host
        self.keyring['lochness_sync']['PORT'] = port

        self.write_keyring_and_encrypt()


@pytest.fixture
def Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    KeyringAndEncryptLochnessTransfer(args.outdir)

    lochness = config_load_test('tmp_lochness/config.yml', '')
    return lochness



def test_get_updated_files(Lochness):

    timestamp_a_day_ago = datetime.timestamp(
            datetime.fromtimestamp(time()) - timedelta(days=1))

    posttime = time()

    file_lists = get_updated_files(Lochness['phoenix_root'],
                                   timestamp_a_day_ago,
                                   posttime)

    assert Path('PHOENIX/GENERAL/StudyA/StudyA_metadata.csv') in file_lists
    assert Path('PHOENIX/GENERAL/StudyB/StudyB_metadata.csv') in file_lists

    show_tree_then_delete('tmp_lochness')


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

    show_tree_then_delete('tmp_lochness')

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
    os.remove(str(compressed_file))

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
        self.lochness_sync_send = False
        self.lochness_sync_receive = True
        self.lochness_sync_history_csv = 'lochness_sync_history.csv'
        self.det_csv = ''
        self.pii_csv = ''



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
    os.remove(str(compressed_file))

    show_tree_then_delete('PHOENIX')


    out_dir = 'DPACC'
    args = DpaccArgs(out_dir)
    create_lochness_template(args)
    update_keyring_and_encrypt_DPACC(args.outdir)

    lochness = config_load_test(f'{out_dir}/config.yml', '')
    lochness_to_lochness_transfer_receive(lochness)


    show_tree_then_delete('DPACC')
    os.remove(tmpfilename.name)


def update_keyring_and_encrypt_DPACC(tmp_lochness_dir: str):
    keyring_loc = Path(tmp_lochness_dir) / 'lochness.json'
    with open(keyring_loc, 'r') as f:
        keyring = json.load(f)

    keyring['lochness_sync']['PATH_IN_HOST'] = '.'

    with open(keyring_loc, 'w') as f:
        json.dump(keyring, f)
    
    keyring_content = open(keyring_loc, 'rb')
    key = crypt.kdf('')
    crypt.encrypt(keyring_content, key,
                  filename=Path(tmp_lochness_dir) / '.lochness.enc')


def test_lochness_to_lochness_transfer(Lochness):
    print()
    protected_dir = Path(Lochness['phoenix_root']) / 'PROTECTED'

    for i in range(10):
        with tf.NamedTemporaryFile(suffix='tmp.text',
                                   delete=False,
                                   dir=protected_dir) as tmpfilename:

            with open(tmpfilename.name, 'w') as f:
                f.write('ha')


    lochness_to_lochness_transfer(Lochness, False)
    print(os.popen('tree').read())
    shutil.rmtree('tmp_lochness')

    compressed_file = list(Path('.').glob('tmp*tar'))[0]
    os.popen(f'tar -xf {compressed_file}').read()
    os.remove(str(compressed_file))

    show_tree_then_delete('PHOENIX')



def test_sftp():
    tokens = Tokens(test_dir / 'lochness_test' / 'transfer')
    host, username, password, path_in_host, port = \
            tokens.read_token_or_get_input()
    file_to_send = 'hoho.txt'
    with open(file_to_send, 'w') as f:
        f.write('hahahah')

    transport = paramiko.Transport((host, int(port)))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    sftp.put(file_to_send, str(Path(path_in_host) / Path(file_to_send).name))
    sftp.close()
    transport.close()

    os.remove('hoho.txt')


def test_using_sync_do_send(Lochness):
    syncArg = SyncArgs('tmp_lochness')
    syncArg.lochness_sync_send = True
    do(syncArg)
    show_tree_then_delete('tmp_lochness')
