#!/usr/bin/env python3

'''
Monitor the robots directory and keep track of updated robots.
Each robot is "described" by a text file name <name>.robot, which contains
  a list of binary dependencies. If any of these are updated, the robot
  is re-entered in the tournament.
'''

from BattleData import BattleDB
import re
import os
import os.path
import time
from datetime import datetime

class _RobotDescr:
    def __init__( self, robotFile ):
        self.rfile = robotFile
        self.name = os.path.basename(os.path.splitext(self.rfile)[0])
        rdir = os.path.dirname(self.rfile)
        with open(robotFile) as robotIn:
            self.deps = [ os.path.join(rdir,dep.strip()) for dep in robotIn ]
        self.lastUpdated = max([ os.stat(dep).st_mtime for dep in self.deps ])

    def __str__(self):
        return '[{cls} File({rfile}) Name({name}) lastUpdated({updated})]\n  {deps}'.format(
            cls = self.__class__,
            rfile = self.rfile,
            name = self.name,
            updated = datetime.fromtimestamp(self.lastUpdated),
            deps = '\n  '.join([os.path.basename(dep) for dep in self.deps ]),
            )

class CompetitorMonitor:
    def __init__( self, robotDB ):
        self.db_file = robotDB

    def monitor( self, robotPath ):
        self.db = BattleDB(self.db_file)
        self.path = robotPath

        descr = re.compile(r'\.robot$',re.I)

        while True:
            for robot in [ _RobotDescr(os.path.join(self.path,rfile))
                           for rfile in filter(descr.search,os.listdir(self.path))]:
                print(robot)

            time.sleep(10)

