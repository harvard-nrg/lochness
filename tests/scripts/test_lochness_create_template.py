import lochness

from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

import lochness_create_template
from lochness_create_template import create_lochness_template
import pytest
import shutil


class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA']
        self.sources = ['Redcap', 'xNat', 'boX']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.det_csv = 'prac.csv'

@pytest.fixture
def args():
    return Args('test_lochness')


def test_create_lochness_template(args):
    create_lochness_template(args)
    shutil.rmtree(args.outdir)




def test_create_lochness_template_multiple_study(args):
    args.studies = ['StudyA', 'StudyB']
    create_lochness_template(args)
    pass
    # create_lochness_template(args)
