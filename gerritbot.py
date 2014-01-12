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


import re, os, sys, ConfigParser
import socket, paramiko
import threading, time, random
import simplejson
import subprocess

# config file section titles
GERRIT = "GerritServer"
IRC = "IrcServer"
BRANCHES = "Branches"
GENERAL = "General"

config = ConfigParser.ConfigParser()
config.read("gerritbot.conf")


NONE, BLACK, NAVY, GREEN, RED, BROWN, PURPLE, OLIVE, YELLOW, LIME, TEAL, AQUA, BLUE, PINK, GREY, SILVER, WHITE = range(17)

def color(fg=None, bg=None, bold=False, underline=False):
    # generate sequence for irc formatting
    result = "\x0f"
    if not fg is None: result += "\x03%d" % (fg)
    if not bg is None: result += ",%s" % (bg)
    if bold: result += "\x02"
    if underline: result += "\x1f"
    return result

branch_colors = {}
branch_ignore = []
for name, value in config.items(BRANCHES):
    if value == "IGNORE":
        branch_ignore.append(name)
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
        branch_colors[name] = color(globals()[colour], bold=bold, underline=underline)


def shorten_project(project):
    # shorten long project names by omitting middle
    reinner = re.compile('^([^/]+)/(.+?)/([^/]+)$')
    match = reinner.match(project)
    if match is None: return project

    first, middle, last = match.groups()
    if len(middle) < 16: return project
    return "%s/../%s" % (first, last)

def shorten_hash(full_hash):
    if len(full_hash) <= 7:
        return full_hash
    return full_hash[:7]

def trigger(event):
    if event["type"] == "change-abandoned":
        change_abandoned(event)
    elif event["type"] == "comment-added":
        comment_added(event)
    elif event["type"] == "change-merged":
        change_merged(event)
    elif event["type"] == "patchset-created":
        patchset_created(event)
    elif event["type"] == "ref-updated":
        ref_updated(event)
    else:
        pass

class GerritThread(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.config = config

    def run(self):
        while True:
            self.run_internal()
            print self, "sleeping and wrapping around"
            time.sleep(5)

    def run_internal(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = self.config.get(GERRIT, "host")
        port = self.config.getint(GERRIT, "port")
        user = self.config.get(GERRIT, "user")
        privkey = self.config.get(GERRIT, "privkey")

        try:
            print self, "connecting to", host
            client.connect(host, port, user, key_filename=privkey, timeout=60)
            client.get_transport().set_keepalive(60)

            stdin, stdout, stderr = client.exec_command("gerrit stream-events")
            for line in stdout:
                print line
                try:
                    event = simplejson.loads(line)
                    trigger(event)
                except ValueError:
                    pass
            client.close()
        except Exception, e:
            print self, "unexpected", e

def username_from_person(person):
    username = re.compile(r'@.+').sub("", person["email"])
    return username

def project_from_change(change):
    project = re.compile(r'^platform/').sub("", change["project"])
    return project

def link_from_change(change):
    link = config.get(GENERAL, "shortlink") % (change["number"])
    return link

def link_from_trac_id(trac_id):
    link = config.get(GENERAL, "traclink") % str(trac_id)
    return link

def get_branch_color(branch):
    branch_color = branch_colors.get(branch, color(NAVY))
    return branch_color

def build_repo_branch(project, branch):
    project = shorten_project(project)
    branch_color = get_branch_color(branch)

    msg_branch = branch_color + branch + color(GREY)
    msg_project = color(TEAL,bold=True) + project + color(GREY)

    msg_project_branch = "%s(%s)" % (msg_project, msg_branch)

    return msg_project_branch

def extract_trac_id(message):
    match = re.match('^Fix #(\d+):', message)
    if match is None:
        return None
    number = match.groups(1)[0]
    return number

def change_abandoned(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    project = project_from_change(change)
    owner = username_from_person(change["owner"])
    abandoner = username_from_person(event["abandoner"])
    subject = change["subject"]
    link = link_from_change(change)

    if owner != abandoner:
        msg_owner = color(GREEN) + owner + "'s" + color()
    else:
        msg_owner = "their"
    msg_abandoner = color(GREEN) + abandoner + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    message = "%s abandoned %s change on %s : %s %s" % (msg_abandoner, msg_owner, msg_project_branch, msg_subject, msg_link)
    subprocess.call(['./pipebot/say', message])

def change_merged(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    project = project_from_change(change)
    owner = username_from_person(change["owner"])
    subject = change["subject"]
    link = link_from_change(change)

    msg_owner = color(GREEN) + owner + "'s" + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    message = "Applied %s change on %s : %s %s" % (msg_owner, msg_project_branch, msg_subject, msg_link)
    subprocess.call(['./pipebot/say', message])

def comment_added(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    author = event["author"]

    project = project_from_change(change)
    author = username_from_person(author)
    subject = change["subject"]
    link = link_from_change(change)

    msg_author = color(GREEN) + author + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    message = "%s reviewed %s : %s %s" % (msg_author, msg_project_branch, msg_subject, msg_link)
    subprocess.call(['./pipebot/say', message])

def patchset_created(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    project = project_from_change(change)
    uploader = username_from_person(event["uploader"])
    subject = change["subject"]
    link = link_from_change(change)
    trac_id = extract_trac_id(change['subject'])
    number = int(event['patchSet']['number'])

    msg_owner = color(GREEN) + uploader + color()
    msg_project_branch = build_repo_branch(project, branch)
    msg_subject = color() + subject + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color(GREY)
    msg_verb = 'updated' if number > 1  else 'submitted'

    message = "%s %s %s : %s %s" % (msg_owner, msg_verb, msg_project_branch, msg_subject, msg_link)

    if trac_id is not None:
        trac_link = link_from_trac_id(trac_id)
        msg_trac_link = color(NAVY, underline=True) + trac_link + color(GREY)
        message += " : %s" % (msg_trac_link)

    subprocess.call(['./pipebot/say', message])

def ref_updated(event):
    updated_ref = event["refUpdate"]

    branch = updated_ref["refName"]
    if branch in branch_ignore: return

    to_hash = shorten_hash(updated_ref['newRev'])
    from_hash = shorten_hash(updated_ref['oldRev'])

    project = project_from_change(updated_ref)
    submitter = username_from_person(event["submitter"])
    link = "http://srobo.org/cgit/%s.git" % project

    msg_project_branch = build_repo_branch(project, branch) + color()
    msg_owner = color(GREEN) + submitter + color()
    msg_old_ref = color(bold=True) + from_hash + color()
    msg_new_ref = color(bold=True) + to_hash + color(GREY)
    msg_link = color(NAVY, underline=True) + link + color()

    message = "%s updated %s from %s to %s : %s" % (msg_owner, msg_project_branch, msg_old_ref, msg_new_ref, msg_link)
    subprocess.call(['./pipebot/say', message])

if __name__ == '__main__':
    gerrit = GerritThread(config); gerrit.start()

    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break
