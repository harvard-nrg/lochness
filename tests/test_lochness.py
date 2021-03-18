import lochness
from lochness import config
from config.test_config import create_config
import pytest


class Args(object):
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = 'suggest_config.yml'
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

def test_read_phoenix_metadata():
    args = Args()
    args.source = ['xnat', 'box']
    args.studies = ['mclean']
    args.dry = [False]
    config_string, fp = create_config()
    # cfg = lochness.config._read_config_file(fp)

    Lochness = config.load(args.config, args.archive_base)
    print(Lochness)
    for subject in lochness.read_phoenix_metadata(Lochness):
        print(subject)
        print(subject.box['box.mclean'])
        for module in subject.box:
            print(module)

