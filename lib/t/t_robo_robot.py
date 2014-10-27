#!/usr/bin/env python3

import sys
sys.path.append('..')
import Robocode
import os.path

di_arena = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__),'..')))
robo = Robocode.Robocode(os.path.join(di_arena,'robocode'),
                         robots = os.path.join(di_arena,'robots'),
                         battles = os.path.join(di_arena,'battles'),
                         results = os.path.join(di_arena,'results'),
                         recordings = os.path.join(di_arena,'recordings'),
                     )
print(robo)

print("\n\nName:")
robot = robo.robot( name = 'jubjub_robofab.RandomRunner' )
print(robot)
robot = robo.robot( name = 'sample.Crazy' )
print(robot)


print("\n\nDescriptor:")
robot = robo.robot(descriptor = 
                   os.path.join(robo.robots,
                                'jubjub_robofab',
                                'RandomRunner.robot'))
print(robot)
robot = robo.robot(descriptor = 
                   os.path.join(robo.robots,
                                'sample',
                                'Crazy.robot'))
print(robot)

