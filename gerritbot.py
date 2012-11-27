#!/usr/bin/env python3

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
from configparser import ConfigParser
import json
import re
import subprocess
import sys
import threading
from time import sleep

import gerrit_stream

# config file section titles
GERRIT = "GerritServer"
IRC = "IrcServer"
BRANCHES = "Branches"
GENERAL = "General"

CONFIG = ConfigParser()
CONFIG.read("gerritbot.conf")


(NONE, BLACK, NAVY, GREEN, RED, BROWN, PURPLE, OLIVE, YELLOW,
 LIME, TEAL, AQUA, BLUE, PINK, GREY, SILVER, WHITE) = range(17)


def color(fg=None, bg=None, bold=False, underline=False):
    # generate sequence for irc formatting
    result = "\x0f"
    if not fg is None:
        result += "\x03{0}".format(fg)
    if not bg is None:
        result += ",{0}".format(bg)
    if bold:
        result += "\x02"
    if underline:
        result += "\x1f"
    return result

BRANCH_COLORS = {}
BRANCH_IGNORE = []
for name, value in CONFIG.items(BRANCHES):
    if value == "IGNORE":
        BRANCH_IGNORE.append(name)
    else:
        bold = False
        underline = False
        colour = value
        if ':' in value:
            colour, mods = value.split(':')
            if 'BOLD' in mods:
                bold = True
            if 'UNDERLINE' in mods:
                underline = True
        BRANCH_COLORS[name] = color(globals()[colour],  # ouch!
                                    bold=bold, underline=underline)


PROJECT_INNER_RE = re.compile('^([^/]+)/(.+?)/([^/]+)$')

def shorten_project(project):
    # shorten long project names by omitting middle
    match = PROJECT_INNER_RE.match(project)
    if match is None:
        return project

    first, middle, last = match.groups()
    if len(middle) < 16:
        return project
    return "{0}/../{1}".format(first, last)

def shorten_hash(full_hash):
    if len(full_hash) <= 7:
        return full_hash
    return full_hash[:7]

EVENT_HANDLERS = {}
def trigger(event):
    handler = EVENT_HANDLERS.get(event["type"], lambda x: None)
    handler(event)

def event_handler(name):
    def wrap(fn):
        EVENT_HANDLERS[name] = fn
        return fn
    return wrap

class GerritThread(threading.Thread):
    def __init__(self, config):
        super().__init__()
        self.daemon = True
        self.config = config

    def run(self):
        while True:
            self.run_internal()
            print(self, "sleeping and wrapping around")
            sleep(5)

    def run_internal(self):
        host = self.config.get(GERRIT, "host")
        port = self.config.getint(GERRIT, "port")
        user = self.config.get(GERRIT, "user")
        privkey = self.config.get(GERRIT, "privkey")

        try:
            print(self, "connecting to", host)
            stream = gerrit_stream.GerritStream(host, user, port, privkey)
            for event in stream:
                trigger(event)
        except Exception as exception:
            print(self, "unexpected", exception)

USERNAME_RE = re.compile(r'@.+')
def username_from_person(person):
    username = USERNAME_RE.sub("", person["email"])
    return username

PROJECT_RE = re.compile(r'^platform/')
def project_from_change(change):
    project = PROJECT_RE.sub("", change["project"])
    return project

def link_from_change(change):
    link = CONFIG.get(GENERAL, "shortlink").format(id=change["number"])
    return link

def get_branch_color(branch):
    branch_color = BRANCH_COLORS.get(branch, color(NAVY))
    return branch_color

def build_repo_branch(project, branch):
    project = shorten_project(project)
    branch_color = get_branch_color(branch)

    msg_branch = branch_color + branch + color(GREY)
    msg_project = color(TEAL, bold=True) + project + color(GREY)

    return "{project}({branch})".format(project=msg_project,
                                        branch=msg_branch)

    return msg_project_branch

@event_handler("change-merged")
def change_merged(event):
    change = event["change"]

    branch = change["branch"]
    if branch in BRANCH_IGNORE:
        return

    project = project_from_change(change)
    owner = username_from_person(change["owner"])
    subject = change["subject"]
    link = link_from_change(change)

    msg_owner = color(GREEN) + owner + "'s" + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    MESSAGE_FORMAT = "Applied {owner} change on {project}: {subject} {link}"
    message = MESSAGE_FORMAT.format(owner=msg_owner,
                                    project=msg_project_branch,
                                    subject=msg_subject,
                                    link=msg_link)
    subprocess.call(['./pipebot/say', message])

@event_handler("comment-added")
def comment_added(event):
    change = event["change"]

    branch = change["branch"]
    if branch in BRANCH_IGNORE:
        return

    author = event["author"]

    project = project_from_change(change)
    author = username_from_person(author)
    subject = change["subject"]
    link = link_from_change(change)

    msg_author = color(GREEN) + author + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    MESSAGE_FORMAT = "{author} reviewed {project}: {subject} {link}"
    message = MESSAGE_FORMAT.format(author=msg_author,
                                    project=msg_project_branch,
                                    subject=msg_subject,
                                    link=msg_link)
    subprocess.call(['./pipebot/say', message])

@event_handler("patchset-created")
def patchset_created(event):
    change = event["change"]

    branch = change["branch"]
    if branch in BRANCH_IGNORE:
        return

    project = project_from_change(change)
    uploader = username_from_person(event["uploader"])
    subject = change["subject"]
    link = link_from_change(change)
    number = event['patchSet']['number']

    msg_owner = color(GREEN) + uploader + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)
    msg_verb = 'updated' if number > 1 else 'submitted'

    MESSAGE_FORMAT = "{owner} {verb} {project}: {subject} {link}"
    message = MESSAGE_FORMAT.format(owner=msg_owner,
                                    verb=msg_verb,
                                    project=msg_project_branch,
                                    subject=msg_project,
                                    link=msg_link)
    subprocess.call(['./pipebot/say', message])

@event_handler("ref-updated")
def ref_updated(event):
    updated_ref = event["refUpdate"]

    branch = updated_ref["refName"]
    if branch in BRANCH_IGNORE:
        return

    to_hash = shorten_hash(updated_ref['newRev'])
    from_hash = shorten_hash(updated_ref['oldRev'])

    project = project_from_change(updated_ref)
    submitter = username_from_person(event["submitter"])
    link = "http://git.srobo.org/{project}.git".format(project=project)

    msg_project_branch = build_repo_branch(project, branch) + color()
    msg_owner = color(GREEN) + submitter + color()
    msg_old_ref = color(bold=True) + from_hash + color()
    msg_new_ref = color(bold=True) + to_hash + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color()

    MESSAGE_FORMAT = "{owner} updated {project} from {old} to {new}: {link}"
    message = MESSAGE_FORMAT.format(owner=msg_owner,
                                    project=msg_project_branch,
                                    old=msg_old_ref,
                                    new=msg_new_ref,
                                    link=msg_link)
    subprocess.check_call(['./pipebot/say', message])

def main():
    gerrit = GerritThread(CONFIG)
    gerrit.start()

    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    main()
