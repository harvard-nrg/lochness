import os
import six
import csv
import mano
import json
import lochness
import logging
import mano.sync
import getpass as gp
import datetime as dt
import cryptease as crypt
import lochness.hdd as hdd
import lochness.tree as tree
import lochness.config as config

BACKFILL_START_FALLBACK = '2015-10-01T00:00:00'

PROTECT = [
    'gps',
    'audio_recordings'
]

logger = logging.getLogger(__name__)

def sync(Lochness, subject, dry=False):
    '''
    Sync beiwe data
    '''
    logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
    backfill_start = Lochness['beiwe'].get('backfill_start', BACKFILL_START_FALLBACK)
    if str(backfill_start).strip().lower() == 'consent':
        backfill_start = subject.consent
    for alias,beiwe_uids in iter(subject.beiwe.items()):
        logger.debug('getting {0} from keyring'.format(alias))
        Keyring = mano.keyring(alias, keyring_file=Lochness['keyring_file'], passphrase=config.load.passphrase)
        base_url = Keyring['URL']
        for uid in beiwe_uids:
            study_frag,beiwe_id = uid
            study_name,study_id = mano.expand_study_id(Keyring, study_frag)
            logger.info('backfill subject={0}, study={1}, url={2}'.format(beiwe_id, study_name, base_url))
            dst_beiwe_folder = tree.get('phone', subject.general_folder, beiwe_id=beiwe_id)
            # save a hidden file with the study id, original name, and sanitized name
            save_study_file(dst_beiwe_folder, study_id, study_name)
            # do backfill
            passphrase = Lochness['keyring']['lochness']['SECRETS'].get(subject.study, None)
            mano.sync.backfill(Keyring, study_id, beiwe_id, os.path.dirname(dst_beiwe_folder), 
                               str(backfill_start), PROTECT, passphrase)
            # check for registry file
            registry_file = os.path.join(dst_beiwe_folder, '.registry')
            logger.debug('reading registry file {0}'.format(registry_file))
            if not os.path.exists(registry_file):
                logger.error('could not find registry file {0}'.format(registry_file))
                continue
            # read registry file
            with open(registry_file) as fo:
                registry = fo.read()
            # sync up to today
            logger.info('delta subject={0}, study={1}, url={2}'.format(beiwe_id, study_name, base_url))
            archive = mano.sync.download(Keyring, study_id, beiwe_id, registry=registry)
            mano.sync.save(Keyring, archive, beiwe_id, dst_beiwe_folder, PROTECT, passphrase)

def save_study_file(d, study_id, study_name):
    study_file = os.path.join(d, '.study')
    if os.path.exists(study_file):
        return
    sio = six.StringIO()
    writer = csv.writer(sio)
    writer.writerow(['ID', 'Name'])
    writer.writerow([study_id, study_name])
    sio.seek(0)
    logger.debug('saving study file {0}'.format(study_file))
    lochness.atomic_write(study_file, sio.read().encode('utf-8'))

