def passphrase(Lochness, study):
    '''get passphrase for study from keyring'''

    if study not in Lochness['keyring']['lochness']['SECRETS']:
        raise KeyringError('lochness.SECRETS.{0} not found'.format(study))
    return Lochness['keyring']['lochness']['SECRETS'][study]


def dropbox_api_token(Lochness, key):
    '''get dropbox api token from keyring'''
    if key not in Lochness['keyring']:
        raise KeyringError('\'{0}\' not in keyring'.format(key))
    if 'API_TOKEN' not in Lochness['keyring'][key]:
        raise KeyringError('\'API_TOKEN\' not in {0}'.format(key))
    return Lochness['keyring'][key]['API_TOKEN']


def box_api_token(Lochness, key):
    '''get box api token from keyring'''
    if key not in Lochness['keyring']:
        raise KeyringError('\'{0}\' not in keyring'.format(key))
    if 'API_TOKEN' not in Lochness['keyring'][key]:
        raise KeyringError('\'API_TOKEN\' not in {0}'.format(key))
    return (Lochness['keyring'][key]['CLIENT_ID'],
            Lochness['keyring'][key]['CLIENT_SECRET'],
            Lochness['keyring'][key]['API_TOKEN'])


def mediaflux_api_token(Lochness, key):
    """
    Get mediaflux login credentials from an encrypted keyring file

    Parameters
    ----------
    Lochness : dict
        It is the configuration obtained from a file provided via scripts/sync.py --config

    key : str
        It is the subsection within the keyring_file (listed in the above configuration file)
        where login credentials are written e.g. mediaflux.sydney, mediaflux.melbourne etc.

    Returns
    -------
    : tuple
        Login credentials for the remote host specified in the subsection
    """
    
    if key not in Lochness['keyring']:
        raise KeyringError('\'{0}\' not in keyring'.format(key))

    auths = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN', 'DOMAIN', 'USER', 'PASSWORD']

    for item in auths:
        if item not in Lochness['keyring'][key]:
            raise KeyringError(f'\'{item}\' not in {key}')

    return tuple([Lochness['keyring'][key][x] for x in auths])


class KeyringError(Exception):
    pass

