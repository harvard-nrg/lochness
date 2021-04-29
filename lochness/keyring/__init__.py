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
        It is the subsection within the keyring_file where login credentials are noted
        e.g. mediaflux.sydney. The latter is the remote name of the study under
        Mediaflux column in STUDY_metadata.csv file. Meanwhile, keyring_file is listed
        in the above configuration file.

        Content of STUDY_metadata.csv:

        Active,Consent,Subject ID,Mediaflux,XNAT
        1,2017-02-09,sub01234,mediaflux.bwh:01234,xnat:HCPEP-BWH:01234
        1,2017-02-09,sub01235,mediaflux.bwh:01235,xnat:HCPEP-BWH:01235
        1,2017-02-09,sub01236,mediaflux.bwh:01236,xnat:HCPEP-BWH:01236

        Content of keyring_file:

        {
            "lochness": {
                "SECRETS": {
                    "BWH":""
                }
            },
            "mediaflux.bwh": {
                "HOST": "mediaflux.researchsoftware.unimelb.edu.au",
                "PORT": "443",
                "TRANSPORT": "https",
                "TOKEN":
                "DOMAIN": "",
                "USER": "",
                "PASSWORD": ""
            }
        }

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
        credentials = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN']
    else:
        credentials = ['HOST', 'PORT', 'TRANSPORT', 'TOKEN', 'DOMAIN', 'USER', 'PASSWORD']

    auths= Lochness['keyring'][key]
    mflux_cfg= os.path.join(Lochness['phoenix_root'], 'mflux.cfg')
    with open(mflux_cfg, 'w') as f:

        for item in credentials:
            if item not in auths:
                raise KeyringError(f'\'{item}\' not in {key}')
            f.write(f'{item.lower()}={auths[item]}\n')

    # for security, make the mflux.cfg readable by the owner only
    os.chmod(mflux_cfg, 0o600)

    return mflux_cfg


class KeyringError(Exception):
    pass

