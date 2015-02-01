
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

try:
    # python 2
    import ConfigParser as configparser
except ImportError:
    # python 3
    import configparser

import os.path
import re

# config file section titles
BRANCHES = "Branches"
GENERAL = "General"

config = configparser.RawConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "gerritbot.conf"))

NONE, BLACK, NAVY, GREEN, RED, BROWN, PURPLE, OLIVE, YELLOW, LIME, TEAL, AQUA, BLUE, PINK, GREY, SILVER, WHITE = range(17)

def color(fg=None, bg=None, bold=False, underline=False):
    # generate sequence for irc formatting
    result = "\x0f"
    if not fg is None: result += "\x03%d" % (fg)
    if not bg is None: result += ",%s" % (bg)
    if bold: result += "\x02"
    if underline: result += "\x1f"
    return result

# set up the branch colours mapping
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


def username_from_person(person):
    username = person["username"]
    return username

def project_from_change(change):
    project = re.compile(r'^platform/').sub("", change["project"])
    return project

def link_from_change(change):
    link = config.get(GENERAL, "shortlink") % (change["number"])
    return link

def link_from_project(project):
    link = config.get(GENERAL, "projlink") % (project,)
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

def is_private(project):
    return project.startswith('priv/')

def describe_patchset(change):
    project = project_from_change(change)
    link = link_from_change(change)

    branch = change['branch']
    subject = change["subject"]

    msg_project_branch = build_repo_branch(project, branch)
    msg_link = color(NAVY, underline=True) + link + color(GREY)

    msg_subject = ''
    if not is_private(project):
        msg_subject = color() + subject + color(GREY) + ' '

    description = "%s : %s%s" % (msg_project_branch, msg_subject, msg_link)
    return description
