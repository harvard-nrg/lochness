import lochness

from pathlib import Path
import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))
from lochness_create_template import create_lochness_template
from test_lochness import show_tree_then_delete, args

import pytest
import shutil
import pandas as pd
import cryptease as crypt
import json
import lochness.config as config
import os


class Args:
    def __init__(self, root_dir):
        self.outdir = root_dir
        self.studies = ['StudyA', 'StudyB']
        self.sources = ['Redcap', 'RPMS']
        self.poll_interval = 10
        self.ssh_user = 'kc244'
        self.ssh_host = 'erisone.partners.org'
        self.email = 'kevincho@bwh.harvard.edu'
        self.lochness_sync_send = True
        self.lochness_sync_receive = False
        self.lochness_sync_history_csv = 'lochness_sync_history.csv'
        self.det_csv = 'prac.csv'
        self.pii_csv = ''


def test_create_lochness_template(args):
    create_lochness_template(args)
    show_tree_then_delete('tmp_lochness')


def test_create_lochness_template_multiple_study(args):
    args.studies = ['StudyA', 'StudyB']
    create_lochness_template(args)
    show_tree_then_delete('tmp_lochness')


def test_create_lochness_template_for_documentation(args):
    args.outdir = 'lochness_root'
    args.studies = ['BWH', 'McLean']
    args.sources = ['redcap', 'xnat', 'box', 'mindlamp']
    args.poll_interval = 43200
    args.det_csv = '/data/data_entry_trigger_db.csv'
    args.pii_csv = '/data/personally_identifiable_process_mappings.csv'

    create_lochness_template(args)
    show_tree_then_delete('lochness_root')





