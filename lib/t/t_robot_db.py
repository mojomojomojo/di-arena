#!/usr/bin/env python3

from BattleData import BattleDB
from datetime import datetime

bdata = BattleDB('t_robot_db.sqlite3')

for i_id in range(3,10):
    stamp = datetime(2014,10,7,9,0,0)
    name = 'nonex.TestRobot' + str(i_id)

    try:
        i_robot = bdata.GetRobot(name=name)
        # robot exists
        print('Robot {0} exists: {1}'.format(name,i_robot))
    except:
        print('New Robot')
        i_robot = bdata.UpdateRobot(
            lastUpdated = stamp.strftime('%Y-%m-%dT%H:%M:%S'),
            name = name,
        )
    print(i_robot)

    print("updating robot")
    stamp = datetime.now()
    i_robot = bdata.UpdateRobot(
        lastUpdated = stamp.strftime('%Y-%m-%dT%H:%M:%S'),
        id = i_robot.RobotID,
    )
    print(i_robot)

print('\nAll Robots:\n  {0}'.format('\n  '.join(list(map(str,bdata.GetRobots())))))
