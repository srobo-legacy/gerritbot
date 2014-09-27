from __future__ import print_function

_handlers = {}

def trigger(event):
    event_type = event['type']
    if event_type in _handlers:
        for handler in _handlers[event_type]:
            handler(event)
    else:
        print("Unhandled event type '{0}'.".format(event_type))

def register_for(event_type):
    def wrapper(handler):
        if not event_type in _handlers:
            _handlers[event_type] = []
        _handlers[event_type].append(handler)
    return wrapper
