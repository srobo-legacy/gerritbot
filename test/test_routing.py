
from routing import trigger, register_for

def test_no_handlers():
    event_name = 'test-no-handlers'

    test_event = {'type': event_name}
    trigger(test_event)

    # 'assert' no errors

def test_one_handler():
    events = []
    event_name = 'test-one-handler'

    @register_for(event_name)
    def dummy_handler(event):
        events.append(event)

    test_event = {'type': event_name}
    trigger(test_event)

    assert events == [test_event]

def test_only_handlers_for_event():
    events = []
    event_name = 'test-only-handlers-for-event'

    @register_for(event_name)
    def dummy_handler_1(event):
        events.append((1, event))

    @register_for('another-event')
    def dummy_handler_2(event):
        events.append((2, event))

    test_event = {'type': event_name}
    trigger(test_event)

    assert events == [(1,test_event)]

def test_all_relevant_handlers_called():
    events = []
    event_name = 'test-all-relevant-handlers-called'

    @register_for(event_name)
    def dummy_handler_1(event):
        events.append((1, event))

    @register_for(event_name)
    def dummy_handler_2(event):
        events.append((2, event))

    test_event = {'type': event_name}
    trigger(test_event)

    assert events == [(1, test_event), (2, test_event)]
