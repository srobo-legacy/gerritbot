
from nose import with_setup

import helpers

@with_setup(helpers.clear_messages, helpers.clear_messages)
def test_simple():
    helpers.trigger_from_file('sample-push.json')
    message = helpers.last_message()

    message = helpers.text_only(message)

    assert message == 'plaw submitted test(master) : CHEEEEEESE http://gerrit.srobo.org/32'
