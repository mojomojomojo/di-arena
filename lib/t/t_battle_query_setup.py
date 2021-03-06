#!/usr/bin/env python3

'''
Attempt to schedule a number of battles, mark some as running, and
complete others. The goal is to leave the database in a state to test
some of the more complicated queries.
'''


import sys
sys.path.append('..')

from BattleData import BattleDB
from datetime import datetime
import Robocode
import random
import os
import os.path

def bdump(d,prefix='\n    '):
    return prefix.join(list(map(str,[ b.BattleID for b in d.values() ])))


def query_test(
        battledb, robocode,
        k_battles, k_r_battles,
        scheduled, running, finished_nonobs, finished, obsolete
):
    # scheduled
    got_scheduled = battledb.GetScheduledBattles()
    d_got_scheduled = { b.BattleID:b for b in got_scheduled }
    assert comp(d_got_scheduled,scheduled), \
        'Mismatch: scheduled battles\n  Got:\n    {got}\n  Expected:\n    {exp}'.format(
            got = bdump(d_got_scheduled),
            exp = bdump(scheduled),
        )

    # running
    got_running = battledb.GetRunningBattles()
    d_got_running = { b.BattleID:b for b in got_running }
    assert comp(d_got_running,running), \
        'Mismatch: running battles\n  Got:\n    {got}\n  Expected:\n    {exp}'.format(
            got = bdump(d_got_running),
            exp = bdump(running),
        )

    # finished, non-obsolete
    got_finished_nonobs = battledb.GetFinishedBattles(nonObsolete=True)
    d_got_finished_nonobs = { b.BattleID:b for b in got_finished_nonobs }
    assert comp(d_got_finished_nonobs,finished_nonobs), \
        'Mismatch: finished, non-obsolete battles\n  Got:\n    {got}\n  Expected:\n    {exp}'.format(
            got = bdump(d_got_finished_nonobs),
            exp = bdump(finished_nonobs),
        )


    # finished
    got_finished = battledb.GetFinishedBattles(nonObsolete = False)
    d_got_finished = { b.BattleID:b for b in got_finished }
    assert comp(d_got_finished,finished), \
        'Mismatch: finished battles\n  Got:\n    {got}\n  Expected:\n    {exp}'.format(
            got = bdump(d_got_finished),
            exp = bdump(running),
        )

    # obsolete
    got_obsolete = battledb.GetObsoleteBattles()
    d_got_obsolete = { b.BattleID:b for b in got_obsolete }
    assert comp(d_got_obsolete,obsolete), \
        'Mismatch: obsolete battles\n  Got:\n    {got}\n  Expected:\n    {exp}'.format(
            got = bdump(d_got_obsolete),
            exp = bdump(running),
        )


def comp( a, b ):
    '''
    Perform a comparison of keys (only) between the two dicts.
    '''
    return set(a.keys()) == set(b.keys())


def diff( from_dict, del_dict ):
    '''
    Return a shallow copy of from_dict with the items in del_dict removed.
    '''

    ret = from_dict.copy()
    for k in del_dict.keys():
        try:
            del(ret[k])
        except KeyError:
            pass

    return ret

def combine( a, b ):
    '''
    Return a shallow copy of from_dict with the items in del_dict added.
    '''

    ret = a.copy()
    for k,v in b.items():
        ret[k] = v

    return ret


db_file = 't_battle_query.sqlite3'
# always start clean
if os.path.isfile(db_file):
    os.remove(db_file)
bdata = BattleDB(db_file)

di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','arena')))
robocode = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..','robocode')))
robo = Robocode.Robocode(di_arena,robocode)


robots = [
    'jubjub_robofab.RandomRunner',
    'sample.Crazy',
    'sample.Fire',
    'sample.VelociRobot',
    'sample.Tracker',
]

for robotName in robots:
    robot = robo.robot( name = robotName )
    bdata.UpdateRobot( name = robot.name,
                       lastUpdated = robot.lastUpdated )

robots = bdata.GetRobots()

# Schedule a bunch of battles
num_battles = 20
battles = [
    bdata.ScheduleBattle(random.sample(robots,2))
    for i in range(num_battles)
]
d_battles = { b.BattleID:b for b in battles }
robot_battles = {
    r.RobotID:[ b.BattleID 
                for b in filter(lambda b:
                                r.RobotID in [_r.RobotID
                                              for _r in b.competitors()],
                                d_battles.values()) ]
    for r in robots
}
print('Battles by Robot: {0}'.format(robot_battles))

r_battles = {
    b.BattleID : robo.battle(b.BattleID,
                             [c.Name for c in b.competitors()],
                             b.getProperties())
    for b in battles
}

# Query for scheduled, running, finished, and obsolete battles.
query_test( 
    bdata, robo,
    d_battles, r_battles,
    scheduled = d_battles,
    running = {},
    finished_nonobs = {},
    finished = {},
    obsolete = {},
)

num_marked = 5
num_torun = 8
chosen = random.sample(battles,num_marked+num_torun)
marked_only = { b.BattleID:b for b in chosen[:num_marked] }
torun = { b.BattleID:b for b in chosen[num_marked:num_marked+num_torun] }
# Choose a robot from one run battle to obsolesce.
robot_to_obs = random.choice(random.sample(list(torun.values()),1)[0].competitors())
to_obs = { id:d_battles[id] for id in (set(torun.keys()) & {id for id in robot_battles[robot_to_obs.RobotID]}) }

print("Mark Only: {0}".format(list(marked_only.keys())))
print("To Run: {0}".format(list(torun.keys())))
print("To Obs ({0}): {1}".format(robot_to_obs.RobotID,list(to_obs.keys())))

print('\nMarking battles...')
for battle in marked_only.values():
    bdata.MarkBattleRunning(battle)


# Query for scheduled, running, finished, and obsolete battles.
query_test( 
    bdata, robo,
    d_battles, r_battles,
    scheduled = diff(d_battles,marked_only),
    running = marked_only,
    finished_nonobs  = {},
    finished  = {},
    obsolete  = {},
)


print('\nRunning battles...')
for battle in torun.values():
    bdata.MarkBattleRunning(battle)


# Query for scheduled, running, finished, and obsolete battles.
query_test( 
    bdata, robo,
    d_battles, r_battles,
    scheduled = diff(diff(d_battles,marked_only),torun),
    running = combine(marked_only,torun),
    finished_nonobs  = {},
    finished  = {},
    obsolete  = {},
)

profBattle = datetime.now()
for battle in torun.values():
    r_battle = r_battles[battle.BattleID]
    r_battle.run()
    print('.',end='')
    sys.stdout.flush()

    bdata.BattleCompleted(battle,
                          r_battle.dbData(),
                          r_battle.result.dbData())
print()
print("  Time Per Battle: {0}".format((datetime.now()-profBattle)/len(torun)))

# Query for scheduled, running, finished, and obsolete battles.
query_test( 
    bdata, robo,
    d_battles, r_battles,
    scheduled = diff(diff(d_battles,marked_only),torun),
    running = marked_only,
    finished_nonobs = torun,
    finished = torun,
    obsolete  = {},
)


print('\n\nObsolescing battles for ({0}): {1}'.format(robot_to_obs.RobotID,list(to_obs.keys())))
print('Robot:\n{0}'.format(robot_to_obs))
bdata.UpdateRobot(lastUpdated=datetime.now(),id=robot_to_obs.RobotID)
bdata.ObsolesceBattles()
# Query for scheduled, running, finished, and obsolete battles.
query_test( 
    bdata, robo,
    d_battles, r_battles,
    scheduled = diff(diff(d_battles,marked_only),torun),
    running = marked_only,
    finished_nonobs = diff(torun,to_obs),
    finished = torun,
    obsolete  = to_obs,
)


print("\nAll queries return expected values.")
print("\n[TEST_OK]")
