import dataclasses
import enum

from idlez.store import Player


class EventType(enum.Enum):
    LOUD_NOISE = 1


class Event:
    pass


@dataclasses.dataclass
class PlayerEvent(Event):
    player: Player


class LevelUpEvent(PlayerEvent):
    pass


@dataclasses.dataclass
class BadPlayerEvent(PlayerEvent):
    event_type: EventType
    exp_loss: int


class NewPlayerEvent(BadPlayerEvent):
    def __init__(self, player: Player, exp_loss: int):
        self.player = player
        self.event_type = EventType.LOUD_NOISE
        self.exp_loss = exp_loss
