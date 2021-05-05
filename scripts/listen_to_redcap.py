#!/usr/bin/env python

from lochness.redcap import data_trigger_capture
import sys
import argparse


def parse_args(args):
    '''Parse inputs coming from the terminal'''
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Make record of REDCap data entry trigger POST signals',
        epilog="DPACC")

    # you need freewater directory
    argparser.add_argument(
            "--database_csv", "-dbc",
            type=str,
            required=True,
            help='CSV path to store REDCap data entry trigger records')

    argparser.add_argument(
            "--port", "-p",
            type=int,
            required=True,
            default=8080,
            help='port number to listen')
    
    return argparser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    data_trigger_capture.run(args.database_csv,
                             port=args.port)
