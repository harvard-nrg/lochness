import os
import yaml
import logging
import yaml.reader
import getpass as gp
import cryptease as crypt

logger = logging.getLogger(__name__)

def load(f, archive_base=None):
    '''load configuration file and keyring'''
    logger.debug('loading configuration')
    with open(os.path.expanduser(f), 'rb') as fp:
        Lochness = _read_config_file(fp)
    if archive_base:
        Lochness['phoenix_root'] = archive_base
    if 'phoenix_root' not in Lochness:
        raise ConfigError('need either --archive-base or \'phoenix_root\' in config file')
    Lochness['phoenix_root'] = os.path.expanduser(Lochness['phoenix_root'])
    Lochness['keyring_file'] = os.path.expanduser(Lochness['keyring_file'])
    with open(Lochness['keyring_file'], 'rb') as fp:
        logger.info('reading keyring file {0}'.format(Lochness['keyring_file']))
        if 'NRG_KEYRING_PASS' in os.environ:
            load.passphrase = os.environ['NRG_KEYRING_PASS']
        if not load.passphrase:
            load.passphrase = gp.getpass('enter passphrase: ')
        key = crypt.key_from_file(fp, load.passphrase)
        content = b''
        for chunk in crypt.decrypt(fp, key):
            content += chunk
        try:
            Lochness['keyring'] = yaml.load(content, Loader=yaml.FullLoader)
        except yaml.reader.ReaderError:
            raise KeyringError('could not decrypt keyring {0} (wrong passphrase?)'.format(Lochness['keyring_file']))
    return Lochness
load.passphrase = None 

class KeyringError(Exception):
    pass

def _read_config_file(fp):
    '''helper to read lochness configuration file'''
    try:
        cfg = yaml.load(fp.read(), Loader=yaml.FullLoader)
    except Exception as e:
        raise ConfigError('failed to parse {0} with error: {1}'.format(fp.name, e))
    return cfg

class ConfigError(Exception):
    pass


