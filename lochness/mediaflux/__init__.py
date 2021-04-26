import os, sys
import gzip
import logging
import importlib
import boxsdk
import lochness
import tempfile as tf
import cryptease as crypt
import lochness.net as net
from typing import Generator, Tuple
from pathlib import Path
import hashlib
from io import BytesIO
import lochness.keyring as keyring
import lochness.net as net
import lochness.tree as tree
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
    ''' get module-specific base box diretory '''
    return Lochness.get('mediaflux', {}) \
                   .get(study_name, {}) \
                   .get('namespace', '')




def save(box_file_object: boxsdk.object.file,
         box_path_tuple: Tuple[str, str],
         out_base: str,
         key=None,
         compress=False, delete=False, dry=False):
    '''save a box file to an output directory'''
    # file path
    box_path_root, box_path_name = box_path_tuple
    box_fullpath = os.path.join(box_path_root, box_path_name)

    # extension
    ext = '.lock' if key else ''
    ext = ext + '.gz' if compress else ext

    # local path
    local_fullfile = os.path.join(out_base, box_path_name + ext)

    if os.path.exists(local_fullfile):
        return
    local_dirname = os.path.dirname(local_fullfile)
    if not os.path.exists(local_dirname):
        os.makedirs(local_dirname)

    if not dry:
        try:
            _save(box_file_object, box_fullpath, local_fullfile, key, compress)
            if delete:
                logger.debug(f'deleting file on box {box_fullpath}')
                _delete(box_file_object, box_fullpath)
        except HashRetryError:
            msg = f'too many failed attempts downloading {box_fullpath}'
            raise DownloadError(msg)




def _save(box_file_object, box_fullpath, local_fullfile, key, compress):
    # request the file from box.com
    try:
        content = BytesIO(box_file_object.content())
    except boxsdk.BoxAPIException as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            msg = f'error downloading file {box_fullpath}'
            raise DownloadError(msg)
        else:
            raise e
    local_dirname = os.path.dirname(local_fullfile)
    logger.info(f'saving {box_fullpath} to {local_fullfile} ')

    # write the file content to a temporary location
    if key:
        _stream = crypt.encrypt(content, key, chunk_size=CHUNK_SIZE)
        tmp_name = _savetemp(crypt.buffer(_stream),
                             local_dirname,
                             compress=compress)
    else:
        tmp_name = _savetemp(content, local_dirname, compress=compress)

    # verify the file and rename to final local destination
    logger.debug(f'verifying temporary file {tmp_name}')
    verify(tmp_name, box_file_object.sha1, key=key, compress=compress)
    os.chmod(tmp_name, 0o0644)
    os.rename(tmp_name, local_fullfile)




def _savetemp(content, dirname=None, compress=False):
    '''save content to a temporary file with optional compression'''
    if not dirname:
        dirname = tf.gettempdir()
    fo = tf.NamedTemporaryFile(dir=dirname, prefix='.', delete=False)
    if compress:
        fo = gzip.GzipFile(fileobj=fo, mode='wb')

    while 1:
        buf = content.read(CHUNK_SIZE)
        if not buf:
            break
        fo.write(buf)

    fo.flush()
    os.fsync(fo.fileno())
    fo.close()
    return fo.name


def verify(f, content_hash, key=None, compress=False):
    '''compute box hash of a local file and compare to content_hash'''
    hasher = hashlib.sha1()
    CHUNK_SIZE = 65536
    fo = open(f, 'rb')
    if compress:
        fo = gzip.GzipFile(fileobj=fo, mode='rb')
    if key:
        fo = crypt.buffer(crypt.decrypt(fo, key, chunk_size=CHUNK_SIZE))
    while 1:
        buf = fo.read(CHUNK_SIZE)
        if not buf:
            break
        hasher.update(buf)
    fo.close()
    if hasher.hexdigest() != content_hash:
        message = f'hash mismatch detected for {f}'
        raise BoxHashError(message, f)


class PatternError(Exception):
    pass


def sync_module(Lochness: 'lochness.config',
                subject: 'subject.metadata',
                study_name: 'mediaflux.study_name',
                dry: bool):


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
