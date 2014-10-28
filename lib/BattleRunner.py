#!/usr/bin/env python3

import multiprocessing
from queue import Empty
import subprocess
import Robocode
import os, os.path
from datetime import datetime
import sys
import time

# This class knows about Robocode and the Database.

def recommendedWorkers():
    cpus = multiprocessing.cpu_count()
    if cpus > 12:
        return cpus-2
    elif cpus > 6:
        return cpus-1
    else:
        return cpus

def BattleWorker( robocode, battledb, job_q, result_q ):
    print('[{who}] Started:\n  {db}\n  {robo}'.format(
        who = multiprocessing.current_process().name,
        db = battledb,
        robo = robocode
        ), file=sys.stderr)

    try:
        while True:
            battle = job_q.get()

            if battle.__class__ != Robocode.Battle:
                # sentinel: no more jobs
                print('[{0}] EndOfWork!'.format(
                    multiprocessing.current_process().name,
                ), file=sys.stderr)
                break

            start_time = datetime.now()
            try:
                battledb.MarkBattleRunning(battle.id)

                print('[{who}] Running battle {id} between: {comps}'.format(
                    who = multiprocessing.current_process().name,
                    id = battle.id,
                    comps = ' '.join(battle.competitors),
                ), file=sys.stderr)
                battle.run()
                print('[{who}] Finished: {id}'.format(
                    who = multiprocessing.current_process().name,
                    id = battle.id,
                ), file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print('[{who}] Battle invocation fails: {exc}\n{output}'.format(
                    who = multiprocessing.current_process().name,
                    exc = e.cmd,
                    output = e.output,
                ), file=sys.stderr)

            battledb.BattleCompleted(battle.id,
                                     battle.dbData(),
                                     battle.result.dbData())

            elapsed = datetime.now() - start_time

            result_q.put(battle.id)
    except Exception as e:
        print('[{who}] Exception: {exc}'.format(
            who = multiprocessing.current_process().name,
            exc = e,
        ), file=sys.stderr)
        raise e

    print('[{0}] Finished!'.format(
        multiprocessing.current_process().name,
    ), file=sys.stderr)



class BattleRunner:
    def __init__( self, battledb, robocode, maxWorkers=None ):
        self.battledb = battledb
        self.robocode = robocode
        self.job_q = multiprocessing.JoinableQueue()
        self.result_q = multiprocessing.JoinableQueue()
        self.workers = maxWorkers if maxWorkers is not None else recommendedWorkers()
        self.job_count = 0


    def start( self ):
        # Start the workers.
        self.pool = [ multiprocessing.Process( target = BattleWorker,
                                               args=(self.robocode, self.battledb, 
                                                     self.job_q, self.result_q) )
                      for i in range(self.workers) ]
        for p in self.pool:
            p.start()


    def finish( self ):
        print('[{0}] Sending EndOfWork signals'.format(
            multiprocessing.current_process().name,
        ), file=sys.stderr)

        for p in self.pool:
            self.job_q.put(0)

        # Consume everything in the result_q
        while self.job_count > 0:
            battleid = self.result_q.get()
            self.job_count -= 1

        for p in self.pool:
            p.join()


    def submit( self, battle ):
        print('[{0}] Submitting battle #{1} '.format(
            multiprocessing.current_process().name,
            battle.id,
        ), file=sys.stderr)
        self.job_q.put(battle)
        self.job_count += 1

    def running(self):
        '''
        check to see if any of the workers are still running
        '''
        for p in self.pool:
            if p.is_alive():
                return True
        return False

    def getResults(self):
        '''
        check to see if there are any results
        '''

        results = []
        try:
            results.append(self.result_q.get_nowait())
        except Empty:
            pass

        return results
