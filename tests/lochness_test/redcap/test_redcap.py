import lochness
import pandas as pd
import json, os, time
from lochness import tree
from pathlib import Path

from lochness.redcap import sync, initialize_metadata
from lochness.redcap.data_trigger_capture import save_post_from_redcap
from lochness.redcap.data_trigger_capture import back_up_db

import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))
from test_lochness import Args, KeyringAndEncrypt
from test_lochness import show_tree_then_delete, rmtree, config_load_test
from lochness_create_template import create_lochness_template

import pytest
pd.set_option('max_columns', 50)


@pytest.fixture
def args_and_Lochness():
    args = Args('tmp_lochness')
    create_lochness_template(args)
    keyring = KeyringAndEncrypt(args.outdir)
    for study in args.studies:
        keyring.update_for_redcap(study)

    lochness_obj = config_load_test('tmp_lochness/config.yml', '')

    return args, lochness_obj


def test_initialize_metadata_function_adding_new_data_to_csv(
        args_and_Lochness):
    args, Lochness = args_and_Lochness

    # before initializing metadata
    for study in args.studies:
        phoenix_path = Path(Lochness['phoenix_root'])
        general_path = phoenix_path / 'GENERAL'
        metadata = general_path / study / f"{study}_metadata.csv"
        assert len(pd.read_csv(metadata)) == 1

        initialize_metadata(Lochness, study, 'record_id1', 'cons_date')

        assert len(pd.read_csv(metadata)) > 3

    rmtree('tmp_lochness')


def test_initialize_metadata_then_sync(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # before initializing metadata
    for study in args.studies:
        phoenix_path = Path(Lochness['phoenix_root'])
        general_path = phoenix_path / 'GENERAL'
        metadata = general_path / study / f"{study}_metadata.csv"
        initialize_metadata(Lochness, study, 'record_id1', 'cons_date')

    for subject in lochness.read_phoenix_metadata(Lochness,
                                                  studies=['StudyA']):
        sync(Lochness, subject, False)

    show_tree_then_delete('tmp_lochness')


@pytest.fixture
def LochnessMetadataInitialized(args_and_Lochness):
    args, Lochness = args_and_Lochness

    # before initializing metadata
    for study in args.studies:
        phoenix_path = Path(Lochness['phoenix_root'])
        general_path = phoenix_path / 'GENERAL'
        metadata = general_path / study / f"{study}_metadata.csv"

        initialize_metadata(Lochness, study, 'record_id1', 'cons_date')

    return Lochness


def test_initialize_metadata_update_when_initialized_again(
        LochnessMetadataInitialized):
    args = Args('tmp_lochness')
    for study in args.studies:
        phoenix_path = Path(LochnessMetadataInitialized['phoenix_root'])
        general_path = phoenix_path / 'GENERAL'
        metadata = general_path / study / f"{study}_metadata.csv"

        prev_st_mtime = metadata.stat().st_mtime

        initialize_metadata(LochnessMetadataInitialized, study,
                            'record_id1', 'cons_date')
        post_st_mtime = metadata.stat().st_mtime

        assert prev_st_mtime < post_st_mtime


@pytest.fixture
def lochness_subject_raw_json(LochnessMetadataInitialized):
    for subject in lochness.read_phoenix_metadata(LochnessMetadataInitialized,
                                                  studies=['StudyA']):
        if subject.id != 'subject_1':
            continue

        phoenix_path = Path(LochnessMetadataInitialized['phoenix_root'])
        subject_proc_p = phoenix_path / 'PROTECTED' / 'StudyA' / 'raw' / 'subject_1'
        raw_json = subject_proc_p / 'surveys' / f"{subject.id}.StudyA.json"

        return LochnessMetadataInitialized, subject, raw_json


def test_sync_init(lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    assert raw_json.is_file() == True
    rmtree('tmp_lochness')


def test_sync_twice(lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    # second sync without update in the db
    sync(Lochness, subject, False)
    rmtree('tmp_lochness')


def test_sync_no_mtime_update_when_no_pull(
        lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    init_mtime = raw_json.stat().st_mtime

    # second sync without update in the db
    sync(Lochness, subject, False)
    assert init_mtime == raw_json.stat().st_mtime
    rmtree('tmp_lochness')


def test_sync_det_update_no_file_leads_to_pull(
        lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    init_mtime = raw_json.stat().st_mtime

    os.remove(raw_json)
    text_body = "redcap_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2F&project_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2Fredcap_v10.0.30%2Findex.php%3Fpid%3D26709&project_id=26709&username=kc244&record=subject_1&instrument=inclusionexclusion_checklist&inclusionexclusion_checklist_complete=0"
    save_post_from_redcap(
            text_body,
            Lochness['redcap']['data_entry_trigger_csv'])

    # second sync without update in the db
    sync(Lochness, subject, False)
    assert raw_json.is_file()
    rmtree('tmp_lochness')


def test_sync_det_update_while_file_leads_to_mtime_update(
        lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    init_mtime = raw_json.stat().st_mtime

    text_body = "redcap_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2F&project_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2Fredcap_v10.0.30%2Findex.php%3Fpid%3D26709&project_id=26709&username=kc244&record=subject_1&instrument=inclusionexclusion_checklist&inclusionexclusion_checklist_complete=0"
    save_post_from_redcap(
            text_body,
            Lochness['redcap']['data_entry_trigger_csv'])

    with open(raw_json, 'r') as json_file:
        init_content_dict = json.load(json_file)

    # second sync without update in the db
    sync(Lochness, subject, False)

    with open(raw_json, 'r') as json_file:
        new_content_dict = json.load(json_file)

    assert init_content_dict == new_content_dict
    assert init_mtime < raw_json.stat().st_mtime
    rmtree('tmp_lochness')


def test_sync_det_update_while_diff_file_leads_to_data_overwrite(
        lochness_subject_raw_json):
    Lochness, subject, raw_json = lochness_subject_raw_json
    sync(Lochness, subject, False)
    # change the content of the existing json
    with open(raw_json, 'w') as json_file:
        json.dump({'test': 'test'}, json_file)

    text_body = "redcap_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2F&project_url=https%3A%2F%2Fredcap.partners.org%2Fredcap%2Fredcap_v10.0.30%2Findex.php%3Fpid%3D26709&project_id=26709&username=kc244&record=subject_1&instrument=inclusionexclusion_checklist&inclusionexclusion_checklist_complete=0"
    save_post_from_redcap(
            text_body,
            Lochness['redcap']['data_entry_trigger_csv'])

    # second sync without update in the db
    sync(Lochness, subject, False)

    with open(raw_json, 'r') as json_file:
        new_content_dict = json.load(json_file)
    assert {'test': 'test'} != new_content_dict
    rmtree('tmp_lochness')

