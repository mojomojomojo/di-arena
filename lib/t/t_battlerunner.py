#!/usr/bin/env python3


import sys
sys.path.append('..')

from BattleRunner import BattleRunner
from BattleData import BattleDB
from datetime import datetime
import time
import Robocode
import os, os.path
import itertools
import argparse
import random

def name( obj ):
    return obj.Name

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--battles',type=int,default=60)
    cmdline = parser.parse_args()

    workers = cmdline.workers
    num_battles =cmdline.battles

    db_file = 't_battlerunner.sqlite3'
    # always start clean
    if os.path.isfile(db_file):
        os.remove(db_file)
    bdata = BattleDB(db_file)

    di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','arena')))
    robo_dir = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','robocode')))
    robo = Robocode.Robocode(di_arena,robo_dir)

    runner = BattleRunner(bdata,robo,workers)
    runner.start()


    #
    # Import/create the robots
    # 
    robots = [
        'jubjub_robofab.RandomRunner',
        'sample.Crazy',
        'sample.Fire',
        'sample.VelociRobot',
        'sample.Tracker',
        'sample.RamFire',
        'sample.SittingDuck',
        'sample.SpinBot',
        'sample.TrackFire',
        'sample.Walls',
    ]

    for robotName in robots:
        robot = robo.robot( name = robotName )
        bdata.UpdateRobot( name = robot.name,
                           lastUpdated = robot.lastUpdated )

    robots = bdata.GetRobots()
    d_robots = { r.RobotID:r for r in robots }

    all_battles = list(itertools.combinations(bdata.GetRobots(),2))
    battles = [
#        bdata.ScheduleBattle(comps)
#        for comps in all_battles
        bdata.ScheduleBattle(random.choice(all_battles))
        for i in range(num_battles)
    ]
    d_battles = { b.BattleID:b for b in battles }
    print('Battles: {0}'.format(' '.join(['{0}:{1}'.format(b.BattleID,
                                                           '-'.join([str(r.RobotID) for r in b.competitors()]))
                                          for b in d_battles.values()])))

    robo_battles = [ robo.battle(b.BattleID,list(map(name,b.competitors())),bdata.getProperties())
                     for b in battles ]

    
    startTime = datetime.now()
    for battle in robo_battles:
        runner.submit(battle)

    runner.finish()
    print("[TIME] {0} battles ({2} workers) took {1}".format(len(battles),datetime.now()-startTime,workers))

    # Attempt to get better performance numbers.
    for rec in bdata.execute('SELECT MIN(Started) AS begin, MAX(Finished) as end FROM Battles'):
        start = datetime.strptime(rec['begin'],'%Y-%m-%dT%H:%M:%S')
        finish = datetime.strptime(rec['end'],'%Y-%m-%dT%H:%M:%S')
        elapsed = finish-start
        print('[ELAPSED] {battles},{workers},{elapsed},{start},{finish}'.format(
            battles = len(battles),
            workers = workers,
            elapsed = elapsed.total_seconds(),
            start = start,
            finish = finish,
        ))
    
