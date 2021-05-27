import lochness
from lochness.xnat import sync
from lochness import config
from pathlib import Path

import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))
from test_lochness import Args, KeyringAndEncrypt, Tokens
from test_lochness import show_tree_then_delete, rmtree, config_load_test
from test_lochness import initialize_metadata_test
from lochness_create_template import create_lochness_template

import pytest


xnat_test_dir = test_dir / 'lochness_test/xnat'
phoenix_root = xnat_test_dir / 'tmp_lochness/PHOENIX'
protected_root = phoenix_root/ 'PROTECTED'
general_root = phoenix_root/ 'GENERAL'


class KeyringAndEncrypt(KeyringAndEncrypt):
    def update_for_xnat(self, study):
        token = Tokens(test_dir / 'lochness_test' / 'xnat')

        url, username, password = token.read_token_or_get_input()

        self.keyring[f'xnat.hcpep'] = {}
        self.keyring[f'xnat.hcpep']['URL'] = url
        self.keyring[f'xnat.hcpep']['USERNAME'] = username
        self.keyring[f'xnat.hcpep']['PASSWORD'] = password

        self.write_keyring_and_encrypt()


@pytest.fixture
def args_and_Lochness():
    args = Args('tmp_lochness')
    args.sources = ['xnat']
    create_lochness_template(args)
    keyring = KeyringAndEncrypt(args.outdir)
    information_to_add_to_metadata = {'xnat': {
        'subject_id': '1001',
        'source_id': '2004'}}

    for study in args.studies:
        keyring.update_for_xnat(study)

        # update box metadata
        initialize_metadata_test('tmp_lochness/PHOENIX', study,
                                 information_to_add_to_metadata,
                                 f'hcpep:HCPEP-BWH')

    lochness_obj = config_load_test('tmp_lochness/config.yml', '')

    return args, lochness_obj


def test_xnat_sync_module_dry(args_and_Lochness):
    args, Lochness = args_and_Lochness

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=True)


def test_xnat_sync_module_default(args_and_Lochness):
    args, Lochness = args_and_Lochness

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)



# def test_box_sync_module_default(args_and_Lochness):
    # args, Lochness = args_and_Lochness
    # # change protect to true for all actigraphy
    # for study in args.studies:
        # new_list = []
        # for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            # i['protect'] = False
            # i['processed'] = False
            # new_list.append(i)
        # Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # for study in args.studies:
        # subject_dir = general_root / study / '1001'
        # print(subject_dir)
        # assert (subject_dir / 'actigraphy').is_dir()
        # assert (subject_dir / 'actigraphy/raw').is_dir()
        # assert len(list((subject_dir / 'actigraphy/raw/').glob('*csv'))) > 1

    # show_tree_then_delete('tmp_lochness')


# def test_box_sync_module_protected(args_and_Lochness):
    # args, Lochness = args_and_Lochness

    # # change protect to true for all actigraphy
    # for study in args.studies:
        # new_list = []
        # for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            # i['protect'] = True
            # i['processed'] = False
            # new_list.append(i)
        # Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # for study in args.studies:
        # subject_dir = protected_root / study / '1001'
        # assert (subject_dir / 'actigraphy').is_dir()
        # assert (subject_dir / 'actigraphy/raw').is_dir()
        # assert len(list((subject_dir / 'actigraphy/raw/').glob('*csv'))) > 1

        # subject_dir = general_root / study / '1001'
        # assert (subject_dir / 'actigraphy').is_dir() == False
        # assert (subject_dir / 'actigraphy/raw').is_dir() == False
        # assert len(list((subject_dir / 'actigraphy/raw/').glob('*csv'))) == 0

    # show_tree_then_delete('tmp_lochness')


# def test_box_sync_module_protect_processed(args_and_Lochness):
    # args, Lochness = args_and_Lochness

    # # change protect to true for all actigraphy
    # for study in args.studies:
        # new_list = []
        # for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            # i['protect'] = True
            # i['processed'] = True
            # new_list.append(i)
        # Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # for study in args.studies:
        # subject_dir = protected_root / study / '1001'
        # assert (subject_dir / 'actigraphy').is_dir()
        # assert (subject_dir / 'actigraphy/processed').is_dir()
        # assert len(list((subject_dir /
                        # 'actigraphy/processed/').glob('*csv'))) > 1

        # subject_dir = general_root / study / '1001'
        # assert not (subject_dir / 'actigraphy').is_dir()
        # assert not (subject_dir / 'actigraphy/processed').is_dir()
        # assert len(list((subject_dir /
                         # 'actigraphy/processed/').glob('*csv'))) == 0

    # show_tree_then_delete('tmp_lochness')


# def test_box_sync_module_missing_root(args_and_Lochness):
    # args, Lochness = args_and_Lochness

    # # change base for StudyA to missing path
    # Lochness['box']['StudyA']['base'] = 'hahah'

    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # study = 'StudyA'
    # subject_dir = protected_root / study / '1001'
    # assert (subject_dir / 'actigraphy').is_dir() == False
    # assert (subject_dir / 'actigraphy/raw').is_dir() == False

    # show_tree_then_delete('tmp_lochness')


# def test_box_sync_module_missing_subject(args_and_Lochness):
    # args, Lochness = args_and_Lochness

    # # change subject name
    # keyring = KeyringAndEncrypt(args.outdir)
    # information_to_add_to_metadata = {'box': {
        # 'subject_id': '1001',
        # 'source_id': 'O12341234'}}

    # for study in args.studies:
        # keyring.update_for_box(study)

        # # update box metadata
        # initialize_metadata_test('tmp_lochness/PHOENIX', study,
                                 # information_to_add_to_metadata)

    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # show_tree_then_delete('tmp_lochness')


# def test_box_sync_module_no_redownload(args_and_Lochness):
    # args, Lochness = args_and_Lochness

    # # change subject name
    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # a_file_path = general_root / 'StudyA' / '1001' / 'actigraphy' / \
            # 'raw' / 'BLS-F6VVM-GENEActivQC-day22to51.csv'

    # init_time = a_file_path.stat().st_mtime

    # # change subject name
    # for subject in lochness.read_phoenix_metadata(Lochness):
        # sync(Lochness, subject, dry=False)

    # post_time = a_file_path.stat().st_mtime
    # assert init_time == post_time

    # show_tree_then_delete('tmp_lochness')
