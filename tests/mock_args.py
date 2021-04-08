from lochness.config import _read_config_file, ConfigError, yaml
import os
import string


class LochnessArgs(object):
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = 'config.yml'
        self.archive_base = None
    def __str__(self):
        return 'haha'


def mock_load(f, archive_base=None):
    '''load configuration file and keyring for test

    This function loads unencrypted json for testing purposes.
    - lochness/tests/suggest_config.yml
    - lochness/tests/lochness.json
    '''

    with open(os.path.expanduser(f), 'rb') as fp:
        Lochness = _read_config_file(fp)

    if archive_base:
        Lochness['phoenix_root'] = archive_base
    if 'phoenix_root' not in Lochness:
        raise ConfigError('need either --archive-base or '
                          '\'phoenix_root\' in config file')
    Lochness['phoenix_root'] = os.path.expanduser(Lochness['phoenix_root'])
    Lochness['keyring_file'] = os.path.expanduser(Lochness['keyring_file'])

    # box file pattern strings from the config to string template
    # regardless of the selected study in the args
    if 'box' in Lochness:
        for _, study_dict in Lochness['box'].items():
            for _, modality_values in study_dict['file patterns'].items():
                for modality_dict in modality_values:
                    modality_dict['pattern'] = \
                        string.Template(modality_dict['pattern'])

    with open(Lochness['keyring_file'], 'rb') as fp:
        Lochness['keyring'] = yaml.load(
                fp.read(), Loader=yaml.FullLoader)

    return Lochness

