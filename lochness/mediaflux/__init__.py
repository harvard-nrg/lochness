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
import lochness.net as net
import lochness.tree as tree
from os.path import join as pjoin, basename, dirname
import cryptease as enc
import re
from subprocess import Popen
from tempfile import gettempdir
import pandas as pd


logger = logging.getLogger(__name__)
Module = lochness.lchop(__name__, 'lochness.')
Basename = lochness.lchop(__name__, 'lochness.mediaflux.')

CHUNK_SIZE = 65536


def base(Lochness, study_name):
    ''' get module-specific base box diretory '''
    return Lochness.get('mediaflux', {}) \
                   .get(study_name, {}) \
                   .get('namespace', '')


def get_box_object_based_on_name(client:boxsdk.client,
                                 box_folder_name: str,
                                 box_path_id: str = '0') \
                                         -> boxsdk.object.folder:
    '''Return Box folder object for the given folder name

    Currently, there is no api function to get box folder objects using
    path strings in Box.
        - https://stackoverflow.com/questions/16153409/is-there-any-easy-way-to-get-folderid-based-on-a-given-path

    This function will recursively search for a folder which
    has the same name as the `bx_head` and return its id.

    Key Arguments:
        client: Box client object
        box_folder_name: Name of the folder in interest, str
        box_path: Known parent id, str of int.
                  Default=0. This execute search from the root.

    Returns:
        box_folder_object
    '''
    box_folder_name = str(box_folder_name)

    # get list of files and directories under the top directory
    root_dir = client.folder(folder_id=box_path_id).get()

    # for entry in listing.entries:
    for file_or_folder in root_dir.get_items():
        if file_or_folder.type == 'folder' and \
           file_or_folder.name == box_folder_name:
            return file_or_folder


def walk_from_folder_object(root: str, box_folder_object) -> \
        Generator[str, list, list]:
    '''top-down os.path.walk that operates on a Box folder object

    Box does not support getting file or folder IDs with path strings,
    but only supports recursively searching files and folders under
    a folder with specific box ID.

    Key Arguments:
        root: path of the folder, str
        box_folder_object: folder object, Box Folder

    Yields:
        (root, box_folder_objects, box_file_object)
        root: root of the following objects, str
        box_folder_object: box folder objects, list
        box_file_object: box file objects, list
    '''
    box_folder_objects, box_file_objects = [], []
    for file_or_folder in box_folder_object.get_items():
        if file_or_folder.type == 'folder':
            box_folder_objects.append(file_or_folder)
        else:
            box_file_objects.append(file_or_folder)

    yield root, box_folder_objects, box_file_objects

    for box_dir_object in box_folder_objects:
        new_root = os.path.join(root, box_dir_object.name)
        for x in walk_from_folder_object(new_root, box_dir_object):
            yield x


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


def hash_retry(n):
    '''decorator to retry a box download on hash mismatch'''
    def wrapped(func):
        def f(*args, **kwargs):
            attempts = 1
            while attempts <= n:
                try:
                    return func(*args, **kwargs)
                except BoxHashError as e:
                    msg = f'attempt {attempts}/{n} failed with error: {e}'
                    logger.warn(msg)
                    attempts += 1
                    os.remove(e.filename)
            raise HashRetryError()
        return f
    return wrapped


class HashRetryError(Exception):
    pass


@hash_retry(3)
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


class DownloadError(Exception):
    pass


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


class BoxHashError(Exception):
    def __init__(self, message, filename):
        super(BoxHashError, self).__init__(message)
        self.filename = filename

class PatternError(Exception):
    pass

@net.retry(max_attempts=5)
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
        # loop through the items defined for the BOX data
        for datatype, products in iter(
                Lochness['mediaflux'][study_basename]['file patterns'].items()):
            print(datatype, products)

            for p in products:
                if '*' not in p['pattern']:
                    raise PatternError('Mediaflux pattern must include an asterisk e.g. *csv or GENEActiv/*csv')
                else:
                    p['pattern']= p['pattern'].replace('*','(.+?)')

                # construct mediaflux remote dir
                mf_remote_pattern= pjoin(mf_base, p['data_dir'], mf_subid, p['pattern'])
                mf_remote_dir = dirname(mf_remote_pattern)

                # obtain mediaflux remote paths
                with tempfile.TemporaryDirectory() as tmpdir:
                    diff_path= pjoin(tmpdir,'diff.csv')
                    cmd = (' ').join(['unimelb-mf-check',
                                      '--mf.config', mflux_cfg,
                                      '--direction down', tmpdir,
                                      mf_remote_dir,
                                      '-o', diff_path])

                    p= Popen(cmd, shell=True)
                    p.wait()

                    df= pd.read_csv(diff_path)
                    for remote in df['SRC_PATH'].values:
                        if not re.search(p['pattern'], remote):
                            continue
                            # mf_remote_pattern
                            # remote.strip("\"").split(':')[1]

                        # construct local path
                        protect = p.get('protect', False)
                        key = enc_key if protect else None
                        subj_dir = subject.protected_folder \
                            if protect else subject.general_folder

                        mf_local= pjoin(subj_dir, datatype, dirname(p['pattern']), basename(remote))
                        # ENH set different permissions
                        # GENERAL: 0o755, PROTECTED: 0700
                        os.makedirs(dirname(mf_local),exist_ok=True)

                        # ENH retry 5 times
                        # pass --check-csum so no redownload
                        # subprocess call unimelb-mf-download
                        cmd = (' ').join(['unimelb-mf-download',
                                          '--mf.config', mflux_cfg,
                                          '-o', mf_local,
                                          remote])

                        p = Popen(cmd, shell=True)
                        p.wait()

                        # ENH after download completes, retry 5 times based on --check-csum



@net.retry(max_attempts=5)
def sync(Lochness, subject, dry):
    '''call sync on the correct sub-module'''
    for module_name in subject.box:
        sync_module(Lochness, subject, module_name, dry)
