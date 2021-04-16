from lochness.redcap.process_piis import read_pii_mapping_to_dict
from lochness.redcap.process_piis import load_raw_return_proc_json
from lochness.redcap.process_piis import process_pii_string
from lochness.redcap.process_piis import get_shuffle_dict_for_type

import pandas as pd
import tempfile
import json
import string


def test_read_pii_mapping_to_dict_empty():
    assert read_pii_mapping_to_dict('') == {}


def test_read_pii_mapping_to_dict_one_line():
    df = pd.DataFrame({
        'pii_label_string': ['address'],
        'process': 'remove'
        })

    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.csv') as tmpfilename:
        df.to_csv(tmpfilename.name)

    d = read_pii_mapping_to_dict(tmpfilename.name)
    assert d == {'address': 'remove'}


def test_read_pii_mapping_to_dict_two_line():
    df = pd.DataFrame({
        'pii_label_string': ['address', 'phone_number'],
        'process': ['remove', 'random_number']
        })

    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.csv') as tmpfilename:
        df.to_csv(tmpfilename.name)

    d = read_pii_mapping_to_dict(tmpfilename.name)
    assert d == {'address': 'remove',
                 'phone_number': 'random_number'}


def get_pii_mapping_table():
    df = pd.DataFrame({
        'pii_label_string': ['address', 'phone_number'],
        'process': ['remove', 'random_number']
        })

    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.csv') as tmpfilename:
        df.to_csv(tmpfilename.name)

    return tmpfilename.name


def get_json_file():
    d = [{'subject': 'test',
          'address': 'Boston, 02215',
          'phone_number': '877-000-0000',
          'ha_phone_number': '800-000-0000'}]

    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.json') as tmpfilename:
        with open(tmpfilename.name, 'w') as f:
            json.dump(d, f)

    return tmpfilename.name


def test_load_raw_return_proc_json():
    print()
    json_loc = get_json_file()
    pii_table_loc = get_pii_mapping_table()

    pii_str_proc_dict = read_pii_mapping_to_dict(pii_table_loc)
    processed_content = load_raw_return_proc_json(json_loc,
                                                  pii_str_proc_dict)

    assert type(processed_content) == bytes


def test_process_pii_string():
    print(process_pii_string('my name is kevin', 'random_string'))
    print(process_pii_string('1923956', 'random_number'))
    print(process_pii_string('816-198-963', 'random_number'))


def test_get_shuffle_dict_for_type():
    print(get_shuffle_dict_for_type(string.digits, '393jfi'))
    print(get_shuffle_dict_for_type(string.ascii_lowercase, '393jfiefy090'))
    print(get_shuffle_dict_for_type(string.ascii_uppercase, '393jfUUy090'))

