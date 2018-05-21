import re
import os
import lochness
import logging
import importlib
import subprocess as sp
import lochness.functools as functools

logger = logging.getLogger(__name__)

def get(module):
    '''return a specific hdd module'''
    try:
        module = '.' + module
        return importlib.import_module(module, 'lochness.hdd')
    except ImportError:
        raise ImportError('no module {0} in package lochness.hdd'.format(module))

def listdir(path, ignore=None):
    ignore = _batch_compile(ignore)
    for item in os.listdir(path):
        if _match(item, ignore):
            continue
        yield item

def rsync(source, destination, progress=False, dry=False):
    '''rsync command wrapper'''
    if not os.path.exists(source):
        raise RsyncError('source does not exist {0}'.format(source))
    if os.path.isdir(source):
        source = source.rstrip(os.sep) + os.sep
        destination = destination.rstrip(os.sep) + os.sep
    cmd = ['rsync', '-rlp', '--exclude', '*.DS_Store']
    if progress:
        cmd.append('-P')
    cmd.extend([source, destination]) 
    try:
        logger.debug('running {0}'.format(cmd))
        if not dry:
            _ = sp.check_output(cmd, stderr=sp.PIPE)
    except sp.CalledProcessError as e:
        raise RsyncError(e)

class RsyncError(Exception):
    pass

@functools.lru_cache
def _batch_compile(patterns):
    '''helper for compiling a list of regular expressions'''
    if not patterns:
        return []
    return [re.compile(x) for x in patterns]

def _match(x, patterns):
    '''helper to match a string against a list of regular expressions'''
    for pattern in patterns:
        if pattern.match(x):
            return True
    return False

