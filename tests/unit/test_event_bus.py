from dataclasses import dataclass

from bus.event_bus import EventBus


@dataclass(frozen=True)
class _AlphaEvent:
    value: int


@dataclass(frozen=True)
class _BetaEvent:
    value: int


def test_subscriber_receives_matching_event_once():
    bus = EventBus()
    received = []

    bus.subscribe(_AlphaEvent, received.append)
    event = _AlphaEvent(1)
    bus.publish(event)

    assert received == [event]


def test_other_event_type_is_not_delivered():
    bus = EventBus()
    received = []

    bus.subscribe(_AlphaEvent, received.append)
    bus.publish(_BetaEvent(2))

    assert received == []


def test_multiple_subscribers_receive_same_event():
    bus = EventBus()
    first = []
    second = []
    event = _AlphaEvent(3)

    bus.subscribe(_AlphaEvent, first.append)
    bus.subscribe(_AlphaEvent, second.append)
    bus.publish(event)

    assert first == [event]
    assert second == [event]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received = []

    bus.subscribe(_AlphaEvent, received.append)
    bus.unsubscribe(_AlphaEvent, received.append)
    bus.publish(_AlphaEvent(4))

    assert received == []


def test_duplicate_subscribe_does_not_double_notify():
    bus = EventBus()
    received = []

    bus.subscribe(_AlphaEvent, received.append)
    bus.subscribe(_AlphaEvent, received.append)
    bus.publish(_AlphaEvent(5))

    assert len(received) == 1


def test_failing_subscriber_does_not_block_others():
    bus = EventBus()
    received = []

    def boom(_event):
        raise RuntimeError("subscriber failed")

    bus.subscribe(_AlphaEvent, boom)
    bus.subscribe(_AlphaEvent, received.append)
    bus.publish(_AlphaEvent(6))

    assert received == [_AlphaEvent(6)]


def test_publish_with_no_subscribers_is_safe():
    bus = EventBus()
    bus.publish(_AlphaEvent(7))
