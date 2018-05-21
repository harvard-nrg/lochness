import os
import errno
import lochness
import logging
import paramiko
import getpass as gp
import posixpath as path
import lochness.functools as functools

logger = logging.getLogger(__name__)

def open(Lochness, f, mode):
    '''open a file over sftp'''
    _,sftp = sftp_client(Lochness['ssh_host'], Lochness['ssh_user'])
    try:
        logger.debug('sftp.open {0}'.format(f))
        return sftp.open(f, mode)
    except IOError as e:
        e.filename = f
        raise e

def listdir(Lochness, d):
    '''list a directory over sftp'''
    _,sftp = sftp_client(Lochness['ssh_host'], Lochness['ssh_user'])
    try:
        logger.debug('sftp.listdir {0}'.format(d))
        return sftp.listdir(d)
    except IOError as e:
        e.filename = d
        raise e

def makedirs(Lochness, d):
    '''recursive directory creation over sftp'''
    head,tail = path.split(d)
    if head != os.sep:
        makedirs(Lochness, head)
    _,sftp = sftp_client(Lochness['ssh_host'], Lochness['ssh_user'])
    try:
        sftp.mkdir(d)
    except IOError as e:
        if e.errno == None: # all we get for errno.EEXIST
            return
        e.filename = d
        raise e

@functools.lru_cache
def sftp_client(host, user):
    '''create ssh and sftp clients'''
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    client.load_system_host_keys()
    try:
        client.connect(host, username=user, password='')
    except paramiko.ssh_exception.AuthenticationException:
        password = gp.getpass('enter password for {0}@{1}: '.format(user, host))
        client.connect(host, username=user, password=password)
    return client,client.open_sftp()

