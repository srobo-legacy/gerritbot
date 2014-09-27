#!/usr/bin/env python

from __future__ import print_function

import os
import simplejson
import sys

import gerritbot

if len(sys.argv) < 2:
    print("Usage: dev.py EVENT_FILE.json [EVENT_FILE.json ..]")
    print("  Triggers the given events inside gerritbot")
    exit(1)

paths = sys.argv[1:]
for filePath in paths:
    if not os.path.exists(filePath):
        print("File '%s' doesn't exist." % filePath)
        continue

    event = None
    with open(filePath) as f:
        event_data = f.read()

    event = simplejson.loads(event_data)

    gerritbot.trigger(event)
