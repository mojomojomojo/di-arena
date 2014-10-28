#!/usr/bin/env python3

from BattleData import BattleDB
from datetime import datetime
import Robocode
import random
import os
import os.path

db_file = 't_battle_db.sqlite3'
# always start clean
if os.path.isfile(db_file):
    os.remove(db_file)
bdata = BattleDB(db_file)

for i in range(10):
    id = random.randint(0,59)
    name = 'nonex.TestRobot.{0:02d}'.format(id)
    bdata.UpdateRobot(
        lastUpdated = '2014-10-20T09:30:{0:02d}'.format(id),
        name = name,
    )

robots = bdata.GetRobots()

# schedule a few battles
battleCount = 5
for i in range(battleCount):
    comps = random.sample(robots,2)
    print('\n'.join(list(map(str,comps))))

    battle = bdata.ScheduleBattle(comps)
    print(battle)


# get all battles
print('\n\n\n[TEST] GetBattles()...')
all_battles = bdata.GetBattles()
assert len(all_battles) == battleCount, \
    'GetBattles() returns incorrect number of battles: {0}!={1}\n{2}'.format(
        len(all_battles), all_battles,
        '\n'.join(list(map(str,all_battles))))
print('[TEST] Get all battles: OK')


# mark one as running
run_battle = random.choice(all_battles)
bdata.MarkBattleRunning(run_battle)
print("[RUNNING] {0}".format(run_battle))

running_battles = bdata.GetRunningBattles()
assert len(running_battles) == 1, \
    'GetBattles(State=\'running\') returns incorrect number of battles: {0}!={1}\n{2}'.format(
        len(running_battles), running_battles,
        '\n'.join(list(map(str,running_battles))))
    

        

print('\n\n\n[TEST_RESULTS] OK')
