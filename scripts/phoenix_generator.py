#!/usr/bin/env python

import os
import re
import sys
import csv
import logging
import argparse as ap

logger = logging.getLogger(__name__)

def main(args):
    configure_logging(args.verbose)

    # secure the resulting directory structure
    os.umask(0o077)

    # make sure study name contains only word characters
    if not re.match('^\w+$', args.study):
        logger.critical('study name can only contain word characters')
        sys.exit(1)

    general = os.path.join(args.dir, 'GENERAL', args.study)
    protected = os.path.join(args.dir, 'PROTECTED', args.study)
    metadata = os.path.join(general, '{0}_metadata.csv'.format(args.study))

    # check if folder or metadata file already exists
    for f in [general, protected, metadata]:
        if os.path.exists(f):
            logger.critical('file already exists %s', f)
            sys.exit(1)

    print('\tcreate: {0}'.format(general))
    os.makedirs(general)
    print('\tcreate: {0}'.format(protected))
    os.makedirs(protected)
    create_example_meta_file(metadata)


def create_example_meta_file(metadata: str) -> None:
    # example metadata file row
    example = [
        ['Active', 'Consent', 'Subject ID', 'Beiwe'],
        ['1', '1979-01-01', 'EXAMPLE', 'beiwe:5432:abcde']
    ]

    # write metadata file
    print('\tcreate: {0}'.format(metadata))
    with open(metadata, 'w') as fo:
        writer = csv.writer(fo)
        writer.writerows(example)

def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument('-s', '--study', required=True,
        help='Study name')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Verbose logging')
    parser.add_argument('dir', type=os.path.expanduser,
        help='PHOENIX directory')
    return parser.parse_args()

def configure_logging(verbose):
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    logging.basicConfig(level=level)
 
if __name__ == '__main__':
    # arguments and logging
    args = parse_args()
    main(args)
