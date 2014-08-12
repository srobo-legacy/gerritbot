
from nose import with_setup

import helpers

@with_setup(helpers.clear_messages, helpers.clear_messages)
def test_private():
    helpers.trigger_from_file('private-push.json')
    assert not helpers.messages, 'private commit was published'

