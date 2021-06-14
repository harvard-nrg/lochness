from jsonpath_ng import parse
import tempfile
import json
import cryptease as crypt
import yaml
import getpass as gp


def load_encrypted_keyring(enc_keyring_loc: str) -> dict:
    with open(enc_keyring_loc, 'rb') as fp:
        passphrase = gp.getpass('enter passphrase: ')
        key = crypt.key_from_file(fp, passphrase)
        content = b''
        for chunk in crypt.decrypt(fp, key):
            content += chunk

        keyring_dict = yaml.load(content, Loader=yaml.FullLoader)

    return keyring_dict


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
                "TOKEN": "",
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
        credentials = ['HOST', 'PORT', 'TRANSPORT', 'DOMAIN', 'USER', 'PASSWORD']

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


def search_and_hide_keys(input_dict, a={}):
    try:
        a = {}
        for k, v in input_dict.items():
            # if the key is of sensitive value
            if 'password' in k.lower() or \
                    'token' in k.lower() or \
                    k.lower().endswith('secret'):
                a[k] = search_and_hide_keys('****', a)

            # if the key is the SECRETS
            elif 'SECRETS' == k:
                a[k] = search_and_hide_keys(
                        dict(zip(v.keys(), ['***' for x in v.values()])), a)
            else:
                a[k] = search_and_hide_keys(v, a)
        return a

    except:
        # lowest item in the dict tree
        return input_dict


def print_keyring(keyring_dict):
    '''Print the structure of the Lochness['keyring'] without sensitive info'''

    keyring_wo_sensitive_info = search_and_hide_keys(keyring_dict)
    pretty_print_dict(keyring_wo_sensitive_info)


def pretty_print_dict(input_dict: dict):
    '''Pretty print dictionary'''
    with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as tmpfile:
        with open(tmpfile.name, 'w') as f:
            json.dump(input_dict, f,
                    sort_keys=False, indent='  ', separators=(',', ': '))

        with open(tmpfile.name, 'r') as f:
            lines = f.readlines()
            for i in lines:
                print(i.strip('\n'))


class KeyringError(Exception):
    pass

