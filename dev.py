#!/usr/bin/env python

import os
import simplejson
import sys

import gerritbot

if len(sys.argv) is not 2:
    print "Usage: dev.py EVENT.json"
    print "  Triggers the given event inside gerritbot"
    exit(1)

filePath = sys.argv[1]
if not os.path.exists(filePath):
    print "File '%s' doesn't exist." % filePath
    exit(1)

event = None
with open(filePath) as f:
    event_data = f.read()

event = simplejson.loads(event_data)

gerritbot.trigger(event)
