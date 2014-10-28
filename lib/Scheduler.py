#!/usr/bin/env python3

import BattleData

import itertools


# Strategy:
#   1. Get a list of all robots.
#   2. For each entry in the job queue:
#      A. Decide which battles are the most important.
#         Score the robots
#          - number of scheduled battles
#          - not currently playing
#          - fewest non-obsolete battles
#      B. Choose a robot needing battles
#      C. Choose an opponent.
#      D. Schedule the battle.

class Scheduler:
    def __init__( self, db_file, runner, **propertyOverrides ):
        self.db_file = db_file
        self.runner = runner
        self.battledb = BattleData.BattleDB(self.db_file)

    def necessaryBattles( self ):
        alreadyCompleted = self.battledb.GetFinishedBattles(nonObsolete=True)
        for comps in self.allBattles():
            self.battledb.GetBattleBetween(comps)
        
        return filter(lambda b: b.BattleID not in alreadyCompleted, self.allBattles())

    def allBattles( self ):
        return itertools.combinations(self.battledb.GetRobots(),2)

    def ScheduleBattle( comps ):
        return self.battledb.ScheduleBattle(comps) # property overrides
        
    
