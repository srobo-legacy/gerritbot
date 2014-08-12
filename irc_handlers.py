
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

from routing import register_for
from pipebot import say as emit_message
from utils import *

@register_for('change-abandoned')
def change_abandoned(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    owner = username_from_person(change["owner"])
    abandoner = username_from_person(event["abandoner"])

    if owner != abandoner:
        msg_owner = color(GREEN) + owner + "'s" + color()
    else:
        msg_owner = "their"
    msg_abandoner = color(GREEN) + abandoner + color()
    msg_description = describe_patchset(change)

    message = "%s abandoned %s change on %s" % (msg_abandoner, msg_owner, msg_description)
    emit_message(message)

@register_for('change-merged')
def change_merged(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    owner = username_from_person(change["owner"])

    msg_owner = color(GREEN) + owner + "'s" + color()
    msg_description = describe_patchset(change)

    message = "Applied %s change on %s" % (msg_owner, msg_description)
    emit_message(message)

@register_for('comment-added')
def comment_added(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    author = event["author"]
    author = username_from_person(author)

    msg_author = color(GREEN) + author + color()
    msg_description = describe_patchset(change)

    message = "%s reviewed %s" % (msg_author, msg_description)
    emit_message(message)

@register_for('patchset-created')
def patchset_created(event):
    change = event["change"]

    branch = change["branch"]
    if branch in branch_ignore: return

    uploader = username_from_person(event["uploader"])
    trac_id = extract_trac_id(change['subject'])
    number = int(event['patchSet']['number'])

    msg_owner = color(GREEN) + uploader + color()
    msg_description = describe_patchset(change)
    msg_verb = 'updated' if number > 1  else 'submitted'

    message = "%s %s %s" % (msg_owner, msg_verb, msg_description)

    if trac_id is not None:
        trac_link = link_from_trac_id(trac_id)
        msg_trac_link = color(NAVY, underline=True) + trac_link + color(GREY)
        message += " : %s" % (msg_trac_link)

    emit_message(message)

@register_for('ref-updated')
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
    emit_message(message)
