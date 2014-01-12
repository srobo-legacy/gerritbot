#!/usr/bin/python

'''
    Copyright 2010, The Android Open Source Project

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''

# bridge script to irc channel from gerrit livestream
# written by jeff sharkey and kenny root
# with modifications by jeremy morse, peter law and richard barlow

import sys

from gerritthread import GerritThread
from routing import trigger
from utils import config

# import the SR pipebot event handlers, which self-subscribe to the event routing
import irc_handlers

if __name__ == '__main__':
    gerrit = GerritThread(config, trigger); gerrit.start()

    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break
