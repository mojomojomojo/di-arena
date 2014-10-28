#!/usr/bin/env python3

'''
Attempt to schedule a number of battles, mark some as running, and
complete others. The goal is to leave the database in a state to test
some of the more complicated queries.
'''


import sys
sys.path.append('..')

from Scheduler import Scheduler
from BattleData import BattleDB
import Robocode
import random
import argparse
import os
import os.path

def build_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=random.randint(0,1<<63-1))
    parser.add_argument('--db',type=str,default='t_sched_db.sqlite3')
    return parser

def init_robots( battledb, robocode ):
    robots = [
        'jubjub_robofab.RandomRunner',
        'sample.Crazy',
        'sample.Fire',
        'sample.VelociRobot',
        'sample.Tracker',
    ]
    for robotName in robots:
        robot = robo.robot( name = robotName )
        battledb.UpdateRobot( name = robot.name,
                              lastUpdated = robot.lastUpdated )

    robots = battledb.GetRobots()
    return robots, { r.RobotID:r for r in robots }

def main_objects( db_file ):
    # typical
    battledb = BattleDB(db_file)
    scheduler = Scheduler(db_file,None)
    di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..')))
    robocode = Robocode.Robocode(os.path.join(di_arena,'robocode'),
                                 robots = os.path.join(di_arena,'robots'),
                                 battles = os.path.join(di_arena,'battles'),
                                 results = os.path.join(di_arena,'results'),
                                 recordings = os.path.join(di_arena,'recordings'),
                             )

    return robocode,battledb,scheduler

def battleid( battle ):
    return battle.BattleID

def comp_ids( comps ):
    return [ c.RobotID for c in comps ]

def abbrBattles( sched_battles ):
    '''
    sched_battles is a sequence of (<Robot>,<Robot>)
    '''
    return [ '{0}-{1}'.format(min(a,b),max(a,b)) for a,b in sorted(list(map(comp_ids,sched_battles))) ]

if __name__ == '__main__':
    cmdline = build_cmdline().parse_args()

    print("[RANDOM_SEED] {0}".format(cmdline.seed))
    random.seed(cmdline.seed)
    print("[DATABASE] {0}".format(cmdline.db))
    if os.path.isfile(cmdline.db):
        os.remove(cmdline.db)

    robo,bdata,sched = main_objects(cmdline.db)


    robots, d_robots = init_robots(bdata,robo)

    all_battles = list(sched.allBattles())
    assert len(all_battles) == 10, 'Incorrect number of battles: {0}'.format(len(all_battles))
    print(str(abbrBattles(all_battles)))

    necessary = list(sched.necessaryBattles())
    assert len(all_battles) == len(necessary), \
        'Mismatch: all battles should be necessary\n  All: {all}\n  Necessary: {necc}'.format(
            all = abbrBattles(all_battles),
            necc = abbrBattles(necessary),
        )
    

        
    # Run some random ones.
    num_torun = 3
    to_run = random.sample(all_battles,num_torun)
    for comps in to_run:
        pass
