#!/usr/bin/env python3

import sqlite3
import re
import json
import csv
import sys
from datetime import datetime

class DBRecord:
    '''
    instances of this class resemble a database record
    '''
    def __init__(self, db_rec):
        for col in db_rec.keys():
            setattr(self,col,db_rec[col])

    def __str__(self):
        non_internal = re.compile(r'^[^_]')
        return '[{0} {1}]'.format(
            self.__class__.__name__,
            ' '.join(
                [ '{0}({1})'.format(attr,getattr(self,attr))
                  for attr in filter(non_internal.match,vars(self).keys()) ]),
        )
            

class Battle(DBRecord):
    def __init__(self, record, db):
        self.db = db
        self._robots = []
        super().__init__(record)

    def addCompetitor( self, robot ):
        self._robots.append(robot)

    def getProperties( self ):
        return json.loads(self.Properties)

    def competitors( self ):
        '''
        This returns a list of BattleData.Robot.
        '''
        return self._robots

    def __str__(self):
        return '{0}\n  {1}'.format(
            super().__str__(),
            '\n  '.join(list(map(str,self._robots))),
        )


class Robot(DBRecord):
    def __init__(self, record, db):
        self.db = db
        super().__init__(record)


class BattleDB:
    def __init__( self, db_file ):
        self.db_file = db_file
        self.conn = None
        self._debug = False

    def __del__( self ):
        if self.conn:
            self.conn.close()

    def __str__( self ):
        return '[BattleDB file({0})]'.format(
            self.db_file,
        )

    def debug( self, state=None ):
        if state is None:
            self._debug = not self._debug
        else:
            self._debug = state

    def connect( self ):
        if self.conn is not None:
            return

        self.conn = sqlite3.connect(self.db_file,
                                    # autocommit
                                    isolation_level = None)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS Robots (
               RobotID INTEGER PRIMARY KEY,
               Name TEXT,
               LastUpdated Text
            );
            ''')

        # State: scheduled,running,finished
        # Started/Finish: ISO timestamps
        # Obsolete: boolean
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS Battles (
               BattleID INTEGER PRIMARY KEY,
               Priority INTEGER,
               State TEXT,
               Started TEXT,
               Finished TEXT,
               Properties TEXT,
               Winner INTEGER,
               Obsolete INTEGER
            );
            ''')

        # Score: -1 means no results
        # Results: stringified dict of properties
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS BattleRobots (
               BattleID INTEGER,
               RobotID INTEGER,
               RobotUpdated TEXT,
               Score INTEGER,
               Results TEXT,
               PRIMARY KEY(BattleID,RobotID)
            );
            ''')



    #
    # Robots
    #

    def UpdateRobot( self, lastUpdated=None, name=None, id=None ):
        self.connect()

        if lastUpdated is None:
            lastUpdated = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        elif lastUpdated.__class__ == datetime:
            lastUpdated = lastUpdated.strftime('%Y-%m-%dT%H:%M:%S')

        if id is None:
            if name is None:
                raise ValueError('UpdateRobot() cannot create new robot without a name')
            # ensure that names are unique
            try:
                orig = self.GetRobot(name=name)
                raise ValueError('UpdateRobot() cannot create new robot with duplicate name ({0}): {1}'.format(name,orig))
            except:
                # good
                pass

            # new robot
            insert = self.conn.execute('''
               INSERT INTO Robots
               (Name,LastUpdated)
               VALUES (?,?)
            ''', [name,lastUpdated])
            return self.GetRobot(id=insert.lastrowid)

        else:
            # updated robot
            self.conn.execute('''
               UPDATE Robots
               SET LastUpdated=?
               WHERE RobotID=?
            ''', [lastUpdated,id])
            return self.GetRobot(id=id)


    def GetRobots( self ):
        self.connect()
        return [
            Robot(record,self)
            for record in self.conn.execute('SELECT * FROM Robots').fetchall()
            ]
            

    def GetRobot( self, name=None, id=None ):
        if name is None and id is None:
            raise ValueError('GetRobot() called with neither name or id')

        self.connect()

        if id is not None:
            for record in self.conn.execute('''
               SELECT *
               FROM Robots
               WHERE RobotID=?
               ;
            ''',[id]):
                return Robot(record,self)
            raise KeyError("GetRobot() no robot with ID '{0}' found".format(id))
        if name is not None:
            for record in self.conn.execute('''
               SELECT *
               FROM Robots
               WHERE Name=?
               ;
            ''',[name]):
                return Robot(record,self)
            raise KeyError("GetRobot() no robot with name '{0}' found".format(name))

    def dump( self, ofile=sys.stdout, otype='json' ):
        '''
        Dump the database contents.
        '''
        self.connect()

        o_csv = csv.writer(ofile)

        for table in ['Robots','Battles','BattleRobots']:
            print('\n\nTABLE: {0}'.format(table),file=ofile)
            emitHeader = True
            for row in self.conn.execute('SELECT * FROM {0}'.format(table)):
                if otype == 'csv':
                    if emitHeader:
                        o_csv.writerow(row.keys())
                        emitHeader = False
                    o_csv.writerow([row[k] for k in row.keys()])
                elif otype == 'json':
                    print(json.dumps({ k:row[k] for k in row.keys()},
                                     sort_keys=True,
                                     indent=4),
                          file=ofile)



    #
    # Battles
    #

    defaultProperties = {
        'robocode.battleField.width':800,
        'robocode.battleField.height':600,
        'robocode.battle.numRounds':10,
        'robocode.battle.gunCoolingRate':0.1,
        'robocode.battle.rules.inactivityTime':450,
        'robocode.battle.hideEnemyNames':True,
    }

    def ObsolesceBattles( self ):
        '''
        Check each of the finished battles to see if any of the competitors
        has since been updated.
        '''

        self.connect()

        self.conn.execute('''
            UPDATE Battles
            SET Obsolete=1
            WHERE BattleID IN (
                     SELECT BattleRobots.BattleID
                     FROM BattleRobots
                       INNER JOIN Robots
                       ON BattleRobots.RobotID=Robots.RobotID
                     WHERE Robots.LastUpdated > BattleRobots.RobotUpdated
                       AND BattleRobots.RobotUpdated <> ''
                  )
              AND Obsolete=0
              AND State='finished'
        ''',[])

        
    def GetRobotBattles( self, robot,
                         state=['finished'], obsolete=False ):
        '''
        Return a list of BattleData.Battle objects for which <robot> is a
           competitor.
        '''
        pass


    def GetRunningBattles(self):
        return self.GetBattles(State='running')

    def GetScheduledBattles(self):
        return self.GetBattles(State='scheduled')

    def GetFinishedBattles(self, nonObsolete=True):
        if nonObsolete:
            return self.GetBattles(State='finished',Obsolete=0)
        else:
            return self.GetBattles(State='finished')

    def GetObsoleteBattles(self):
        return self.GetBattles(Obsolete=1)

    def GetBattles( self, *sql_conditions, **conditions ):
        self.connect()

        # Construct the SQL query.
        query = '''
            SELECT BattleID
            FROM Battles
        '''
        params = []
        if len(sql_conditions) + len(conditions) > 0:
            conds = list(sql_conditions) + \
                    list(map(lambda f:'{0}=?'.format(f),conditions.keys()))
            query += 'WHERE {0}'.format(
                ' AND '.join(conds)
            )
            params = [ str(v) for v in conditions.values() ]

        if self._debug:
            print('Query: {0}\nParams: {1}'.format(query,params)) #DEBUG

        return [
            self.GetBattle(record['BattleID'])
            for record in self.conn.execute(query,params)
        ]


    def GetBattle( self, id ):
        '''
        Query and return the battle matching the specified ID from the DB.

        This method is the only one that adds the battle's competitors.
        Anything that returns a BattleData.Battle should use this.
        '''
        self.connect()

        if id.__class__ == Battle:
            id = id.BattleID

        battle = None
        for record in self.conn.execute('''
           SELECT *
           FROM Battles
           WHERE BattleID=?
           ;
        ''',[id]):
            battle = Battle(record,self)
            break
        else:
            raise KeyError("GetBattle() no Battle with ID '{0}' found".format(id))

        for record in self.conn.execute('''
           SELECT *
           FROM BattleRobots
           WHERE BattleID=?
           ;
        ''',[id]):
            battle.addCompetitor(self.GetRobot(id=record['RobotID']))

        return battle


    def ScheduleBattle( self, competitors, properties=None ):
        if properties is None:
            properties = self.__class__.defaultProperties

        self.connect;

        # Create the battle
        insert = self.conn.execute('''
           INSERT INTO Battles
           (State,Priority,Started,Finished,Properties,Winner,Obsolete)
           VALUES ('scheduled',-1,'','',?,-1,0)
           ;
        ''',[json.dumps(properties)])
        battle_obj = self.GetBattle(insert.lastrowid)

        for robot in competitors:
            # allow ID's or Robots
            if robot.__class__ != Robot:
                robotID = robot
                robot = self.GetRobot(id=robotID)
            else:
                robotID = robot.RobotID

            self.conn.execute('''
                INSERT INTO BattleRobots
                (BattleID,RobotID,RobotUpdated,Score,Results)
                VALUES (?,?,'',-1,'')
                ;
            ''',[battle_obj.BattleID,robot.RobotID])

        return self.GetBattle(battle_obj.BattleID)


    class BattleAlreadyFinished(Exception):
        def __init__(self,battle):
            self.battle = battle
        def __str__(self):
            return 'The battle is already finished: {0}'.format(battle)
    class BattleAlreadyStarted(Exception):
        def __init__(self,battle):
            self.battle = battle
        def __str__(self):
            return 'The battle is already started: {0}'.format(battle)
    class BattleNotStarted(Exception):
        def __init__(self,battle):
            self.battle = battle
        def __str__(self):
            return 'The battle has not been started: {0}'.format(battle)

    def MarkBattleRunning( self, battle ):
        self.connect()

        # validate/normalize <battle>
        if battle.__class__ == Battle:
            # replace it with current data
            battle = self.GetBattle(battle.BattleID)
        else:
            battle = self.GetBattle(battle)

        # Verify that it isn't already running or finished
        if battle.Finished:
            raise BattleDB.BattleAlreadyFinished(battle)
        if battle.Started:
            raise BattleDB.BattleAlreadyStarted(battle)

        # Change the Battle.State
        self.conn.execute('''
            UPDATE Battles
            SET State='running',
                Started=?
            WHERE BattleID=?
        ''',[ datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
              battle.BattleID ])

        # Update the BattleRobot.RobotUpdated
        self.conn.execute('''
            UPDATE BattleRobots
            SET RobotUpdated=(
                SELECT LastUpdated
                FROM Robots
                WHERE RobotID=BattleRobots.RobotID
            )
            WHERE BattleID=?
        ''',[battle.BattleID])


    def BattleCompleted( self, battle, battleData, resultData ):
        '''
        <battle> is a BattleData.Battle object or a BattleID
        battleData is a dict of battle data
        '''
        self.connect()

        # validate/normalize <battle>
        if battle.__class__ == Battle:
            # replace it with current data
            battle = self.GetBattle(battle.BattleID)
        else:
            battle = self.GetBattle(battle)

        # Verify that it isn't already running or finished
        if battle.Finished:
            raise BattleDB.BattleAlreadyFinished(battle)
        if battle.State != 'running':
            raise BattleDB.BattleNotStarted(battle)

        winner = None
        for robot in battle.competitors():
            if robot.Name == battleData['Winner']:
                winner = robot.RobotID
        if winner is None:
            raise ValueError('No winner found ({0})'.format(battleData['Winner']))
        
        # Change the Battle.State
        self.conn.execute('''
            UPDATE Battles
            SET State='finished',
                Started=?,
                Finished=?,
                Winner=?,
                Properties=?
            WHERE BattleID=?
        ''',[battleData['Started'],
             battleData['Finished'],
             winner,
             battleData['Properties'], # these should be definitive

             battle.BattleID])


        # Update the BattleRobot.RobotUpdated
        for robot in battle.competitors():
            self.conn.execute('''
                UPDATE BattleRobots
                SET Score=?,
                    Results=?
                WHERE BattleID=? AND RobotID=?
            ''',[ resultData[robot.Name]['Score'],
                  resultData[robot.Name]['Results'],

                  battle.BattleID,
                  robot.RobotID ])
