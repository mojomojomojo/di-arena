#!/usr/bin/env python3

import sys
sys.path.append('..')

import Robocode
import os.path


di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','arena')))
robo_dir = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','robocode')))
robo = Robocode.Robocode(di_arena,robo_dir)
print(robo)

result = robo.result('test.result')
print(result)
