import lochness
from pathlib import Path
import pytest
import pandas as pd
import cryptease as crypt
import json
from lochness import config
from lochness import box
from lochness import mindlamp
from mock_args import LochnessArgs, mock_load
import boxsdk

import sys, os, shutil

lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from lochness_test.config.test_config import create_config
from lochness_create_template import create_lochness_template


class Args:
    '''Arg class to be used in the create_lochness_template function'''
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA', 'StudyB']
        self.sources = ['Redcap', 'RPMS']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.lochness_sync_send = True
        self.lochness_sync_receive = False
        self.lochness_sync_history_csv = 'lochness_sync_history.csv'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


class Tokens():
    '''class used to load sensitive information for lochness.tests'''
    def __init__(self):
        self.token_and_url_file = Path('token.txt')

    def get_lochness_sync_info(self):
        if self.token_and_url_file.is_file():
            df = pd.read_csv(self.token_and_url_file, index_col=0)
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


class KeyringAndEncrypt():
    def __init__(self, tmp_lochness_dir: str):
        # def update_keyring_and_encrypt(tmp_lochness_dir: str):
        self.tmp_lochness_dir = Path(tmp_lochness_dir)
        self.keyring_loc = tmp_lochness_dir / 'lochness.json'
        with open(self.keyring_loc, 'r') as f:
            self.keyring = json.load(f)

        self.write_keyring_and_encrypt()

    def update_for_rpms(self):
        self.keyring['rpms.StudyA']['RPMS_PATH'] = str(
                Path(self.tmp_lochness_dir).absolute().parent / 'RPMS_repo')

        self.write_keyring_and_encrypt()

    def update_for_lochness_sync(self):
        token = Tokens()
        host, username, password, path_in_host, port = \
                token.get_lochness_sync_info()

        self.keyring['lochness_sync']['HOST'] = host
        self.keyring['lochness_sync']['USERNAME'] = username
        self.keyring['lochness_sync']['PASSWORD'] = password
        self.keyring['lochness_sync']['PATH_IN_HOST'] = path_in_host
        self.keyring['lochness_sync']['PORT'] = port

        self.write_keyring_and_encrypt()

    def write_keyring_and_encrypt(self):
        with open(self.keyring_loc, 'w') as f:
            json.dump(self.keyring, f)
        
        keyring_content = open(self.keyring_loc, 'rb')
        key = crypt.kdf('')
        crypt.encrypt(
                keyring_content, key,
                filename=self.tmp_lochness_dir / '.lochness.enc')


def test_load(f: 'location', archive_base=None):
    '''load configuration file and keyring'''
    config.logger.debug('loading configuration')

    with open(os.path.expanduser(f), 'rb') as fp:
        Lochness = config._read_config_file(fp)

    if archive_base:
        Lochness['phoenix_root'] = archive_base
    if 'phoenix_root' not in Lochness:
        raise config.ConfigError('need either --archive-base or '
                          '\'phoenix_root\' in config file')
    Lochness['phoenix_root'] = os.path.expanduser(Lochness['phoenix_root'])
    Lochness['keyring_file'] = os.path.expanduser(Lochness['keyring_file'])

    # box file pattern strings from the config to string template
    # regardless of the selected study in the args
    if 'box' in Lochness:
        for _, study_dict in Lochness['box'].items():
            for _, modality_values in study_dict['file_patterns'].items():
                for modality_dict in modality_values:
                    modality_dict['pattern'] = \
                        config.string.Template(modality_dict['pattern'])

    with open(Lochness['keyring_file'], 'rb') as fp:
        config.logger.info(f'reading keyring file {Lochness["keyring_file"]}')
        passphrase = ''
        key = crypt.key_from_file(fp, passphrase)
        content = b''
        for chunk in crypt.decrypt(fp, key):
            content += chunk
        try:
            Lochness['keyring'] = config.yaml.load(
                    content,
                    Loader=config.yaml.FullLoader)
        except config.yaml.reader.ReaderError:
            raise config.KeyringError('could not decrypt keyring {0} (wrong passphrase?)'.format(Lochness['keyring_file']))

    return Lochness

@pytest.fixture
def args():
    return Args('test_lochness')


@pytest.fixture
def Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    _ = KeyringAndEncrypt(args.outdir)

    lochness = test_load('tmp_lochness/config.yml', '')
    return lochness


def show_tree_then_delete(tmp_dir):
    print()
    print('-'*75)
    print(f'Temporary directory structure : {tmp_dir}')
    print('-'*75)
    print(os.popen(f'tree {tmp_dir}').read())
    shutil.rmtree(tmp_dir)


def test_do():
    args = LochnessArgs()
    Lochness = mock_load(args.config, args.archive_base)


def test_read_phoenix_data():
    args = LochnessArgs()
    args.source = ['xnat', 'box']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject)


def test_read_phoenix_metadata():
    args = LochnessArgs()
    args.source = ['xnat', 'box', 'redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    config_string, fp = create_config()

    Lochness = mock_load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        # Subject(active=1,
                # study='StudyA', id='EXAMPLE', consent='1979-01-01',
                # beiwe=defaultdict(<class 'list'>,
                    # {'beiwe': [('5432', 'abcde')]}),
                # icognition={},
                # saliva={},
                # xnat=defaultdict(<class 'list'>,
                    # {'xnat.hcpep': [('HCPEP-BWH', '1001')]}),
                # redcap=defaultd ict(<class 'list'>,
                    # {'redcap.hcpep': ['1001_1']}),
                # dropbox={},
                # box=defaultdict(<class 'list'>,
                    # {'box.mclean': ['O1234']}),
                # general_folder='./PHOENIX/GENERAL/StudyA/EXAMPLE',
                # protected_folder='./PHOENIX/PROTECTED/StudyA/EXAMPLE')

        assert subject.study == 'StudyA'
        assert subject.general_folder == './PHOENIX/GENERAL/StudyA/EXAMPLE'
        assert list(subject.xnat.keys())[0] == 'xnat.StudyA'
        assert list(subject.xnat.values())[0][0][0] == 'HCPEP-BWH'


def test_box_module():
    args = LochnessArgs()
    args.source = ['xnat', 'box', 'redcap']
    args.studies = ['StudyA']
    args.dry = [False]
    config_string, fp = create_config()

    Lochness = mock_load(args.config, args.archive_base)
    Lochness['keyring']['lochness']['SECRETS'] = {}
    Lochness['keyring']['lochness']['SECRETS']['StudyA'] = 'ha'
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject.study)
        for module in subject.box:
            print(module)
            print(module)
            try:
                box.sync_module(Lochness, subject, module, dry=True)
            except boxsdk.BoxAPIException as e:
                print('ha')


def test_mindlamp_module():
    args = LochnessArgs()
    args.source = ['xnat', 'mindlamp']
    args.studies = ['StudyA']
    args.dry = [False]
    config_string, fp = create_config()

    Lochness = mock_load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject.study)
        for module in subject.mindlamp:
            assert module == 'mindlamp.StudyA'
            mindlamp.sync(Lochness, subject, dry=True)
