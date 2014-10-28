#!/usr/bin/env python3

'''
This is an interface into Robocode and its data.
It knows nothing about any other classes.
'''

import os
import os.path
import csv
import json
import re
import sys
from datetime import datetime
import subprocess

class Robocode:
    def __init__( self, robocode_dir, arena_dir,
                  robots = 'robots',
                  battles = 'battles',
                  results = 'results',
                  recordings = 'recordings',
                  lib = 'libs',
              ):
        self.robocode_dir = robocode_dir
        self.arena_dir = arena_dir
        for prop,def_dir,param in (
                ('robots',     self.robocode_dir, robots),
                ('battles',    self.arena_dir,    battles),
                ('results',    self.arena_dir,    results),
                ('recordings', self.arena_dir,    recordings)):
            if os.path.isdir(param):
                setattr(self,prop,param)
            else:
                setattr(self,prop,os.path.join(def_dir,param))

        self.lib = os.path.join(self.robocode_dir,lib)

    def __str__(self):
        return '[Robocode dir({robo_dir}) {nonstd}]'.format(
            robo_dir = self.robocode_dir,
            nonstd = ' '.join(
                [ '{0}({1})'.format(d,getattr(self,d))
                  for d in
                    filter(lambda d:os.path.abspath(getattr(self,d)) !=
                                    os.path.abspath(os.path.join(self.robocode_dir,d)),
                           ('robots','battles','results','recordings','lib'))
              ]),
        )

    def result( self, result_base ):
        '''
        Read the contents of a results file.
        '''
        if os.path.isfile(result_base):
            return Robocode.Result(result_base)
        # Otherwise, assume it's in the system dir.
        return Robocode.Result(os.path.join(self.results,result_base))

    def robot( self, name=None, descriptor=None ):
        '''
        Search the robot directory for the given robot.
        '''
        if name is not None:
            return Robocode.Robot(name,self.robots)
        elif descriptor is not None:
            # path to a descriptor file
            namePart = os.path.splitext(os.path.relpath(descriptor,self.robots))[0]
            return Robocode.Robot('.'.join(namePart.split(os.sep)),self.robots)
            
    def battle( self, id, competitors, properties ):
        return Robocode.Battle(self,id,competitors,properties)

    #
    # Robocode subclasses
    #

    class RobotDescr:
        def __init__( self, robotFile ):
            self.rfile = robotFile
            self.name = os.path.basename(os.path.splitext(self.rfile)[0])
            rdir = os.path.dirname(self.rfile)
            with open(robotFile) as robotIn:
                self.deps = [ dep.strip() for dep in robotIn ]
                self.deps = [ os.path.join(rdir,dep)
                              for dep in self.deps if dep ]
            self.lastUpdated = \
                datetime.fromtimestamp(max([ os.stat(dep).st_mtime
                                             for dep in self.deps ]))

        def __str__(self):
            return '[{cls} File({rfile}) Name({name}) lastUpdated({updated})]\n  {deps}'.format(
                cls = self.__class__.__name__,
                rfile = self.rfile,
                name = self.name,
                updated = datetime.fromtimestamp(self.lastUpdated),
                deps = '\n  '.join([os.path.basename(dep) for dep in self.deps ]),
                )


    class Robot:
        def __init__(self,robotBase,robotRoot):
            '''
            robotBase is just a "name" (no extension, no dirs)
            '''
            pieces = robotBase.split('.') # dirs in Java naming

            # look for .jar (not recursively)
            jar = os.path.join(robotRoot,robotBase+'.jar')
            jclass = os.path.join(robotRoot,*pieces)+'.class'
            if os.path.isfile(jar):
                self.path = jar
                ext = '.jar'
            elif os.path.isfile(jclass):
                self.path = jclass
                ext = '.class'
            else:
                raise FileNotFoundError(robotBase)
                
            self.name = robotBase
            self.descriptor = Robocode.RobotDescr(os.path.splitext(self.path)[0] + '.robot')
            # robocode.repository/src/main/java/net/sf/robocode/repository
            if ( ext == '.class' and
                 not ( pieces[0] == 'tested' or pieces[0] == 'sample' ) ):
                self.development = True
            else:
                self.development = False

            self.lastUpdated = self.descriptor.lastUpdated

        def battleName( self ):
            return '{0}{1}'.format(
                self.name,
                '*' if self.development else '',
            )

        def __str__(self):
            return '[Robocode.Robot name({name}) develP({devel}) updated({updated}) path({path})]\n  {deps}'.format(
                name = self.name,
                devel = self.development,
                updated = datetime.fromtimestamp(self.lastUpdated).strftime('%Y-%m-%dT%H:%M:%S'),
                path = self.path,
                deps = '\n  '.join(self.descriptor.deps),
            )

    class Result:
        _score = re.compile(r'^\s*(\d+)\s*\(\d+%\)\s*$')
        _place = re.compile(r'^(\d+)(?:st|nd|rd|th): .*$')
        _name = re.compile(r'^[^:]+: (.*)\*?$')
        _rounds = re.compile(r'Results for (\d+) rounds',re.I)

        def __init__( self, in_file ):
            self.robots = []
            self.winner = ''
            self.rounds = 0

            with open(in_file,'rt') as in_tab_file:
                meta_head = in_tab_file.readline()
                self.rounds = int(re.sub(Robocode.Result._rounds,r'\1',meta_head))
                header = re.split(r'\s*\t\s*',in_tab_file.readline())
                
                in_tab = csv.DictReader( in_tab_file,
                                         fieldnames = header,
                                         delimiter = '\t' )
                for row in in_tab:
                    data = { k:row[k] for k in row.keys() }
                    del(data['']) # strip the empty column
                    data['_Score'] = re.sub(Robocode.Result._score,r'\1',data['Total Score'])
                    data['_Place'] = int(re.sub(Robocode.Result._place,r'\1',data['Robot Name']))
                    # remove the 'devel' marker, if it exists
                    data['_Name'] = re.sub(Robocode.Result._name,r'\1',data['Robot Name']).rstrip('*')
                    if data['_Place'] == 1:
                        # remove the 'devel' marker, if it exists
                        self.winner = data['_Name'].rstrip('*')

                    self.robots.append(data)

        def __str__(self):
            return '[Result rounds({rounds}) winner({winner})]\n  {robots}'.format(
                rounds = self.rounds,
                winner = self.winner,
                robots = '\n  '.join(list(map(str,self.robots))),
            )

        def dbData(self):
            '''
            an interface between this object and the database
            
            Each DB field is a key in the returned dict.
            '''

            # This is highly dependent on the DB schema.
            #    BattleID INTEGER,
            #    RobotID INTEGER,
            #    RobotUpdated TEXT,
            #    Score INTEGER,
            #    Results TEXT,
            #    PRIMARY KEY(BattleID,RobotID)
            return {
                r_data['_Name']: {
                    'Score'    : r_data['_Score'],
                    'Results'  : json.dumps(r_data, sort_keys=True),
                }
                for r_data in self.robots
            }




    class Battle:
        robotProp = 'robocode.battle.selectedRobots'
        notOther = ( 'id', 'properties', 'competitors' )

        def __init__( self, robocode, id, competitors, properties, **kwargs ):
            self.robocode = robocode # parent object (class Robocode)
            self.id = id
            self.competitors = competitors # robot names
            self.properties = properties
            self.battleFile = None

            # allow overriding 

        def __str__( self ):
            return '[{cls} BattleID({id})]\n Properties:\n  {props}\n Competitors:\n  {comps}\n Other:\n  {other}'.format(
                cls = self.__class__.__name__,
                id = self.id,
                comps = '\n  '.join(self.competitors),
                props = '\n  '.join([ '{0}={1}'.format(k,v)
                                      for k,v in self.properties.items() ]),
                other = '\n  '.join(
                    [ '{0}: {1}'.format(attr,getattr(self,attr))
                      for attr in filter(lambda p: p not in Robocode.Battle.notOther,
                                         vars(self)) ])
            )

        def run( self ):
            '''
            Run the battle.
            '''

            self.createBattleFile()
            self.resultFile = os.path.join(self.robocode.results,
                                           '{0}.result'.format(self.id))
            self.recordFile = os.path.join(self.robocode.results,
                                           '{0}.br'.format(self.id))

            command = [
                'java',
                '-Xmx512M', # memory
                # This probably had better not have spaces in it.
                '-DROBOTPATH={0}'.format(self.robocode.robots),
                #'-DPARALLEL=true', # attempt parallelism
                '-cp', os.path.join(self.robocode.lib,'robocode.jar'),
                'robocode.Robocode',
                '-cwd', self.robocode.robocode_dir,
                '-battle', self.battleFile,
                '-results', self.resultFile,
                '-record', self.recordFile,
                '-nodisplay',
                '-nosound',
            ]
            try:
                self.started = datetime.now()
                self.output = subprocess.check_output(
                    command,
                    stderr = subprocess.STDOUT,
                )
                self.finished = datetime.now()
                self.runTime = self.finished-self.started
                matches = re.search(r"Can't find '([^']+)\*?'",
                                    self.output.decode('ascii'),re.I)
                if matches:
                    print("Missing Robot: {0}".format(matches.group(1)),
                                                      file=sys.stderr)
                    raise subprocess.CalledProcessError(
                        0,
                        cmd=command,
                        output=self.output)

                self.error = False

                self.result = self.robocode.result(self.resultFile)

            except subprocess.CalledProcessError as e:
                self.finished = datetime.now()
                self.runTime = self.finished-self.started
                self.error = True
                print('Battle returns error:\n{0}'.format(e.output.decode('ascii')))
                raise e
                

        def createBattleFile( self ):
            self.battleFile = os.path.join(self.robocode.battles,
                                           '{0}.battle'.format(self.id))
            with open(self.battleFile,'wt') as out_battle:
                for prop,value in self.properties.items():
                    print('{0}={1}'.format(prop,value), file=out_battle)

                # Competitors
                print('{0}={1}'.format(
                    Robocode.Battle.robotProp,
                    ','.join([ Robocode.Robot(r,self.robocode.robots).battleName()
                               for r in self.competitors ]),
                ), file=out_battle)


        def dbData( self ):
            '''
            an interface between this object and the database
            
            Each DB field is a key in the returned dict.
            '''

            # This is highly dependent on the DB schema.
            #   BattleID INTEGER PRIMARY KEY,
            #   Priority INTEGER,
            #   State TEXT,
            #   Started TEXT,
            #   Finished TEXT,
            #   Properties TEXT,
            #   Winner INTEGER,
            #   Obsolete INTEGER

            return {
                'BattleID'     :    self.id,
                'Started'      :    self.started,
                'Finished'     :    self.finished,
                'Properties'   :    json.dumps(self.properties,sort_keys=True),
                'Winner'       :    self.result.winner,
            }
            
