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
import irclib


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


def shorten_project(project):
    # shorten long project names by omitting middle
    reinner = re.compile('^([^/]+)/(.+?)/([^/]+)$')
    match = reinner.match(project)
    if match is None: return project

    first, middle, last = match.groups()
    if len(middle) < 16: return project
    return "%s/../%s" % (first, last)



class GerritThread(threading.Thread):
    def __init__(self, config, irc):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.config = config
        self.irc = irc

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
                    if event["type"] == "comment-added":
                        self.irc.comment_added(event)
                    elif event["type"] == "change-merged":
                        self.irc.change_merged(event)
                    else:
                        pass
                except ValueError:
                    pass
            client.close()
        except Exception, e:
            print self, "unexpected", e



class IrcClient(irclib.SimpleIRCClient):
    pass


class IrcThread(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.config = config

        self.branch_ignore = []
        self.branch_colors = {}
        for name, value in config.items(BRANCHES):
            if value == "IGNORE":
                self.branch_ignore.append(name)
            else:
                self.branch_colors[name] = color(globals()[value])

    def run(self):
        host = self.config.get(IRC, "host")
        port = self.config.getint(IRC, "port")
        nick = self.config.get(IRC, "nick")

        print self, "connecting to", host
        self.client = IrcClient()
        self.client.connect(host, port, nick, username=nick, ircname=nick)
        self.client.start()

    def finish_setup(self):
        nick = self.config.get(IRC, "nick")
        mode = self.config.get(IRC, "mode")
        channel = self.config.get(IRC, "channel")
        key = self.config.get(IRC, "key")
        nickpass = self.config.get(IRC, "nickpass")

        self.client.connection.privmsg("NickServ", "IDENTIFY %s" % (nickpass))
        self.client.connection.mode(nick, mode)
        time.sleep(2)
        self.client.connection.join(channel, key)

    def _topic(self, topic):
        channel = self.config.get(IRC, "channel")
        self.client.connection.topic(channel, topic)

    def _privmsg(self, msg):
        channel = self.config.get(IRC, "channel")
        self.client.connection.privmsg(channel, msg)

    def change_merged(self, event):
        change = event["change"]

        branch = change["branch"]
        if branch in self.branch_ignore: pass

        project = re.compile(r'^platform/').sub("", change["project"])
        owner = re.compile(r'@.+').sub("", change["owner"]["email"])
        subject = change["subject"]
        link = self.config.get(GENERAL, "shortlink") % (change["id"][:9])

        project = shorten_project(project)
        branch_color = self.branch_colors.get(branch, color(GREY))

        msg_branch = branch_color + branch + color(GREY)
        msg_project = color(TEAL,bold=True) + project + color(GREY)
        msg_owner = color(TEAL) + owner + color(GREY)
        msg_subject = color() + subject + color(GREY)
        msg_link = color(NAVY, underline=True) + link + color(GREY)

        message = "%s | %s | %s > %s %s" % (msg_branch, msg_project, msg_owner, msg_subject, msg_link)
        self._privmsg(message)

    def comment_added(self, event):
        pass



irc = IrcThread(config); irc.start()

# sleep before joining to work around unrealircd bug
time.sleep(2)
irc.finish_setup()

# sleep before spinning up threads to wait for chanserv
time.sleep(5)

gerrit = GerritThread(config, irc); gerrit.start()



while True:
    try:
        line = sys.stdin.readline()
    except KeyboardInterrupt:
        break


