import pandas as pd
from pathlib import Path
import json
import random
import string
from datetime import date
from typing import List
import re


def read_pii_mapping_to_dict(pii_table_loc: str) -> pd.DataFrame:
    '''Read PII process table and return as dict

    Any field name containing the pii_label_string will be processed
    accordingly.

    Key arguments:
        pii_table_loc: path of the PII field string and process method csv

    Table example:
        pii_label_string | process
        -----------------|---------------
        address          | remove
        date             | change_date
        phone_number     | random_number
        patient_name     | random_string
    '''

    if Path(pii_table_loc).is_file():
        df = pd.read_csv(pii_table_loc)
        pii_string_process_dict = df.set_index('pii_label_string').to_dcit()

    else:
        pii_string_process_dict = {}

    return pii_string_process_dict


def load_raw_return_proc_json(json_loc: str,
                              pii_str_proc_dict: dict) -> List[dict]:
    # load json in PROTECTED/survey/raw
    with open(json_loc, 'r') as f:
        raw_json = json.load(f)  # list of dicts

    processed_json = []
    for instrument in raw_json:
        processed_instrument = {}
        for field_name, field_value in instrument.items():
            for pii_label_string, process in pii_str_proc_dict.items():
                if re.search(pii_label_string, field_name):
                    new_value = process_pii_string(field_name, process)
                    processed_instrument[field_name] = new_value
                    break
                else:
                    processed_instrument[field_name] = field_value

    processed_content = json.dumps(processed_json).encode()

    return processed_content


def process_pii_string(pii_string: str, process: str) -> str:
    '''Process PII string

    Key Arguments:
        - value_of_field: Raw value of the field, str.
        - process: How to process the raw value, str.
            - 'remove': completely remove the field from the json file.
            - 'change_date': change to days from certain time point.
            - 'random_number': replaced to random numbers in the same length.
            - 'random_string': replaced to random strings in the same length.

    Examples:
        process_pii_string('address': 'remove')
        process_pii_string('patient_name': 'random_string')
    '''

    string_len = len(pii_string)

    if process == 'remove':
        return ''

    elif process == 'change_date':
        base_date = date(1900, 1, 1)

        # eg) 2016-10-03
        y = int(pii_string.split('-')[0])
        m = int(pii_string.split('-')[1])
        d = int(pii_string.split('-')[2])

        date = date(y, m, d)
        delta = date - base_date

        return str(delta.days)

    elif process == 'random_number':
        digits = string.digits
        new_string = ''.join(
                random.choice(digits) for i in range(string_len))
        return new_string

    elif process == 'random_string':
        letters = string.ascii_lowercase
        new_string = ''.join(
                random.choice(letters) for i in range(string_len))
        return new_string

    else:
        return pii_string
