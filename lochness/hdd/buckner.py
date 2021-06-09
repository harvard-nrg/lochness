'''
Buckner Lab hard drives are laid out like this (most of the time)
'''
import os
import re
import logging
import lochness
import lochness.hdd as hdd
import lochness.ssh as ssh
import lochness.tree as tree

logger = logging.getLogger(__name__)

IGNORE = ['.*(.DS_Store|UNKNOWN|batchlog.txt)']

def sync(Lochness, subject, dry=False, datatypes=None):
    logger.debug('exploring {0}/{1}'.format(subject.study, subject.id))
    general_folder = os.path.join(Lochness['phoenix_root'], 'GENERAL')
    # PHOENIX/
    hdd_root = Lochness['buckner']['hdd_root']
    hdd_phoenix_dir = os.path.join(hdd_root, 'PHOENIX')
    if not os.path.exists(hdd_phoenix_dir):
        raise HDDError('directory not found {0}'.format(hdd_phoenix_dir))
    # PHOENIX/{datatype}
    for datatype in hdd.listdir(hdd_phoenix_dir, IGNORE):
        if datatypes and datatype not in datatypes:
            continue
        datatype_dir = os.path.join(hdd_phoenix_dir, datatype)
        # PHOENIX/{datatype}/{study}
        for study in hdd.listdir(datatype_dir, IGNORE):
            phoenix_study_dir = os.path.join(general_folder, study)
            phoenix_sids = lochness.listdir(Lochness, phoenix_study_dir)
            study_dir = os.path.join(datatype_dir, study)
            # PHOENIX/{datatype}/{study}/{sid}
            for sid in hdd.listdir(study_dir, IGNORE):
                if sid not in phoenix_sids:
                    logger.warn('subject not in PHOENIX {0}/{1}'.format(study, sid))
                    continue
                src = os.path.join(study_dir, sid)
                _dst = tree.get(datatype, subject.general, makedirs=False, BIDS=Lochness['BIDS'])
                ssh.makedirs(Lochness, _dst)
                dst = '{0}@{1}:{2}'.format(Lochness['ssh_user'], Lochness['ssh_host'], _dst)
                hdd.rsync(src, dst, dry=dry)
        raw_input('hit enter to continue to next datatype')

class HDDError(Exception):
    pass

