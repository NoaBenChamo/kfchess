class EventBus:
    """
    In-process pub/sub bus keyed by concrete event type.
    A failing subscriber must not break other subscribers or the publisher.
    """

    def __init__(self):
        self._handlers = {}

    def subscribe(self, event_type, handler):
        handlers = self._handlers.setdefault(event_type, [])
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(self, event_type, handler):
        handlers = self._handlers.get(event_type)
        if not handlers:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return
        if not handlers:
            del self._handlers[event_type]

    def publish(self, event):
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except Exception:
                pass
