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
        It is the subsection within the keyring_file where login credentials are written
        e.g. mediaflux.sydney. The latter is the remote name of the study under
        Mediaflux column in study_metadata.csv file. keyring_file is listed
        in the above configuration file. Thus the same key exists in study_metadata.csv,
        keyring_file, and in the configuration file.

    Returns
    -------
    : tuple
        Login credentials for the remote host specified in the subsection
    """

    import os

    if key not in Lochness['keyring']:
        raise KeyringError('\'{0}\' not in keyring'.format(key))

    # allow having both TOKEN and PASSWORD in keyring, prioritize TOKEN
    if 'TOKEN' in Lochness['keyring'][key]:
        credntials = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN']
    else:
        credntials = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN', 'DOMAIN', 'USER', 'PASSWORD']

    auths= Lochness['keyring'][key]
    mflux_cfg= os.path.join(Lochness['phoenix_root'], 'mflux.cfg')
    with open(mflux_cfg, 'w') as f:

        for item in credntials:
            if item not in auths:
                raise KeyringError(f'\'{item}\' not in {key}')
            f.write(f'{item.lower()}={auths[item]}\n')

    # for security, make the mflux.cfg readable by the owner only
    os.chmod(mflux_cfg, 0o600)

    return mflux_cfg


class KeyringError(Exception):
    pass

