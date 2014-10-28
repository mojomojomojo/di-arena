#!/usr/bin/env python3

import RobotMonitor

monitor = RobotMonitor.CompetitorMonitor('monitor.sqlite')

monitor.monitor('robots')
