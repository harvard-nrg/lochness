import lochness
import sys
from pathlib import Path
import lochness.config as config
import lochness.tree as tree
import time
import pandas as pd

lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from lochness_create_template import create_lochness_template
from test_lochness import Args, Tokens, KeyringAndEncrypt, args, Lochness
from test_lochness import show_tree_then_delete
from lochness.rpms import initialize_metadata, sync, get_rpms_database


def create_fake_rpms_repo():
    '''Create fake RPMS repo per variable'''
    # make REPO directory
    root = Path('RPMS_repo')
    root.mkdir(exist_ok=True)

    number_of_measures = 10
    number_of_subjects = 5
    for measure_num in range(0, number_of_measures):
        # create a data
        measure_file = root / f'measure_{measure_num}.csv'

        df = pd.DataFrame()

        for subject_num in range(0, number_of_subjects):
            df_tmp = pd.DataFrame({
                'record_id1': [f'subject_{subject_num}'],
                'Consent': '1988-09-16',
                'var1': f'{measure_num}_var1_subject_{subject_num}',
                'address': f'{measure_num}_var2_subject_{subject_num}',
                'var3': f'{measure_num}_var3_subject_{subject_num}',
                'xnat_id': f'StudyA:bwh:var3_subject_{subject_num}',
                'box_id': f'box.StudyA:var3_subject_{subject_num}',
                'last_modified': time.time()})
            if measure_num // 2 >= 1:
                df_tmp = df_tmp.drop('box_id', axis=1)
            else:
                df_tmp = df_tmp.drop('xnat_id', axis=1)

            df = pd.concat([df, df_tmp])

        df.to_csv(measure_file, index=False)


def test_initializing_based_on_rpms(Lochness):
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
    initialize_metadata(Lochness, 'StudyA', 'record_id1', 'Consent')
    df = pd.read_csv('tmp_lochness/PHOENIX/GENERAL/StudyA/StudyA_metadata.csv')
    show_tree_then_delete('tmp_lochness')
    print(df)
    assert len(df) == 5


def test_create_lochness_template(Lochness):
    create_fake_rpms_repo()
    # create_lochness_template(args)
    study_name = 'StudyA'
    initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        # print(subject)
        for module in subject.rpms:
            print(module)
            print(module)
            print(module)
            # break
        # break

    show_tree_then_delete('tmp_lochness')


def test_sync(Lochness):
    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        sync(Lochness, subject, False)


class KeyringAndEncryptRPMS(KeyringAndEncrypt):
    def __init__(self, tmp_lochness_dir):
        super().__init__(tmp_lochness_dir)
        self.keyring['rpms.StudyA']['RPMS_PATH'] = str(
                Path(self.tmp_lochness_dir).absolute().parent / 'RPMS_repo')

        self.write_keyring_and_encrypt()


def test_sync_from_empty(args):
    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)
    KeyringAndEncryptRPMS(args.outdir)
    create_fake_rpms_repo()

    dry=False
    study_name = 'StudyA'
    Lochness = config.load(f'{args.outdir}/config.yml', '')
    initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        sync(Lochness, subject, dry)

    # print the structure
    show_tree_then_delete('tmp_lochness')


# rpms_root_path: str
def test_get_rpms_database():
    rpms_root_path = 'RPMS_repo'
    all_df_dict = get_rpms_database(rpms_root_path)

    assert list(all_df_dict.keys())[0]=='measure_9'
    assert list(all_df_dict.keys())[1]=='measure_8'

    assert type(list(all_df_dict.values())[0]) == pd.core.frame.DataFrame
    print(list(all_df_dict.values())[0])
    # print(all_df_dict))
