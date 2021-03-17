import os
import yaml
import logging
import yaml.reader
import getpass as gp
import cryptease as crypt
import string

logger = logging.getLogger(__name__)


def load(f, archive_base=None):
    '''load configuration file and keyring'''
    logger.debug('loading configuration')

    with open(os.path.expanduser(f), 'rb') as fp:
        Lochness = _read_config_file(fp)

    if archive_base:
        Lochness['phoenix_root'] = archive_base
    if 'phoenix_root' not in Lochness:
        raise ConfigError('need either --archive-base or \'phoenix_root\' in config file')
    Lochness['phoenix_root'] = os.path.expanduser(Lochness['phoenix_root'])
    Lochness['keyring_file'] = os.path.expanduser(Lochness['keyring_file'])

    # box file pattern strings from the config to string template
    # regardless of the selected study in the args
    if 'box' in Lochness.keys():
        for box_study_name, box_study_dict in Lochness['box'].items():
            box_study_dict['file patterns'] = \
                _return_box_patterns_str_template(
                    box_study_dict['file patterns'])

    with open(Lochness['keyring_file'], 'rb') as fp:
        logger.info('reading keyring file {0}'.format(Lochness['keyring_file']))
        if 'NRG_KEYRING_PASS' in os.environ:
            load.passphrase = os.environ['NRG_KEYRING_PASS']
        if not load.passphrase:
            load.passphrase = gp.getpass('enter passphrase: ')
        key = crypt.key_from_file(fp, load.passphrase)
        content = b''
        for chunk in crypt.decrypt(fp, key):
            content += chunk
        try:
            Lochness['keyring'] = yaml.load(content, Loader=yaml.FullLoader)
        except yaml.reader.ReaderError:
            raise KeyringError('could not decrypt keyring {0} (wrong passphrase?)'.format(Lochness['keyring_file']))
    return Lochness


load.passphrase = None


class KeyringError(Exception):
    pass


def _return_box_patterns_str_template(box_patterns:dict) -> dict:
    '''Convert box patterns to string template

    Key Arguments:
        - box_patterns: 'box' part of the config.yml loaded as dict

    Returns:
        - new_box_patterns: dict, with the 'pattern' values converted
                            to string template

    Example `box_patterns` input

    {'mclean':
        {'base': 'codmtg',
        'delete_on_success': False,
        'file patterns':
            {'actigraphy':
                [{'vendor': 'Philips',
                  'product': 'Actiwatch 2',
                  'pattern': '.*\\.csv'},
                 {'vendor': 'Activinsights',
                  'product': 'GENEActiv',
                  'pattern': 'GENEActiv/.*(\\.csv|\\.bin)',
                  'compress': True}],
             'mri _eye':
                [{'vendor': 'SR Research',
                  'product': 'EyeLink 1000',
                  'pattern': '.*\\.mov'}],
             'behav_qc':
                [{'vendor': 'CNL Lab',
                  'product': 'unknown',
                  'pattern': '.*'}],
             'physio':
                [{'vendor': 'BIOPAC',
                  'product': 'AcqKnowledge',
                  'pattern': '.*\\.acq'}],
             'offsite_interview':
                [{'vendor': 'Zoom',
                  'product' : 'ZoomVideoConference',
                  'pattern': '.*/zoom_0\\.mp4', 'protect': True}],
             'onsite_interview':
                [{'vendor': 'Amir Zadeh (CMU)',
                  'product': 'Recorder.exe',
                  'pattern': '.*',
                  'protect': True},
                 {'vendor': 'Zoom',
                  'product': 'unknown',
                  'pattern': '.*(\\.MOV|\\.WAV)$',
                  'protect': True}]}},
     'otherStudy':
        {'base': 'codmtg2',
         'delete_on_success': False,
         'file patterns':
            {'actigraphy':
                [{'vendor': 'Philips',
                  'product': 'Actiwatch 2',
                  'pattern': '.*\\.csv'},
                 {'vendor': 'Activinsights',
                  'product': 'GENEActiv',
                  'pattern': 'GENEActiv/.*(\\.csv|\\.bin)',
                  'compress': True}]}}}
    '''
    box_patterns_new = {}
    for modality, modality_value_list in box_patterns.items():
        # modality - eg) actigraphy
        modality_value_list_new = []
        for modality_dict in modality_value_list:
            # modality_value - eg){'vendor': 'Philips', 'product':'xx', ...}
            modality_dict_new = {}
            for k, v in modality_dict.items():
                # k - eg) 'vendor'
                # v - eg) 'Philips'
                if k == 'pattern':
                    v = string.Template(v)
                modality_dict_new[k] = v
            modality_value_list_new.append(modality_dict_new)
        box_patterns_new[modality] = modality_value_list_new

    return box_patterns_new


def _read_config_file(fp):
    '''helper to read lochness configuration file'''
    try:
        cfg = yaml.load(fp.read(), Loader=yaml.FullLoader)
    except Exception as e:
        raise ConfigError('failed to parse {0} with error: {1}'.format(fp.name, e))
    return cfg


class ConfigError(Exception):
    pass


