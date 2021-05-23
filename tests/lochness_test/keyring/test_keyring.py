import lochness
from pathlib import Path
from lochness.keyring import print_keyring

import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
from mock_args import LochnessArgs, mock_load
from config.test_config import create_config

class Args():
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = scripts_dir /'config.yml'
        self.archive_base = None
    def __str__(self):
        return 'haha'

def test_read_phoenix_data():
    args = Args()
    args.source = ['xnat', 'box']
    args.studies = ['StudyA']
    args.dry = [False]
    Lochness = mock_load(args.config, args.archive_base)

    print_keyring(Lochness)
