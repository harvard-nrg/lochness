import lochness.box
from lochness import config
from pathlib import Path

import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
from config.test_config import create_config


class Args(object):
    def __init__(self):
        self.source = ['xnat', 'box', 'redcap']
        self.config = scripts_dir /'suggest_config.yml'
        self.archive_base = None
    def __str__(self):
        return 'haha'

def test_box_sync_module():
    args = Args()
    args.source = ['xnat', 'box']
    args.studies = ['mclean']
    args.dry = [False]
    config_string, fp = create_config()
    # cfg = lochness.config._read_config_file(fp)

    Lochness = config.load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness):
        for module in subject.box:
            print(Lochness)
            lochness.box.sync_module(Lochness,
                                     subject,
                                     module,
                                     dry=True)

