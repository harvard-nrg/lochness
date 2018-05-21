import os
import re
import lochness
import dropbox
import logging
import lochness.dropbox
import lochness.net as net
import lochness.tree as tree
import lochness.keyring as keyring

PATTERNS = {
    'mri_eye': '.*\.edf$',
    'mri_behav': '(?!.*\.edf$)',
    'behav_qc': '.*'
}

Module = lochness.lchop(__name__, 'lochness.')
Basename = lochness.lchop(__name__, 'lochness.dropbox.')

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
def sync(Lochness, subject, dry=False):
    delete = lochness.dropbox.delete_on_success(Lochness, Basename)
    logger.debug('delete_on_success for {0} is {1}'.format(Basename, delete))
    for dbx_sid in subject.dropbox[Module]:
        logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
        api_token = keyring.dropbox_api_token(Lochness, Module)
        client = dropbox.Dropbox(api_token)
        dbx_base = lochness.dropbox.base(Lochness, Basename)
        patterns = _batch_compile(PATTERNS)
        # walk dropbox 'Data_output' folder
        mri_eye_base = tree.get('mri_eye', subject.general_folder)
        mri_behav_base = tree.get('mri_behav', subject.general_folder)
        dbx_head = os.path.join(dbx_base, 'Data_output', dbx_sid)
        dbx_head_len = len(dbx_head)
        for root,dirs,files in lochness.dropbox.walk(client, dbx_head):
            for f in files:
                dbx_tail = os.path.join(root, f)[dbx_head_len:].lstrip(os.sep)
                dbx_file = dbx_head,dbx_tail
                if patterns['mri_eye'].match(f): # mri_eye
                    lochness.dropbox.save(client, dbx_file, mri_eye_base, dry=dry)
                elif patterns['mri_behav'].match(f): # mri_behav
                    lochness.dropbox.save(client, dbx_file, mri_behav_base, dry=dry)
        # walk dropbox 'Behav_QC' folder
        behav_qc_base = tree.get('behav_qc', subject.general_folder)
        dbx_head = os.path.join(dbx_base, 'Behav_QC', dbx_sid)
        dbx_head_len = len(dbx_head)
        for root,dirs,files in lochness.dropbox.walk(client, dbx_head):
            for f in files:
                dbx_tail = os.path.join(root, f)[dbx_head_len:].lstrip(os.sep)
                dbx_file = dbx_head,dbx_tail
                if patterns['behav_qc'].match(f): # behav_qc
                    lochness.dropbox.save(client, dbx_file, behav_qc_base, 
                                         delete=delete, dry=dry)

def _batch_compile(patterns):
    '''batch compile regular expressions'''
    compiled = {}
    for key,pattern in iter(patterns.items()):
        compiled[key] = re.compile(pattern)
    return compiled

