#!/usr/bin/env python

import os
import sys
import time
import lochness
import logging
import importlib
import argparse as ap
import lochness.config as config
import lochness.daemon as daemon
import lochness.hdd as HDD
import lochness.xnat as XNAT
import lochness.beiwe as Beiwe
import lochness.redcap as REDCap
import lochness.dropbox as Dropbox
import lochness.scheduler as scheduler
import lochness.icognition as iCognition
import lochness.onlinescoring as OnlineScoring

SOURCES = {
    'xnat': XNAT,
    'beiwe': Beiwe,
    'redcap': REDCap,
    'dropbox': Dropbox,
    'icognition': iCognition,
    'onlinescoring': OnlineScoring
}

DIR = os.path.dirname(__file__)

logger = logging.getLogger(os.path.basename(__file__))

def main():
    parser = ap.ArgumentParser(description='PHOENIX data syncer')
    parser.add_argument('-c', '--config', required=True,
        help='Configuration file')
    parser.add_argument('-a', '--archive-base',
        help='Base output directory')
    parser.add_argument('--dry', action='store_true',
        help='Dry run')
    parser.add_argument('--skip-inactive', action='store_true',
        help='Skip inactive subjects')
    parser.add_argument('-l', '--log-file',
        help='Log file')
    parser.add_argument('--hdd', nargs='+', default=[],
        help='choose hdds to sync')
    parser.add_argument('--source', nargs='+', choices=SOURCES.keys(),
        default=SOURCES.keys(), help='Sources to sync')
    parser.add_argument('--continuous', action='store_true',
        help='Continuously download data')
    parser.add_argument('--studies', nargs='+', default=[],
        help='Study to sync')
    parser.add_argument('--fork', action='store_true',
        help='Daemonize the process')
    parser.add_argument('--until', type=scheduler.parse,
        help='Pause execution until specified date e.g., 2017-01-01T15:00:00')
    parser.add_argument('--debug', action='store_true',
        help='Enable debug messages')
    args = parser.parse_args()

    # configure logging for this application
    lochness.configure_logging(logger, args)

    # replace args.hdd with corresponding lochness.hdd modules
    if args.hdd:
        args.hdd = [HDDS.get(x) for x in args.hdd]

    # replace args.source with corresponding lochness modules
    if args.source:
        args.source = [SOURCES[x] for x in args.source]

    # load the lochness configuration file and keyring
    Lochness = config.load(args.config, args.archive_base)

    # fork the current process if necessary
    if args.fork:
        logger.info('forking the current process')
        daemon.daemonize(Lochness['pid'], stdout=Lochness['stdout'],
                         stderr=Lochness['stderr'], wdir=os.getcwd())

    # pause execution until
    if args.until:
        logger.info('pausing execution until {0}'.format(args.until))
        scheduler.until(args.until)

    # run downloader once, or continuously
    if args.continuous:
        while True:
            do(args)
            logger.info('sleeping for {0} seconds'.format(Lochness['poll_interval']))
            time.sleep(Lochness['poll_interval'])
    else:
        do(args)

def do(args):
    # reload config every time
    Lochness = config.load(args.config, args.archive_base)
    for subject in lochness.read_phoenix_metadata(Lochness, args.studies):
        if not subject.active and args.skip_inactive:
            logger.info('skipping inactive subject={0}, study={1}'.format(subject.id, subject.study))
            continue
        if args.hdd:
            for Module in args.hdd:
                lochness.attempt(Module.sync, Lochness, subject, dry=args.dry)
        else:
            for Module in args.source:
                lochness.attempt(Module.sync, Lochness, subject, dry=args.dry)

if __name__ == '__main__':
    main()
