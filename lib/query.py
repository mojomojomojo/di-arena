#!/usr/bin/env python3

import argparse
import sqlite3
import sys
import csv
import json

def build_cmdline():
    parser = argparse.ArgumentParser(
        'Run an arbitrary query against a SQLite3 database'
    )

    parser.add_argument(
        'db',
        type=str,
        help='the database to run the query against',
    )

    parser.add_argument(
        '--query', '-q',
        type=str,
        required=True,
        help='the query to execute',
    )

    outtype_group = parser.add_mutually_exclusive_group()
    outtype_group.add_argument(
        '--csv',
        action='store_const',
        const='csv',
    )
    outtype_group.add_argument(
        '--json',
        action='store_const',
        const='json',
    )

    return parser


if __name__ == '__main__':
    cmdline = build_cmdline().parse_args()

    output_type = 'csv'
    if cmdline.csv:
        output_type = cmdline.csv
    elif cmdline.json:
        output_type = cmdline.json

    print('Output Type: {0}'.format(output_type),file=sys.stderr)
    print('DB: {0}\nQuery: {1}\n'.format(cmdline.db,cmdline.query,file=sys.stderr))


    db = sqlite3.connect(cmdline.db)
    db.row_factory = sqlite3.Row

    header = None
    csv_out = None
    count = 0
    if output_type == 'csv':
        csv_out = csv.writer(sys.stdout)
    for record in db.execute(cmdline.query):
        count += 1
        if output_type == 'csv':
            if header is None:
                header = record.keys()
                csv_out.writerow(header)
            csv_out.writerow([record[k] for k in header])
        elif output_type == 'json':
            print(json.dumps({k:record[k] for k in record.keys()}, indent=4, sort_keys=True))
        else:
            raise Exception('Unknown output type {0}'.format(output_type))

    print('\n{0} records returned.'.format(count),file=sys.stderr)
