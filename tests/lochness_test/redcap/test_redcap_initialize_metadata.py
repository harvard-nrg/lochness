import lochness
import sys
from pathlib import Path
scripts_dir = Path(lochness.__path__[0]).parent / 'scripts'
sys.path.append(str(scripts_dir))

import lochness.config as config
import lochness.tree as tree
import lochness_create_template
from lochness_create_template import create_lochness_template
import pytest, shutil, os, sys, zipfile
import tempfile as tf
from subprocess import Popen
import time
import pandas as pd
import json

from lochness.redcap import post_to_redcap

scripts_dir = Path(lochness.__path__[0]).parent / 'tests'
sys.path.append(str(scripts_dir))
from mock_args import mock_load

from lochness.redcap import initialize_metadata

import lochness.redcap as REDCap

class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA']
        self.sources = ['Redcap', 'RPMS']
        self.input_sources = ['redcap']
        self.dry = False
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


@pytest.fixture
def args():
    return Args('test_lochness')


def test_create_lochness_template(args):
    # create_lochness_template(args)
    dry=False
    study_name = 'StudyA'
    Lochness = config.load('test_lochness/config.yml', '')
    initialize_metadata(Lochness, study_name, 'record_id1', 'Consent')

    # run redcap pull first to update metadata.csv
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        if not subject.active and args.skip_inactive:
            continue
        else:
            if 'redcap' in args.input_sources:
                lochness.attempt(REDCap.sync, Lochness, subject, dry=args.dry)
