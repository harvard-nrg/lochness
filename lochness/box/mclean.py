import os, sys
from os.path import join, basename
import re
import string
from boxsdk import Client, OAuth2
import lochness
import logging
import cryptease as enc
import lochness.dropbox
import lochness.box
import lochness.net as net
import lochness.tree as tree
import lochness.keyring as keyring

CONFIG = {
    'actigraphy': [
        {
            'vendor': 'Philips',
            'product': 'Actiwatch 2',
            'pattern': string.Template('.*\.csv')
        },
        {
            'vendor': 'Activinsights',
            'product': 'GENEActiv',
            'pattern': string.Template('GENEActiv/.*(\.csv|\.bin)'),
            'compress': True
        }
    ],
    'mri_eye': [
        {
            'vendor': 'SR Research',
            'product': 'EyeLink 1000',
            'pattern': string.Template('.*\.mov')
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
            'pattern': string.Template('.*\.acq')
        }
    ],
    'offsite_interview': [
        {
            'vendor': 'Zoom',
            'product': 'ZoomVideoConference',
            'pattern': string.Template('.*/zoom_0\.mp4'),
            'protect': True
        },
    ],
    'onsite_interview': [
        {
            'vendor': 'Amir Zadeh (CMU)',
            'product': 'Recorder.exe',
            'pattern': string.Template('.*'),
            'protect': True
        },
        {
            'vendor': 'Zoom',
            'product': 'unknown',
            'pattern': string.Template('.*(\.MOV|\.WAV)$'),
            'protect': True
        }
    ]
}

Module = lochness.lchop(__name__, 'lochness.')
Basename = lochness.lchop(__name__, 'lochness.box.')

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
def sync(Lochness: 'lochness.config', subject: 'subject.metadata', dry: bool):
    '''Sync box data for the subject'''
    # delete on success
    delete = lochness.box.delete_on_success(Lochness, Basename)
    logger.debug(f'delete_on_success for {Basename} is {delete}')

    for bx_sid in subject.box[Module]:
        logger.debug(f'exploring {subject.study}/{subject.id}')
        _passphrase = keyring.passphrase(Lochness, subject.study)
        enc_key = enc.kdf(_passphrase)

        client_id, client_secret, api_token = keyring.box_api_token(Lochness, Module)

        # box authentication
        auth = OAuth2(
            client_id=client_id,
            client_secret=client_secret,
            access_token=api_token,
        )
        client = Client(auth)

        bx_base = lochness.box.base(Lochness, Basename)

        # get the id of the bx_base path in box
        bx_base_obj = lochness.box.get_box_object_based_on_name(
                client, bx_base, '0')

        # loop through the items defined for the BOX data
        for datatype, products in iter(CONFIG.items()):

            subject_obj = lochness.box.get_box_object_based_on_name(
                    client, bx_sid, bx_base_obj.id)
            datatype_obj = lochness.box.get_box_object_based_on_name(
                    client, datatype, subject_obj.id)

            # full path
            bx_head = join(bx_base,
                           datatype,
                           bx_sid)

            logger.debug('walking %s', bx_head)

            # if the directory is empty
            if datatype_obj == None:
                continue

            # walk through the root directory
            for root, dirs, files in lochness.box.walk_from_folder_object(
                    bx_head, datatype_obj):

                for box_file_object in files:
                    bx_tail = join(basename(root), box_file_object.name)
                    product = _find_product(bx_tail, products, subject=bx_sid)
                    if not product:
                        continue

                    protect = product.get('protect', False)
                    compress = product.get('compress', False)
                    key = enc_key if protect else None
                    output_base = subject.protected_folder \
                                  if protect else subject.general_folder

                    if 'processed' in root:
                        processed = True
                    else:
                        processed = False

                    # output_base = tree.get(datatype, output_base)
                    output_base = tree.return_local_path(
                            datatype,
                            output_base,
                            processed=processed)

                    lochness.box.save(box_file_object,
                                      (root, box_file_object.name),
                                      output_base, key=key,
                                      compress=False, delete=False,
                                      dry=False)


def _find_product(s, products, **kwargs):
    for product in products:
        pattern = product['pattern'].safe_substitute(**kwargs)
        if re.match(pattern, s):
            return product
    return None
