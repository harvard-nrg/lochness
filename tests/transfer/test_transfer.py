import lochness
import os
import shutil
from lochness.transfer import get_updated_files, compress_list_of_files
from lochness.transfer import compress_new_files
from pathlib import Path
import sys
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))
from lochness_create_template import create_lochness_template

import lochness.config as config
import pytest
from time import time
from datetime import timedelta
from datetime import datetime

class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA', 'StudyB']
        self.sources = ['Redcap', 'RPMS']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


@pytest.fixture
def args():
    return Args('test_lochness')


def test_get_updated_files(args):
    print()

    timestamp_a_day_ago = datetime.timestamp(
            datetime.fromtimestamp(time()) - timedelta(days=1))

    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)
    posttime = time()

    file_lists = get_updated_files(Path(args.outdir / 'PHOENIX'),
                                   timestamp_a_day_ago,
                                   posttime)

    assert Path('PHOENIX/GENERAL/StudyA/StudyA_metadata.csv') in file_lists
    assert Path('PHOENIX/GENERAL/StudyB/StudyB_metadata.csv') in file_lists

    shutil.rmtree('tmp_lochness')

    print(file_lists)
    print(file_lists)



def test_compress_list_of_files(args):
    print()

    timestamp_a_day_ago = datetime.timestamp(
            datetime.fromtimestamp(time()) - timedelta(days=1))

    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)
    posttime = time()

    phoenix_root = Path(args.outdir / 'PHOENIX')
    file_lists = get_updated_files(phoenix_root,
                                   timestamp_a_day_ago,
                                   posttime)
    compress_list_of_files(phoenix_root, file_lists, 'prac.tar')

    shutil.rmtree('tmp_lochness')

    # shutil.rmtree('tmp_lochness')
    assert Path('prac.tar').is_file()

    os.popen('tar -xf prac.tar').read()
    print(os.popen('tree').read())
    shutil.rmtree('PHOENIX')
    os.remove('prac.tar')


def test_compress_new_files(args):
    print()
    outdir = 'tmp_lochness'
    args.outdir = outdir
    create_lochness_template(args)

    phoenix_root = Path(args.outdir / 'PHOENIX')

    compress_new_files('nodb', phoenix_root, 'prac.tar')
    shutil.rmtree('tmp_lochness')

    # shutil.rmtree('tmp_lochness')
    assert Path('prac.tar').is_file()
    assert Path('nodb').is_file()

    with open('nodb', 'r') as f:
        print(f.read())

    os.popen('tar -xf prac.tar').read()
    os.remove('nodb')
    os.remove('prac.tar')
    print(os.popen('tree').read())
    shutil.rmtree('PHOENIX')

