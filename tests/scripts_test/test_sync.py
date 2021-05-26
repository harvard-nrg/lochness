import lochness
from pathlib import Path


import sys
lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))

from test_lochness import Tokens, KeyringAndEncrypt, args, SyncArgs
from test_lochness import show_tree_then_delete, config_load_test
from lochness_test.transfer.test_transfer import KeyringAndEncryptLochnessTransfer

from lochness_create_template import create_lochness_template

import pytest
import lochness.config as config
from sync import do


@pytest.fixture
def syncArgsForLochnessSync(args):
    syncArgs = SyncArgs('tmp_lochness')
    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    syncArgs.sources = args.sources
    _ = KeyringAndEncryptLochnessTransfer(args.outdir)

    return syncArgs


def test_do_init(args):
    syncArgs = SyncArgs('tmp_lochness')
    create_lochness_template(args)
    syncArgs.config = args.outdir / 'config.yml'
    _ = KeyringAndEncrypt(args.outdir)
    Lochness = config_load_test(syncArgs.config, syncArgs.archive_base)
    show_tree_then_delete('tmp_lochness')


def test_do_with_lochness_sync_send(syncArgsForLochnessSync):
    syncArgsForLochnessSync.lochness_sync_send = True
    do(syncArgsForLochnessSync)
    show_tree_then_delete('tmp_lochness')


def test_do_with_lochness_sync_receive(syncArgsForLochnessSync):
    syncArgsForLochnessSync.lochness_sync_receive = True
    do(syncArgsForLochnessSync)
    show_tree_then_delete('tmp_lochness')


def test_do_REDCap(syncArgsForLochnessSync):
    syncArgsForLochnessSync.update_source(['redcap'])
    do(syncArgsForLochnessSync)
    show_tree_then_delete('tmp_lochness')


def test_read_phoenix_data(args):
    syncArgs = SyncArgs('tmp_lochness')
    create_lochness_template(args)
    _ = KeyringAndEncrypt(args.outdir)
    args.source = ['xnat', 'box']
    args.studies = ['mclean']
    args.dry = [False]
    Lochness = config.load(syncArgs.config, syncArgs.archive_base)

    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        print(subject)
        # sync(Lochness, subject, Lochness.dry)

