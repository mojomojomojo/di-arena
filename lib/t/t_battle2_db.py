#!/usr/bin/env python3

import sys
sys.path.append('..')

from BattleData import BattleDB
from datetime import datetime
import Robocode
import random
import os
import os.path

db_file = 't_battle2_db.sqlite3'
# always start clean
if os.path.isfile(db_file):
    os.remove(db_file)
bdata = BattleDB(db_file)

robo = Robocode.Robocode(os.path.realpath(os.path.join(os.path.dirname(__file__),'..')))
print(robo)

robots = [
    'jubjub_robofab.RandomRunner',
    'sample.Crazy',
    'sample.Fire',
]

for robotName in robots:
    robot = robo.robot( name = robotName )
    bdata.UpdateRobot( name = robot.name,
                       lastUpdated = robot.lastUpdated )

robots = bdata.GetRobots()
comps = random.sample(robots,2)
battle = bdata.ScheduleBattle(comps)
print('DB Object:\n{0}\n'.format(battle))

r_battle = robo.battle(battle.BattleID,
                       [c.Name for c in comps],
                       battle.getProperties())
print('Robocode Object:\n{0}\n'.format(r_battle))

print("\nPreparing to run battle...")
bdata.MarkBattleRunning(battle)
print(bdata.GetBattle(battle))

print("\nRunning battle...")
try:
    r_battle.run()
except Exception as e:
    print(e.cmd)
    print(e.output)

print("finished")
print(r_battle)
print(r_battle.result)


print('\nbattleDBData:\n  {0}'.format('\n  '.join([ '{0}: {1}'.format(k,v)
                                                    for k,v in r_battle.dbData().items() ])))
print('\nresultDBData:\n  {0}'.format('\n  '.join([ '{0}: {1}'.format(k,v)
                                                    for k,v in r_battle.result.dbData().items() ])))

print("\nCompleting battle...")
bdata.BattleCompleted(battle,
                      r_battle.dbData(),
                      r_battle.result.dbData())
print(bdata.GetBattle(battle))


