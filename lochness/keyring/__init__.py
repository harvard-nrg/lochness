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

    from os.path import join as pjoin

    if key not in Lochness['keyring']:
        raise KeyringError('\'{0}\' not in keyring'.format(key))

    # allow having both TOKEN and PASSWORD in keyring, prioritize TOKEN
    if 'TOKEN' in Lochness['keyring'][key]:
        auth_keys = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN']
    else:
        auth_keys = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN', 'DOMAIN', 'USER', 'PASSWORD']

    auth_values= Lochness['keyring'][key]
    with open(pjoin(Lochness['phoenix_root'], 'mflux.cfg'), 'w') as f:

        for item in auth_keys:
            if item not in :
                raise KeyringError(f'\'{item}\' not in {key}')
            f.write(item.lower():)


    return tuple([Lochness['keyring'][key][x] for x in auths])


class KeyringError(Exception):
    pass

