import lochness
from pathlib import Path
import pytest
import pandas as pd
import cryptease as crypt
import json
from lochness import config
from lochness import box
from lochness import mindlamp
import boxsdk

import sys, os, shutil

lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from lochness_create_template import create_lochness_template
from sync import SOURCES


class SyncArgs(object):
    def __init__(self, root_dir):
        self.source = ['xnat', 'box', 'redcap']
        self.studies = ['StudyA', 'StudyB']
        self.config = f'{root_dir}/config.yml'
        self.lochness_sync_receive = False
        self.lochness_sync_send = False
        self.archive_base = None
        self.hdd = None
        self.dry = False

        self.source = [SOURCES[x] for x in self.source]
    def __str__(self):
        return 'sync arg in {root_dir}'

    def update_source(self, sources):
        self.source = [SOURCES[x] for x in sources]


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
        self.all_token_file = test_dir / 'token_template_for_test.csv'

    def get_redcap_info(self):
        if self.token_and_url_file.is_file():
            df = pd.read_csv(self.token_and_url_file, index_col=0)
            API_TOKEN = df.loc['API_TOKEN', 'value']
            URL = df.loc['URL', 'value']
        else:
            API_TOKEN = 'API_TOKEN'
            URL = 'URL'

        return API_TOKEN, URL

    def read_token_or_get_input(self, module_name: str) -> list:
        items_to_return = []

        if self.all_token_file.is_file():
            df = pd.read_csv(self.all_token_file)
            for index, row in df[df['module'] == module_name].iterrows():
                items_to_return.append(row['value'])
        else:
            for index, row in df[df['module'] == module_name].iterrows():
                user_input_value = input(f'Enter {row["var"]}: ')
                items_to_return.append(user_input_value)

        return items_to_return


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
        token = Tokens(test_dir / 'lochness_test' / 'transfer')
        host, username, password, path_in_host, port = \
                token.read_token_or_get_input()

        self.keyring['lochness_sync']['HOST'] = host
        self.keyring['lochness_sync']['USERNAME'] = username
        self.keyring['lochness_sync']['PASSWORD'] = password
        self.keyring['lochness_sync']['PATH_IN_HOST'] = path_in_host
        self.keyring['lochness_sync']['PORT'] = port

        self.write_keyring_and_encrypt()

    def update_for_redcap(self, study):
        token = Tokens(test_dir / 'lochness_test' / 'redcap')
        api_token, url = token.read_token_or_get_input()

        self.keyring[f'redcap.{study}']['URL'] = url
        self.keyring[f'redcap.{study}']['API_TOKEN'] = {study: api_token}

        self.write_keyring_and_encrypt()

    def write_keyring_and_encrypt(self):
        with open(self.keyring_loc, 'w') as f:
            json.dump(self.keyring, f)
        
        keyring_content = open(self.keyring_loc, 'rb')
        key = crypt.kdf('')
        crypt.encrypt(
                keyring_content, key,
                filename=self.tmp_lochness_dir / '.lochness.enc')


def config_load_test(f: 'location', archive_base=None):
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
    return Args('tmp_lochness')


@pytest.fixture
def Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    _ = KeyringAndEncrypt(args.outdir)

    lochness = config_load_test('tmp_lochness/config.yml', '')
    return lochness


def show_tree_then_delete(tmp_dir):
    print()
    print('-'*75)
    print(f'Temporary directory structure : {tmp_dir}')
    print('-'*75)
    print(os.popen(f'tree {tmp_dir}').read())
    shutil.rmtree(tmp_dir)


def rmtree(tmp_dir):
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


def initialize_metadata_test(phoenix_root: 'phoenix root',
                             study_name: str,
                             sources_id_dict: dict,
                             v_study_name: str=None) -> None:
    '''Initialize metadata.csv by populating data

    Key arguments:
        phoenix_root: Root of the PHOENIX, str.
        study_name: Name of the study, str.
        sources_id_dict: Source information to test, dict of dict
                         eg. {'xnat': {'subject_id':1001,
                                       'source_id':'1001'}}
    '''
    df = pd.DataFrame()

    # for each record in pulled information, extract subject ID and source IDs
    for source, id_dict in sources_id_dict.items():
        subject_dict = {'Subject ID': id_dict['subject_id']}

        # Consent date
        subject_dict['Consent'] = '1988-09-16'

        if source.capitalize() == 'Xnat':
            if v_study_name != None:
                subject_dict['XNAT'] = \
                        f'xnat.{v_study_name}:{id_dict["source_id"]}'
            else:
                subject_dict['XNAT'] = \
                        f'xnat.{study_name}:{id_dict["source_id"]}'
        else:
            if v_study_name != None:
                subject_dict[source.capitalize()] = \
                        f'{source}.{v_study_name}:{id_dict["source_id"]}'
            else:
                subject_dict[source.capitalize()] = \
                        f'{source}.{study_name}:{id_dict["source_id"]}'

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

    general_path = Path(phoenix_root) / 'GENERAL'
    metadata_study = general_path / study_name / f"{study_name}_metadata.csv"

    df_final.to_csv(metadata_study, index=False)


def print_header(text):
    print()
    print()
    print('='*79)
    print('\t' + '\n\t'.join(text.split('\n')))
    print('='*79)


