#!/usr/bin/env python3

import os
import json
import sys

import gerritbot

if len(sys.argv) < 2:
    print("Usage: dev.py EVENT_FILE.json [EVENT_FILE.json ..]",
          file=sys.stderr)
    print("  Triggers the given events inside gerritbot", file=sys.stderr)
    exit(1)

paths = sys.argv[1:]
for file_path in paths:
    if not os.path.exists(file_path):
        print("File '{0}' doesn't exist.".format(file_path), file=sys.stderr)
        continue

    event = None
    with open(file_path, 'r') as f:
        event = json.load(f)

    gerritbot.trigger(event)
