import os
import gzip
import dropbox
import logging
import importlib
import tempfile as tf
import cryptease as crypt
import lochness.net as net
from . import hash as hash

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024

def delete_on_success(Lochness, module_name):
    ''' get module-specific delete_on_success flag with a safe default '''
    value = Lochness.get('dropbox', dict()) \
                   .get(module_name, dict()) \
                   .get('delete_on_success', False)
    # if this is anything but a boolean, just return False
    if not isinstance(value, bool):
        return False
    return value

def base(Lochness, module_name):
    ''' get module-specific base dropbox diretory '''
    return Lochness.get('dropbox', {}) \
                  .get(module_name, {}) \
                  .get('base', '')

@net.retry(max_attempts=5)
def sync(Lochness, subject, dry):
    '''call sync on the correct sub-module'''
    for module in subject.dropbox:
        get(module).sync(Lochness, subject, dry)

def get(module):
    '''return a specific dropbox module'''
    try:
        module = '.' + module
        return importlib.import_module(module, 'lochness')
    except ImportError:
        raise ImportError('no module {0} in package lochness.dropbox'.format(module))

def walk(client, top=''):
    '''top-down os.path.walk that operates on a Dropbox folder'''
    dirs,files = [],[]
    try:
        listing = client.files_list_folder(top)
    except dropbox.exceptions.ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():    
            logger.info('path does not exist {}'.format(top))
        else:
            raise e
        return
    for entry in listing.entries:
        if isinstance(entry, dropbox.files.FolderMetadata):
            dirs.append(os.path.basename(entry.path_display))
        else:
            files.append(os.path.basename(entry.path_display))
    yield top, dirs, files
    for d in dirs:
        new_path = os.path.join(os.sep, top, d)
        for x in walk(client, new_path):
            yield x

def save(client, dbx_file, out_base, key=None, compress=False, delete=False, dry=False):
    '''save a dropbox file to an output directory'''
    dbx_head,dbx_tail = dbx_file
    dbx_fullfile = os.path.join(dbx_head, dbx_tail)
    ext = '.lock' if key else ''
    ext = ext + '.gz' if compress else ext
    local_fullfile = os.path.join(out_base, dbx_tail + ext)
    if os.path.exists(local_fullfile):
        return
    local_dirname = os.path.dirname(local_fullfile)
    if not os.path.exists(local_dirname):
        os.makedirs(local_dirname)
    if not dry:
        try:
            _save(client, dbx_fullfile, local_fullfile, key, compress)
            if delete:
                logger.debug('deleting file on dropbox {0}'.format(dbx_fullfile))
                _delete(client, dbx_fullfile)
        except HashRetryError:
            raise DownloadError('too many failed attempts downloading {0}'.format(dbx_fullfile))

def hash_retry(n):
    '''decorator to retry a dropbox download on hash mismatch'''
    def wrapped(func):
        def f(*args, **kwargs):
            attempts = 1
            while attempts <= n:
                try:
                    return func(*args, **kwargs)
                except DropboxHashError as e:
                    logger.warn('attempt {0}/{1} failed with error: {2}'.format(attempts, n, e))
                    attempts += 1
                    os.remove(e.filename)
            raise HashRetryError()
        return f 
    return wrapped

class HashRetryError(Exception):
    pass

def _delete(client, dbx_fullfile):
    try:
        md = client.files_delete(dbx_fullfile)
    except dropbox.exceptions.ApiError as e:
        raise DeletionError('error deleting file {0}'.format(dbx_fullfile))

class DeletionError(Exception):
    pass

@hash_retry(3)
def _save(client, dbx_fullfile, local_fullfile, key, compress):
    # request the file from dropbox.com
    try:
        md,resp = client.files_download(dbx_fullfile)
    except dropbox.exceptions.ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            raise DownloadError('error downloading file {0}'.format(dbx_fullfile))
        else:
            raise e
    local_dirname = os.path.dirname(local_fullfile)
    logger.info('saving {0} to {1} '.format(dbx_fullfile, local_fullfile))
    # write the file content to a temporary location
    if key:
        _stream = crypt.encrypt(resp.raw, key, chunk_size=CHUNK_SIZE)
        tmp_name = _savetemp(crypt.buffer(_stream), local_dirname, compress=compress)
    else:
        tmp_name = _savetemp(resp.raw, local_dirname, compress=compress)
    # verify the file and rename to final local destination
    logger.debug('verifying temporary file {0}'.format(tmp_name))
    verify(tmp_name, md.content_hash, key=key, compress=compress)
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
    '''compute dropbox hash of a local file and compare to content_hash'''
    hasher = hash.DropboxContentHasher()
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
        message = 'hash mismatch detected for {0}'.format(f)
        raise DropboxHashError(message, f)

class DropboxHashError(Exception):
    def __init__(self, message, filename):
        super(DropboxHashError, self).__init__(message)
        self.filename = filename

