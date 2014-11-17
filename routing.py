
import logging

_logger = logging.getLogger('gerritbot.routing')
_handlers = {}

def trigger(event):
    global _handlers, _logger
    event_type = event['type']
    if event_type in _handlers:
        for handler in _handlers[event_type]:
            handler(event)
    else:
        _logger.info("Unhandled event type '%s'.", event_type)

def register_for(event_type):
    def wrapper(handler):
        global _handlers
        _handlers.setdefault(event_type, []).append(handler)
    return wrapper
