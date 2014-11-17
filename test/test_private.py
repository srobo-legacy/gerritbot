
from nose import with_setup

import helpers

@with_setup(helpers.clear_messages, helpers.clear_messages)
def test_private():
    helpers.trigger_from_file('private-push.json')

    message = helpers.last_message()
    message = helpers.text_only(message)

    assert "SECRET" not in message, 'private commit message was published'
