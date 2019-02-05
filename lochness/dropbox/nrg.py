import os
import re
import string
import lochness
import dropbox
import logging
import cryptease
import lochness.dropbox
import lochness.net as net
import lochness.tree as tree
import lochness.keyring as keyring

CONFIG = {
    'actigraphy': [
        {
            'vendor': 'Philips',
            'product': 'Actiwatch 2',
            'pattern': string.Template('${subject}_.*\.csv')
        },
        {
            'vendor': 'Activinsights',
            'product': 'GENEActiv',
            'pattern': string.Template('GENEActiv/${subject}_.*(\.csv|\.bin)'),
            'compress': True
        }
    ],
    'mri_eye': [
        {
            'vendor': 'SR Research',
            'product': 'EyeLink 1000',
            'pattern': string.Template('${subject}_.*\.mov')
        }
    ],
    'behav_qc': [
        {
            'vendor': 'CNL Lab',
            'product': 'unknown',
            'pattern': string.Template('.*')
        }
    ],
    'physio': [
        {
            'vendor': 'BIOPAC',
            'product': 'AcqKnowledge',
            'pattern': string.Template('${subject}_.*\.acq')
        }
    ],
    'onsite_interview': [
        {
            'vendor': 'Amir Zadeh (CMU)',
            'product': 'Recorder.exe',
            'pattern': string.Template('${subject}_.*'),
            'protect': True
        },
        {
            'vendor': 'Zoom',
            'product': 'unknown',
            'pattern': string.Template('${subject}_Zoom.*'),
            'protect': True
        }
    ]
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
        for datatype,products in iter(CONFIG.items()):
            dbx_head = os.path.join(os.sep, datatype, subject.study, dbx_sid)
            dbx_head_len = len(dbx_head)
            logger.debug('walking %s', dbx_head)
            for root,dirs,files in lochness.dropbox.walk(client, dbx_head):
                for f in files:
                    dbx_tail = os.path.join(root, f)[dbx_head_len:].lstrip(os.sep)
                    dbx_file = (dbx_head, dbx_tail)
                    product = _find_product(dbx_tail, products, subject=dbx_sid)
                    if not product:
                        continue
                    protect = product.get('protect', False)
                    compress = product.get('compress', False)
                    key = enc_key if protect else None
                    output_base = subject.protected_folder if protect else subject.general_folder
                    output_base = tree.get(datatype, output_base)
                    lochness.dropbox.save(client, dbx_file, output_base, key=key,
                                          compress=compress, delete=delete, dry=dry)
           
def _find_product(s, products, **kwargs):
    for product in products:
        pattern = product['pattern'].substitute(**kwargs)
        if re.match(pattern, s):
            #logger.debug('{0} is from product={1}, vendor={2}'.format(s, product['product'], product['vendor']))
            return product
    return None

