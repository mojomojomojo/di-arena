#!/usr/bin/env python3

import sys
sys.path.append('..')

from BattleData import BattleDB

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--csv',action='store_true')
parser.add_argument('--json',action='store_true')
parser.add_argument('db',type=str)
cmdline = parser.parse_args()

bdata = BattleDB(cmdline.db)
if cmdline.json:
    bdata.dump(otype='json')
else:
    bdata.dump(otype='csv')
