import lochness
import shutil
from lochness.box import sync, sync_module
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


box_test_dir = test_dir / 'lochness_test/box'
phoenix_root = box_test_dir / 'tmp_lochness/PHOENIX'
protected_root = phoenix_root/ 'PROTECTED'
general_root = phoenix_root/ 'GENERAL'


class KeyringAndEncrypt(KeyringAndEncrypt):
    def update_for_box(self, study):
        token = Tokens()
        client_id, client_secret, api_token = \
                token.read_token_or_get_input('box')

        self.keyring[f'box.{study}'] = {}
        self.keyring[f'box.{study}']['CLIENT_ID'] = client_id
        self.keyring[f'box.{study}']['CLIENT_SECRET'] = client_secret
        self.keyring[f'box.{study}']['API_TOKEN'] = api_token

        self.write_keyring_and_encrypt()

@pytest.fixture
def args_and_Lochness():
    args = Args('tmp_lochness')
    args.sources = ['box']
    create_lochness_template(args)
    keyring = KeyringAndEncrypt(args.outdir)
    information_to_add_to_metadata = {'box': {
        'subject_id': '1001',
        'source_id': 'O1234'}}

    for study in args.studies:
        keyring.update_for_box(study)

        # update box metadata
        initialize_metadata_test('tmp_lochness/PHOENIX', study,
                                 information_to_add_to_metadata)

    lochness_obj = config_load_test('tmp_lochness/config.yml', '')

    return args, lochness_obj


def test_box_sync_module_default(args_and_Lochness):
    args, Lochness = args_and_Lochness

    Lochness['BIDS'] = False
    # change protect to true for all actigraphy
    for study in args.studies:
        new_list = []
        for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            i['protect'] = False
            i['processed'] = False
            new_list.append(i)
        Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    for study in args.studies:
        subject_dir = general_root / study / '1001'
        print(subject_dir)
        assert (subject_dir / 'actigraphy').is_dir()
        assert (subject_dir / 'actigraphy/raw').is_dir()
        assert len(list((subject_dir / 'actigraphy/raw/').glob('*csv'))) > 1

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_default_BIDS(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change protect to true for all actigraphy
    for study in args.studies:
        new_list = []
        for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            i['protect'] = False
            i['processed'] = False
            new_list.append(i)
        Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    for study in args.studies:
        subject_dir = general_root / study / 'raw' / '1001'
        print(subject_dir)
        assert (subject_dir / 'actigraphy').is_dir()
        assert len(list((subject_dir / 'actigraphy').glob('*csv'))) > 1

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_protected(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change protect to true for all actigraphy
    for study in args.studies:
        new_list = []
        for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            i['protect'] = True
            i['processed'] = False
            new_list.append(i)
        Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    for study in args.studies:
        subject_dir = protected_root / study / 'raw' / '1001'
        assert (subject_dir / 'actigraphy').is_dir()
        assert len(list((subject_dir / 'actigraphy').glob('*csv'))) > 1

        subject_dir = general_root / study / '1001'
        assert (subject_dir / 'actigraphy').is_dir() == False
        assert len(list((subject_dir / 'actigraphy').glob('*csv'))) == 0

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_protect_processed(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change protect to true for all actigraphy
    for study in args.studies:
        new_list = []
        for i in Lochness['box'][study]['file_patterns']['actigraphy']:
            i['protect'] = True
            i['processed'] = True
            new_list.append(i)
        Lochness['box'][study]['file_patterns']['actigraphy'] = new_list

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    for study in args.studies:
        subject_dir = protected_root / study / 'processed' / '1001'
        assert (subject_dir / 'actigraphy').is_dir()
        assert len(list((subject_dir /
                        'actigraphy').glob('*csv'))) > 1

        subject_dir = general_root / study / 'processed' / '1001'
        assert not (subject_dir / 'actigraphy').is_dir()
        assert len(list((subject_dir /
                         'actigraphy/processed/').glob('*csv'))) == 0

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_missing_root(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change base for StudyA to missing path
    Lochness['box']['StudyA']['base'] = 'hahah'

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    study = 'StudyA'
    subject_dir = protected_root / study / 'raw' / '1001'
    assert (subject_dir / 'actigraphy').is_dir() == False

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_missing_subject(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change subject name
    keyring = KeyringAndEncrypt(args.outdir)
    information_to_add_to_metadata = {'box': {
        'subject_id': '1001',
        'source_id': 'O12341234'}}

    for study in args.studies:
        keyring.update_for_box(study)

        # update box metadata
        initialize_metadata_test('tmp_lochness/PHOENIX', study,
                                 information_to_add_to_metadata)

    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    show_tree_then_delete('tmp_lochness')


def test_box_sync_module_no_redownload(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # change subject name
    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    a_file_path = general_root / 'StudyA' / 'raw' / '1001' / 'actigraphy' / \
            'BLS-F6VVM-GENEActivQC-day22to51.csv'

    init_time = a_file_path.stat().st_mtime

    # change subject name
    for subject in lochness.read_phoenix_metadata(Lochness):
        sync(Lochness, subject, dry=False)

    post_time = a_file_path.stat().st_mtime
    assert init_time == post_time

    show_tree_then_delete('tmp_lochness')


def test_box_with_given_structure():
    site_subject = {
            'PronetLA': ['LA123456',
                         'LA132457',
                         'LA124358'],
            'PronetSL': ['SL124352',
                         'SL123453',
                         'SL124539'],
            'PronetWU': ['WU142358',
                         'WU124351',
                         'WU142531']
            }

    modalities = {
            'actigraphy': ['actigraphy'],
            'interviews': ['onsiteinterview', 'offsiteinterview'],
            'eeg': ['eeg']
            }

    # 'phone': ['accel', 'audioRecordings', 'gps', 'power', 'surveyAnswers', 'surveyTimings']


    root = Path('example_box_root')
    try:
        shutil.rmtree(root)
    except:
        pass

    for site, subjects in site_subject.items():

        site_dir = root / site
        for modality, subdirectories in modalities.items():
            modality_dir = site_dir / modality
            for subject in subjects:
                subject_dir = modality_dir / subject

                for file in subdirectories:
                    if modality == 'phone':
                        final_dir = modality_dir / file / subject
                        final_dir.mkdir(parents=True, exist_ok=True)

                        if file.endswith('interview') or file.endswith('cordings'):
                            suffix = 'mp4'
                        else:
                            suffix = 'csv'
                            
                        file_name = f"{subject}_{file}.{suffix}"

                        with open(final_dir / file_name, 'w') as f:
                            f.write('')
                    else:
                        final_dir = subject_dir
                        final_dir.mkdir(parents=True, exist_ok=True)

                        if file.endswith('interview') or file.endswith('cordings'):
                            suffix = 'mp4'
                        else:
                            suffix = 'csv'
                            
                        file_name = f"{subject}_{file}.{suffix}"

                        with open(final_dir / file_name, 'w') as f:
                            f.write('')

    # show_tree_then_delete('example_box_root')



def test_mediaflux_with_given_structure():
    site_subject = {
            'PrescientME': ['ME123456',
                            'ME132457',
                            'ME124358'],
            'PrescientAD': ['AD124352',
                            'AD123453',
                            'AD124539'],
            'PrescientPE': ['PE142358',
                            'PE124351',
                            'PE142531']
            }

    modalities = {
            'actigraphy': ['actigraphy'],
            'interviews': ['onsiteinterview', 'offsiteinterview'],
            'eeg': ['eeg']
            }

    # 'phone': ['accel', 'audioRecordings', 'gps', 'power', 'surveyAnswers', 'surveyTimings']


    root = Path('example_mediaflux_root')
    try:
        shutil.rmtree(root)
    except:
        pass

    for site, subjects in site_subject.items():

        site_dir = root / site
        for modality, subdirectories in modalities.items():
            modality_dir = site_dir / modality
            for subject in subjects:
                subject_dir = modality_dir / subject

                for file in subdirectories:
                    if modality == 'phone':
                        final_dir = modality_dir / file / subject
                        final_dir.mkdir(parents=True, exist_ok=True)

                        if file.endswith('interview') or file.endswith('cordings'):
                            suffix = 'mp4'
                        else:
                            suffix = 'csv'
                            
                        file_name = f"{subject}_{file}.{suffix}"

                        with open(final_dir / file_name, 'w') as f:
                            f.write('')
                    else:
                        final_dir = subject_dir
                        final_dir.mkdir(parents=True, exist_ok=True)

                        if file.endswith('interview') or file.endswith('cordings'):
                            suffix = 'mp4'
                        else:
                            suffix = 'csv'
                            
                        file_name = f"{subject}_{file}.{suffix}"

                        with open(final_dir / file_name, 'w') as f:
                            f.write('')
