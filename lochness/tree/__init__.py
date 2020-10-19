import os
import logging
from string import Template

Templates = {
    'actigraphy': {
        'raw': Template('${base}/actigraphy/raw'),
        'processed': Template('${base}/actigraphy/processed')
    }, 
    'mri': {
        'raw': Template('${base}/mri/raw'),
        'processed': Template('${base}/mri/processed')
    },
    'mri_behav': {
        'raw': Template('${base}/mri_behav/raw'),
        'processed': Template('${base}/mri_behav/processed')
    },
    'behav_qc': {
        'raw': Template('${base}/mri_behav/processed/behav_qc'),
    },
    'mri_eye': {
        'raw': Template('${base}/mri_eye/raw/eyeTracking'),
        'processed': Template('${base}/mri_eye/processed/eyeTracking')
    },
    'phone': {
        'raw': Template('${base}/phone/raw/${beiwe_id}'),
        'processed': Template('${base}/phone/processed')
    },
    'physio': {
        'raw': Template('${base}/physio/raw'),
        'processed': Template('${base}/physio/processed')
    },
    'cogassess': {
        'raw': Template('${base}/cogassess/raw'),
        'processed': Template('${base}/cogassess/processed')
    },
    'hearing': {
        'raw': Template('${base}/cogassess/raw'),
        'processed': Template('${base}/cogassess/processed'),
    },
    'retroquest': {
        'raw': Template('${base}/retroquest/raw'),
        'processed': Template('${base}/retroquest/processed')
    },
    'saliva': {
        'raw': Template('${base}/saliva/raw'),
        'processed': Template('${base}/saliva/processed')
    },
    'offsite_interview': {
        'raw': Template('${base}/offsite_interview/raw'),
        'processed': Template('${base}/offsite_interview/processed')
    },
    'onsite_interview': {
        'raw': Template('${base}/onsite_interview/raw'),
        'processed': Template('${base}/onsite_interview/processed')
    },
    'surveys': {
        'raw': Template('${base}/surveys/raw'),
        'processed': Template('${base}/surveys/processed')
    }
}

logger = logging.getLogger(__name__)

def get(type, base, **kwargs):
    '''get phoenix folder for a subject and datatype'''
    if type not in Templates:
        raise TreeError('no tree templates defined for {0}'.format(type))
    raw_folder = None
    processed_folder = None
    if 'raw' in Templates[type]:
        raw_folder = Templates[type]['raw'].substitute(base=base, **kwargs)
    if 'processed' in Templates[type]:
        processed_folder = Templates[type]['processed'].substitute(base=base, **kwargs)
    if kwargs.get('makedirs', True):
        if raw_folder and not os.path.exists(raw_folder):
            logger.debug('creating raw folder {0}'.format(raw_folder))
            os.makedirs(raw_folder)
        if processed_folder and not os.path.exists(processed_folder):
            logger.debug('creating processed folder {0}'.format(processed_folder))
            os.makedirs(processed_folder)
            os.chmod(processed_folder, 0o01777)
    return raw_folder

class TreeError(Exception):
    pass

