
import json
import os
import sys

def my_dir():
    return os.path.dirname(os.path.abspath(__file__))

def root():
    return os.path.dirname(my_dir())

sys.path.insert(0, root())

import gerritbot

def assert_exists(file_path):
    assert os.path.exists(file_path), "Path '{0}' must exist!".format(file_path)

def trigger_from_file(file_name):
    file_path = os.path.join(my_dir(), 'data', file_name)
    assert_exists(file_path)

    event = None
    with open(file_path, 'r') as f:
        event = json.load(f)

    assert event is not None, "Failed to load event data from '{0}'.".format(file_path)

    gerritbot.trigger(event)

messages = []

def store_message(message):
    global messages
    messages.append(message)

def clear_messages():
    global messages
    messages = []

def last_message():
    global messages
    assert len(messages), "No last message to get"
    return messages[-1]

# override the output function to our own
# TODO: re-architect things to avoid this?
gerritbot.irc_handlers.emit_message = store_message

def text_only(message):
    # strip out the colour characters
    to_remove = ['\x02', '\x0f', '\x1f', '\x032', '\x033', '\x0310', '\x0314']
    for char in to_remove:
        message = message.replace(char, '')

    return message
