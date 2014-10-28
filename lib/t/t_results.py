#!/usr/bin/env python3

import Robocode
import os.path


robo = Robocode.Robocode(os.path.realpath(os.path.join(os.path.dirname(__file__),'..')))
print(robo)

result = robo.result('test.result')
print(result)
