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
import tempfile as tf
import cryptease as crypt
import lochness.net as net
import lochness.hdd as hdd
import lochness.tree as tree
import lochness.config as config

BACKFILL_START_FALLBACK = '2015-10-01T00:00:00'

PROTECT = [
    'gps',
    'audio_recordings'
]

logger = logging.getLogger(__name__)

@net.retry(max_attempts=5)
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
            study_name_enc = study_name.encode('utf-8')
            dst_general_folder = tree.get('phone',
                                          subject.general_folder,
                                          beiwe_id=beiwe_id,
                                          BIDS=Lochness['BIDS'])
            dst_protected_folder = tree.get('phone',
                                            subject.protected_folder,
                                            beiwe_id=beiwe_id,
                                            BIDS=Lochness['BIDS'])
            # save a hidden file with the study id, original name, and sanitized name
            save_study_file(dst_general_folder, study_id, study_name)
            protected_streams = set(PROTECT)
            general_streams = set(mano.DATA_STREAMS) - protected_streams
            # begin backfill download of all GENERAL data streams
            logger.info('backfill general streams for subject={0}, study={1}, url={2}'.format(beiwe_id, study_name_enc, base_url))
            mano.sync.backfill(
                Keyring,
                study_id,
                beiwe_id,
                os.path.dirname(dst_general_folder),
                start_date=str(backfill_start),
                data_streams=general_streams
            )
            # begin backfill download of all PROTECTED data streams
            passphrase = Lochness['keyring']['lochness']['SECRETS'].get(subject.study, None)
            logger.info('backfill protected streams for subject={0}, study={1}, url={2}'.format(beiwe_id, study_name_enc, base_url))
            mano.sync.backfill(
                Keyring,
                study_id,
                beiwe_id,
                os.path.dirname(dst_protected_folder),
                start_date=str(backfill_start),
                data_streams=protected_streams,
                lock=protected_streams,
                passphrase=passphrase
            )
            # begin delta download of all GENERAL data streams
            registry = None
            registry_file = os.path.join(dst_general_folder, '.registry')
            if os.path.exists(registry_file):
                logger.debug('reading in registry file {0}'.format(registry_file))
                with open(registry_file) as fo:
                    registry = fo.read()
            else:
                logger.warn('no registry file on disk {0}'.format(registry_file))
            logger.info('delta download of general data streams for subject={0}, study={1}, url={2}'.format(beiwe_id, study_name_enc, base_url))
            archive = mano.sync.download(
                Keyring,
                study_id,
                beiwe_id,
                data_streams=general_streams,
                registry=registry
            )
            mano.sync.save(
                Keyring,
                archive,
                beiwe_id,
                os.path.dirname(dst_general_folder)
            )
            # begin delta download of all PROTECTED streams
            registry = None
            registry_file = os.path.join(dst_protected_folder, '.registry')
            if os.path.exists(registry_file):
                logger.debug('reading registry file {0}'.format(registry_file))
                with open(registry_file) as fo:
                    registry = fo.read()
            else:
                logger.warn('no registry file on disk {0}'.format(registry_file))
            logger.info('delta download of protected data streams for subject={0}, study={1}, url={2}'.format(beiwe_id, study_name_enc, base_url))
            archive = mano.sync.download(
                Keyring,
                study_id,
                beiwe_id,
                data_streams=protected_streams,
                registry=registry
            )
            mano.sync.save(
                Keyring,
                archive,
                beiwe_id,
                os.path.dirname(dst_protected_folder),
                lock=protected_streams,
                passphrase=passphrase
            )

def save_study_file(d, study_id, study_name):
    study_file = os.path.join(d, '.study')
    if os.path.exists(study_file):
        return
    sio = six.StringIO()
    writer = csv.writer(sio)
    writer.writerow(['ID', 'Name'])
    writer.writerow([study_id.encode('utf-8'), study_name.encode('utf-8')])
    sio.seek(0)
    logger.debug('saving study file {0}'.format(study_file))
    with tf.NamedTemporaryFile(dir=d, prefix='.', delete=False) as tmp:
        tmp.write(sio.read())
        tmp.flush()
        os.fsync(tmp.fileno())
    os.chmod(tmp.name, 0o0644)
    os.rename(tmp.name, study_file)
