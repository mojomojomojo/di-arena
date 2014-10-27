#!/usr/bin/env python3

import BattleData

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
    def __init__( self, db_file ):
        self.db_file = db_file
        self.db = BattleDB(self.db_file)

        
