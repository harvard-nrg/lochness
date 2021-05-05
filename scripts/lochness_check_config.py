#!/usr/bin/env python

import argparse as ap
from lochness import config
from lochness import keyring
import os
import json


def check_config(config_loc: str):
    with open(config_loc, 'rb') as fp:
        config_loaded = config._read_config_file(fp)
    keyring.pretty_print_dict(config_loaded)


def check_keyring(keyring_dict):
    keyring.print_keyring(keyring_dict)


def check_lochness_configurations():
    '''Check lochness configurations

    To check formatting, field names in following items
        - config.yml
        - lochness.enc
        - lochness.json (before encryption)
    '''

    parser = ap.ArgumentParser(description='Lochness configuration checker')
    parser.add_argument('-c', '--config', help='Configuration file')
    parser.add_argument('-ke', '--keyring_encrypted',
                        help='Encrypted keyring file')
    parser.add_argument('-k', '--keyring',
                        help='None keyring file in json format')

    args = parser.parse_args()


    if args.config:
        check_config(args.config)

    if args.keyring_encrypted:
        keyring_dict = keyring.load_encrypted_keyring(args.keyring_encrypted)
        check_keyring(keyring_dict)

    if args.keyring:
        with open(args.keyring, 'r') as f:
            keyring_dict = json.load(f)
        check_keyring(keyring_dict)


if __name__ == '__main__':
    check_lochness_configurations()
