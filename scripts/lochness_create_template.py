#!/usr/bin/env python
'''
Create template lochness directory
'''
import lochness
from lochness.keyring import pretty_print_dict
from pathlib import Path
import argparse as ap
import sys
import re
from typing import List
import pandas as pd
import json
import importlib
from phoenix_generator import main as pg


lochness_root = Path(lochness.__file__).parent.parent
lochness_test_dir = lochness_root / 'test'


class ArgsForPheonix(object):
    def __init__(self, study, dir):
        self.study = study
        self.dir = dir
        self.verbose = False


def create_lochness_template(args):
    '''Create template for lochness'''
    # make sources small
    args.sources = [x.lower() for x in args.sources]
    args.outdir = Path(args.outdir).absolute()

    # make lochness root directory
    Path(args.outdir).mkdir(exist_ok=True)

    # PHOENIX root
    phoenix_root = Path(args.outdir) / 'PHOENIX'

    # create PHOENIX directory
    for study in args.studies:
        argsForPheonix = ArgsForPheonix(study, phoenix_root)
        pg(argsForPheonix)
        metadata = phoenix_root / 'GENERAL' / study / f'{study}_metadata.csv'

        # create example metadata
        create_example_meta_file_advanced(metadata, study, args.sources)

    # create det_csv
    if not Path(args.det_csv).is_file():
        args.det_csv = args.outdir / 'data_entry_trigger_database.csv'


    # create pii table
    if not Path(args.pii_csv).is_file():
        args.pii_csv = args.outdir / 'pii_convert.csv'
        df = pd.DataFrame({
            'pii_label_string': [
                'address', 'phone_number', 'date',
                'patient_name', 'subject_name'],
            'process': [
                'remove', 'random_number', 'change_date',
                'random_string', 'replace_with_subject_id']
            })
        df.to_csv(args.pii_csv)

    # create config
    config_loc = args.outdir / 'config.yml'
    create_config_template(config_loc, args)

    # create keyring
    keyring_loc = args.outdir / 'lochness.json'
    encrypt_keyring_loc = args.outdir / '.lochness.enc'
    create_keyring_template(keyring_loc, args)


    # write commands for the user to run after editing config and keyring
    write_commands_needed(args.outdir, config_loc,
                          keyring_loc, encrypt_keyring_loc, args.sources)


def write_commands_needed(outdir: Path,
                          config_loc: Path,
                          keyring_loc: Path,
                          encrypt_keyring_loc: Path,
                          sources) -> None:
    '''Write commands'''
    # encrypt_command.sh
    with open(outdir / '1_encrypt_command.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# run this command to encrypt the edited keyring '
                '(lochness.json)\n')
        f.write('# eg) bash 1_encrypt_command.sh\n')
        command = f'crypt.py --encrypt {keyring_loc} ' \
                  f'-o {encrypt_keyring_loc}\n'
        f.write(command)

    # sync_command.sh
    with open(outdir / '2_sync_command.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# run this command to run sync.py\n')
        f.write('# eg) bash 2_sync_command.sh\n')
        command = f"sync.py -c {config_loc} --source {' '.join(sources)} " \
                "--debug --continuous\n"
        f.write(command)


def create_keyring_template(keyring_loc: Path, args: object) -> None:
    '''Create keyring template'''

    template_dict = {}
    template_dict['lochness'] = {}

    if 'redcap' in args.sources:
        template_dict['lochness']['REDCAP'] = {}
        template_dict['lochness']['SECRETS'] = {}
        for study in args.studies:
            study_dict = {f'redcap.{study}': [study]}
            study_secrete = '**PASSWORD_TO_ENCRYPTE_PROTECTED_DATA**'
            template_dict['lochness']['REDCAP'][study] = study_dict
            template_dict['lochness']['SECRETS'][study] = study_secrete

            # lower part of the keyring
            template_dict[f'redcap.{study}'] = {
                    'URL': f'**https://redcap.address.org/redcap/{study}**',
                    'API_TOKEN': {study: f'**API_TOEN_FOR_{study}**'}}

    if 'xnat' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'xnat.{study}'] = {
                'URL': f'**https://{study}-xnat.address.edu**',
                'USERNAME': f'**id_for_xnat_{study}**',
                'PASSWORD': f'**password_for_xnat_{study}**'}

    if 'box' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'box.{study}'] = {
                'CLIENT_ID': '**CLIENT_ID_FROM_BOX_APPS**',
                'CLIENT_SECRET': '**CLIENT_SECRET_FROM_BOX_APPS**',
                'API_TOEN': '**APITOKEN_FROM_BOX_APPS**'}

    if 'mindlamp' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'mindlamp.{study}'] = {
                "URL": "**api.lamp.digital**",
                "ACCESS_KEY": args.email,
                "SECRET_KEY": "**PASSWORD**"}

    if 'daris' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'daris.{study}'] = {
                "URL": "https://daris.researchsoftware.unimelb.edu.au",
                "TOKEN": "******",
                "PROJECT_CID": "******",
                }

    if 'rpms' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'rpms.{study}'] = {
                "RPMS_PATH": "/RPMS/DAILY/EXPORT/PATH",
                "TOKEN": "******",
                }

    with open(keyring_loc, 'w') as f:
        json.dump(template_dict, f,
                  sort_keys=False,
                  indent='  ',
                  separators=(',', ': '))


def create_config_template(config_loc: Path, args: object) -> None:
    '''Create config file template'''

    config_example = f'''keyring_file: {args.outdir}/.lochness.enc
phoenix_root: {args.outdir}/PHOENIX
pid: {args.outdir}/lochness.pid
stderr: {args.outdir}/lochness.stderr
stdout: {args.outdir}/lochness.stdout
poll_interval: {args.poll_interval}
ssh_user: {args.ssh_user}
ssh_host: {args.ssh_host}
sender: {args.email}
pii_table: {args.pii_csv}'''

    redcap_lines = f'''
redcap:
    phoenix_project:
        deidentify: True
    data_entry_trigger_csv: {args.det_csv}
    update_metadata: True'''

    config_example += redcap_lines

    if 'mediaflux' in args.sources:
        config_example += '\nmediaflux:'

        for study in args.studies:
            line_to_add = f'''
    {study}:
        namespace: /DATA/ROOT/UNDER/BOX
        delete_on_success: False
        file_patterns:
            actigraphy:
                - vendor: Philips
                  product: Actiwatch 2
                  data_dir: all_BWH_actigraphy
                  pattern: 'accel/*csv'
                  protect: True
                - vendor: Activinsights
                  product: GENEActiv
                  data_dir: all_BWH_actigraphy
                  pattern: 'GENEActiv/*bin,GENEActiv/*csv'
                - vendor: Insights
                  product: GENEActivQC
                  data_dir: all_BWH_actigraphy
                  pattern: 'GENEActivQC/*csv'
            phone:
                - data_dir: all_phone
                  pattern: 'processed/accel/*csv'
              '''

            config_example += line_to_add


    if 'box' in args.sources:
        config_example += '\nbox:'
        for study in args.studies:
            line_to_add = f'''
    {study}:
        base: /DATA/ROOT/UNDER/BOX
        delete_on_success: False
        file_patterns:
            actigraphy:
                   - vendor: Philips
                     product: Actiwatch 2
                     pattern: '*.csv'
                   - vendor: Activinsights
                     product: GENEActiv
                     pattern: 'GENEActiv/*bin,GENEActive/*csv'
                     compress: True
            mri_eye:
                   - vendor: SR Research
                     product: EyeLink 1000
                     pattern: '*.mov'
             '''

            config_example += line_to_add

    line_to_add = f'''
hdd:
    module_name:
        base: /PHOENIX
admins:
    - {args.email}
notify:
    __global__:
        - {args.email}
                '''
    config_example += line_to_add

    with open(config_loc, 'w') as f:
        f.write(config_example)

def create_example_meta_file_advanced(metadata: str,
                                      project_name: str,
                                      sources: List[str]) -> None:
    '''Create example meta files'''

    col_input_to_col_dict = {'xnat': 'XNAT',
                             'redcap': 'REDCap',
                             'box': 'Box',
                             'mindlamp': 'Mindlamp',
                             'mediaflux': 'Mediaflux',
                             'daris': 'Daris',
                             'rpms': 'RPMS'}

    df = pd.DataFrame({
        'Active': [1],
        'Consent': '1988-09-16',
        'Subject ID': 'subject01'})

    for source in sources:
        source_col = col_input_to_col_dict[source]
        if source == 'xnat':
            value = f'xnat.{project_name}:subproject:subject01'
        else:
            value = f'{source}.{project_name}:subject01'
        df.loc[0, source_col] = value

    df.to_csv(metadata, index=False)


def get_arguments():
    '''Get arguments'''
    parser = ap.ArgumentParser(description='Lochness template maker')
    parser.add_argument('-o', '--outdir',
                        required=True,
                        help='Path of the Lochness template')
    parser.add_argument('-s', '--studies',
                        required=True,
                        nargs='+',
                        help='Names of studies')
    parser.add_argument('-ss', '--sources',
                        required=True,
                        nargs='+',
                        help='List of sources, eg) xnat, redcap, box, '
                             'mindlamp, mediaflux, etc.')
    parser.add_argument('-e', '--email',
                        required=True,
                        help='Email address')
    parser.add_argument('-p', '--poll_interval',
                        default=86400,
                        help='Poll interval in seconds')
    parser.add_argument('-sh', '--ssh_host',
                        required=True,
                        help='ssh id')
    parser.add_argument('-su', '--ssh_user',
                        required=True,
                        help='ssh id')
    parser.add_argument('-det', '--det_csv',
                        default='data_entry_trigger.csv',
                        help='Redcap data entry trigger database csv path')
    parser.add_argument('-pc', '--pii_csv',
                        default='pii_convert.csv',
                        help='Location of table to be used in deidentifying '
                             'redcap fields')

    args = parser.parse_args()

    if Path(args.outdir).is_dir():
        sys.exit(f'*{args.outdir} already exists. Please provide another path')


    create_lochness_template(args)


if __name__ == '__main__':
    get_arguments()
