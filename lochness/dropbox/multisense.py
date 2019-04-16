import os
import re
import lochness
import dropbox
import logging
import cryptease
import lochness.dropbox
import lochness.net as net
import lochness.tree as tree
import lochness.keyring as keyring
from string import Template

CONFIG = {
    'GENERAL': {
        'actigraphy': Template('${subject}_.*\.csv'),
        'mri_eye': Template('${subject}_.*\.mov'),
        'behav_qc': Template('.*'),
        'physio': Template('${subject}_.*\.acq')
    },
    'PROTECTED': {
        'onsite_interview': Template('${subject}_.*')
    }
}

Module = lochness.lchop(__name__, 'lochness.')
Basename = lochness.lchop(__name__, 'lochness.dropbox.')

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
def sync(Lochness, subject, dry):
    delete = lochness.dropbox.delete_on_success(Lochness, Basename)
    logger.debug('delete_on_success for {0} is {1}'.format(Basename, delete))
    for dbx_sid in subject.dropbox[Module]:
        logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
        _passphrase = keyring.passphrase(Lochness, subject.study)
        enc_key = cryptease.kdf(_passphrase)
        api_token = keyring.dropbox_api_token(Lochness, Module)
        client = dropbox.Dropbox(api_token)
        patterns = _batch_compile(CONFIG, dbx_sid)
        for category,datatype in _iterate(CONFIG):
            output_base = subject.protected_folder if category == 'PROTECTED' else subject.general_folder
            output_base = tree.get(datatype, output_base)
            dbx_head = os.path.join(os.sep, datatype, subject.study)
            # shim the dropbox head for certain data types
            if datatype == 'onsite_interview':
                dbx_head = os.path.join(dbx_head, 'output')
            elif datatype == 'behav_qc':
                dbx_head = os.path.join(dbx_head, dbx_sid)
            dbx_head_len = len(dbx_head)
            for root,dirs,files in lochness.dropbox.walk(client, dbx_head):
                for f in files:
                    dbx_tail = os.path.join(root, f)[dbx_head_len:].lstrip(os.sep)
                    dbx_file = dbx_head,dbx_tail
                    if patterns[datatype].match(dbx_tail):
                        key = enc_key if category == 'PROTECTED' else None
                        lochness.dropbox.save(client, dbx_file, output_base,
                                             key=key, delete=delete, dry=dry)

def _iterate(config):
    for category,blob in iter(config.items()):
        category = category.upper()
        for datatype,_ in iter(blob.items()):
            yield category,datatype

def _batch_compile(patterns, sid):
    '''batch compile all regular expressions'''
    compiled = {}
    for patterns in patterns.values():
        for key,pattern in iter(patterns.items()):
            pattern = pattern.substitute(subject=sid)
            compiled[key] = re.compile(pattern)
    return compiled
