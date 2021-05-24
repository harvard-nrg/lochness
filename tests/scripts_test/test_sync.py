import lochness
from pathlib import Path
import sys


import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from test_lochness import Tokens, KeyringAndEncrypt, args, SyncArgs
from test_lochness import show_tree_then_delete, config_load_test

from lochness_create_template import create_lochness_template


import pytest
import lochness.config as config
from sync import do

from lochness_test.transfer.test_transfer import KeyringAndEncryptLochnessTransfer



def test_do_init(args):
    syncArgs = SyncArgs()
    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    _ = KeyringAndEncrypt(args.outdir)
    Lochness = config_load_test(syncArgs.config, syncArgs.archive_base)


def test_do_with_lochness_sync_receive(args):
    syncArgs = SyncArgs()
    syncArgs.lochness_sync_receive = True
    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    syncArgs.sources = args.sources
    _ = KeyringAndEncryptLochnessTransfer(args.outdir)

    do(syncArgs)


def test_read_phoenix_data():
    args = SyncArgs()
    args.source = ['xnat', 'box']
    args.studies = ['mclean']
    args.dry = [False]
    Lochness = config.load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject)
        # sync(Lochness, subject, Lochness.dry)
