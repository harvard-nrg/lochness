import lochness
from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

import sync
import pytest
import lochness.config as config


class Args(object):
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = '/Users/kevin/Dropbox/PNL/Projects/' \
                '2021_lochness/suggest_config.yml'
        self.archive_base = None
    def __str__(self):
        return 'haha'

@pytest.fixture
def simple_args():
    arg = Args()
    return arg

def test_do():
    args = Args()
    Lochness = config.load(args.config, args.archive_base)

def test_read_phoenix_data():
    args = Args()
    args.source = ['xnat', 'box']
    args.studies = ['mclean']
    args.dry = [False]
    Lochness = config.load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject)
        # sync(Lochness, subject, Lochness.dry)
