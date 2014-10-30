#!/usr/bin/env python3

import sys
sys.path.append('..')

import sqlite3
from cpuinfo import cpuinfo # py-cpuinfo
import socket
import argparse
import os,os.path,sys
import itertools,random,re
from datetime import datetime

from BattleData import BattleDB
import Robocode
from BattleRunner import BattleRunner

def build_cmdline():
    parser = argparse.ArgumentParser(
        'performance profiling of multiprocessing battles')

    parser.add_argument(
        '--db',
        type=str,
        default='performance.results.sqlite3',
        help='the database in which to record all information',
    )
    parser.add_argument(
        '--output-directory', '-o',
        type=str,
        default='perf_output',
        help='the directory where output files should be stored',
    )
    parser.add_argument(
        '--runs', '-r',
        type=int,
        default=30,
        help='the number of desired runs for each combination',
    )
    parser.add_argument(
        '--max','-m',
        type=int,
        default=10,
        help='the maximum multiplier of the number of # workers to calculate the # battles',
    )

    return parser

class PerfDB:
    def __init__(self, db_file, desired_runs, max_multiplier=10):
        self.db_file = db_file
        self.desired_runs = desired_runs
        self.mmax = max_multiplier

        self.initDB()


    def initDB(self):
        self.conn = sqlite3.connect(self.db_file,
                                    # autocommit
                                    isolation_level = None)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS Runs (
               RunID             INTEGER   PRIMARY KEY,
               CPUInfo           TEXT,
               CPUCount          INTEGER,
               Hostname          TEXT,
               Workers           INTEGER,
               BattleMultiplier  INTEGER,
               RunStarted        TEXT,
               RunFinished       TEXT,
               DBFile            TEXT
            );
            ''')


    def nextRun( self ):
        '''
        Decide which run should take place next.

        Return a (#workers,#battles,run #) tuple.
        '''
        # See which combinations have the fewest runs.
        #   If there are some, choose one of those at random.
        # Otherwise, choose a possible combination at random.
        
        this_cpu = cpuinfo.get_cpu_info()['brand']
        max_cpu = int(cpuinfo.get_cpu_info()['count'] * 1.5)
        comb = tuple(itertools.product(range(1,max_cpu+1),
                                       range(1,self.mmax+1)))
        already_run = { '{0:04d}_{1:04d}'.format(w,m):0 for w,m in comb }
        #print(str(already_run))
        for record in self.conn.execute('''
            SELECT Workers,BattleMultiplier,COUNT(RunID)
            FROM Runs
            WHERE CPUInfo=?
            GROUP BY Workers,BattleMultiplier
        ''',[this_cpu]):
            #print('{0}'.format({ k:record[k] for k in record.keys()}))
            already_run['{0:04d}_{1:04d}'.format(
                record['Workers'],record['BattleMultiplier'])] = \
                record['COUNT(RunID)']

        #print(str(already_run))
        fewest_runs = min(already_run.values())

        if fewest_runs == self.desired_runs:
            raise StopIteration()

        need_run = tuple(filter(lambda k: already_run[k] == fewest_runs, already_run.keys()))
        # Choose a random scenario with fewer runs.
        if len(need_run) > 0:
            c = random.choice(need_run)
            return tuple(map(int,re.split(r'_',c))) + (fewest_runs+1,)

        # Otherwise, choose a random run.
#        c = random.choose(already_run.keys())
#        return tuple(map(int,re.split(r'_',c))) + (fewest_runs+1,)


    def commitRun( self, run_data ):
        '''
        Save the run data into the database.
        '''

        cpu_info = cpuinfo.get_cpu_info()

        result = self.conn.execute('''
            INSERT INTO Runs
              (CPUInfo,CPUCount,Hostname,Workers,BattleMultiplier,
               RunStarted,RunFinished,DBFile)
            VALUES
              (?,?,?,?,?,?,?,?)
        ''',[ cpu_info['brand'], cpu_info['count'], socket.gethostname(),
              run_data['Workers'], run_data['BattleMultiplier'],
              run_data['RunStarted'], run_data['RunFinished'],
              run_data['DBFile'],              
          ])


def runScenario( num_workers, battle_mult, scen_db_file, perf_db ):
    num_battles = num_workers * battle_mult
    print('[SCENARIO] workers({workers}) battles({battles}) {db}'.format(
        workers = num_workers,
        battles = num_battles,
        db = scen_db_file,
    ))


    # This file is a scratch file. Delete it if it exists.
    if os.path.isdir(scen_db_file):
        os.remove(scen_db_file)

    battledb = BattleDB(scen_db_file)

    di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','arena')))
    robo_dir = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','robocode')))
    robo = Robocode.Robocode(di_arena,robo_dir)

    runner = BattleRunner(battledb,robo,num_workers)
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
        battledb.UpdateRobot( name = robot.name,
                           lastUpdated = robot.lastUpdated )

    robots = battledb.GetRobots()

    all_battles = list(itertools.combinations(battledb.GetRobots(),2))
    # BattleData.Battle
    battles = [
        battledb.ScheduleBattle(random.choice(all_battles))
        for i in range(num_battles)
    ]
    # Robocode.Battle
    robo_battles = [ robo.battle(b.BattleID,
                                 list(map(lambda c:c.Name,b.competitors())),
                                 battledb.getProperties())
                     for b in battles ]

    
    # Run the battles.
    for battle in robo_battles:
        runner.submit(battle)
    runner.finish()


    # Record the run data.
    for rec in battledb.execute('SELECT MIN(Started) AS begin, MAX(Finished) as end FROM Battles'):
        start = datetime.strptime(rec['begin'],'%Y-%m-%dT%H:%M:%S')
        finish = datetime.strptime(rec['end'],'%Y-%m-%dT%H:%M:%S')
        elapsed = finish-start

        perf_db.commitRun({
            'Workers'              : num_workers,
            'BattleMultiplier'     : battle_mult,
            'RunStarted'           : rec['begin'],
            'RunFinished'          : rec['end'],
            'DBFile'               : scen_db_file,
        })
        print('[ELAPSED] {battles},{workers},{elapsed},{start},{finish}'.format(
            battles = len(battles),
            workers = workers,
            elapsed = elapsed.total_seconds(),
            start = start,
            finish = finish,
        ))
    


if __name__ == '__main__':
    cmdline = build_cmdline().parse_args()

    db = PerfDB(cmdline.db, cmdline.runs, cmdline.max)
    print("Performance Test ({0})\nDesired Runs: {1}\nMax Multiplier: {2}".format(cmdline.db,cmdline.runs,cmdline.max))

    if not os.path.isdir(cmdline.output_directory):
        os.makedirs(cmdline.output_directory)

    while True:
        try:
            workers,battle_mult,runIndex = db.nextRun()
            outdb = os.path.join(cmdline.output_directory,
                                 'w{workers:04d}_m{mult:04d}_i{index:03d}.{hostname}.sqlite3'.format(
                                     workers = workers,
                                     mult = battle_mult,
                                     index   = runIndex,
                                     hostname = socket.gethostname()))
            runScenario(workers,battle_mult,outdb,db)
            
        except StopIteration:
            # finished with all necessary scenarios.
            print("Finished with all desired runs.")
            break
