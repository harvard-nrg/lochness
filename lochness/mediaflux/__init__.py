import os, sys
import gzip
import logging
import importlib
import lochness
import tempfile as tf
import cryptease as crypt
import lochness.net as net
from typing import Generator, Tuple
from pathlib import Path
import hashlib
from io import BytesIO
import lochness.keyring as keyring
from os.path import join as pjoin, basename, dirname, isfile
import cryptease as enc
import re
from subprocess import Popen
import tempfile
import pandas as pd
from numpy import nan
from distutils.spawn import find_executable

logger = logging.getLogger(__name__)
Module = lochness.lchop(__name__, 'lochness.')
Basename = lochness.lchop(__name__, 'lochness.mediaflux.')

CHUNK_SIZE = 65536


def base(Lochness, study_name):
    '''get study-specific namespace directory'''
    return Lochness.get('mediaflux', {}) \
                   .get(study_name, {}) \
                   .get('namespace', '')


class PatternError(Exception):
    pass


def sync_module(Lochness: 'lochness.config',
                subject: 'subject.metadata',
                study_name: 'mediaflux.study_name',
                dry: bool):
    '''sync mediaflux data for the subject'''

    if dry:
        raise NotImplementedError('--dry option is not implemented')

    study_basename = study_name.split('.')[1]

    for mf_subid in subject.mediaflux[study_name]:
        logger.debug(f'exploring {subject.study}/{subject.id}')
        _passphrase = keyring.passphrase(Lochness, subject.study)
        enc_key = enc.kdf(_passphrase)

        mflux_cfg= keyring.mediaflux_api_token(Lochness, study_name)
        
        mf_base = base(Lochness, study_basename)

        print(mf_base)

        for datatype, products in \
            iter(Lochness['mediaflux'][study_basename]['file_patterns'].items()):

            print(datatype, products)

            '''
            file_patterns:
                - vendor: Activinsights
                      product: GENEActiv
                      data_dir: all_BWH_actigraphy
                      pattern: 'GENEActiv/*bin,GENEActiv/*csv'
                actigraphy:
                    - vendor: Philips
                      product: Actiwatch 2
                      data_dir: all_BWH_actigraphy
                      pattern: 'accel/*csv'
                      protect: True
            
            '''


            for prod in products:
                for patt in prod['pattern'].split(','):

                    # consider the case with space
                    # pattern: 'GENEActiv/*bin, GENEActiv/*csv'
                    patt= patt.strip()

                    if '*' not in patt:
                        raise PatternError('Mediaflux pattern must include an asterisk e.g. *csv or GENEActiv/*csv')

                    # construct mediaflux remote dir
                    mf_remote_pattern= pjoin(mf_base, prod['data_dir'], mf_subid, patt)
                    mf_remote_dir = dirname(mf_remote_pattern)

                    # obtain mediaflux remote paths
                    with tempfile.TemporaryDirectory() as tmpdir:
                        diff_path= pjoin(tmpdir,'diff.csv')
                        cmd = (' ').join(['unimelb-mf-check',
                                          '--mf.config', mflux_cfg,
                                          '--nb-retries 5',
                                          '--direction down', tmpdir,
                                          mf_remote_dir,
                                          '-o', diff_path])

                        p= Popen(cmd, shell=True)
                        p.wait()

                        # ENH
                        # if dry: exit()

                        if not isfile(diff_path):
                            continue

                        df= pd.read_csv(diff_path)
                        for remote in df['SRC_PATH'].values:

                            if remote is nan:
                                continue

                            if not re.search(patt.replace('*','(.+?)'), remote):
                                continue
                            else:
                                remote= remote.split(':')[1]

                            # construct local path
                            protect = prod.get('protect', False)
                            key = enc_key if protect else None
                            subj_dir = subject.protected_folder \
                                if protect else subject.general_folder

                            mf_local= pjoin(subj_dir, datatype, dirname(patt), basename(remote))
                            # ENH set different permissions
                            # GENERAL: 0o755, PROTECTED: 0700
                            os.makedirs(dirname(mf_local),exist_ok=True)

                            # subprocess call unimelb-mf-download
                            cmd = (' ').join(['unimelb-mf-download',
                                              '--mf.config', mflux_cfg,
                                              '-o', dirname(mf_local),
                                              '--nb-retries 5',
                                              f'\"{remote}\"'])

                            p = Popen(cmd, shell=True)
                            p.wait()

                            # verify checksum after download completes
                            # if checksum does not match, data will be downloaded again
                            # ENH should we verify checksum 5 times?
                            cmd+= ' --csum-check'
                            p = Popen(cmd, shell=True)
                            p.wait()


def sync(Lochness, subject, dry):
    '''call sync on the correct sub-module'''
    
    # check availability of unimelb-mf-clients in PATH 
    for cmd in ['unimelb-mf-download','unimelb-mf-check']:
        exe= find_executable(cmd)
        if not exe:
            raise EnvironmentError(f'''

{cmd} not found in PATH. To resolve this:
* Download Linux 64bit unimelb-mf-clients client from
  https://gitlab.unimelb.edu.au/resplat-mediaflux/unimelb-mf-clients/-/tags
* Unzip it
* Finally, export the unimelb-mf-clients to your PATH
  export PATH=`pwd`/unimelb-mf-clients-0.5.8/bin/unix/:$PATH

''')

    for module_name in subject.mediaflux:
        sync_module(Lochness, subject, module_name, dry)
