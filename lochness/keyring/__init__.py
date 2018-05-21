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

class KeyringError(Exception):
    pass

