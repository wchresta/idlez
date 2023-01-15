import dataclasses
import enum

from idlez.store import Player


class EventType(enum.Enum):
    LOUD_NOISE = 1


class Event:
    pass


class ExpLossType:
    pass


@dataclasses.dataclass
class ExpLossFix(ExpLossType):
    loss_amount: int


@dataclasses.dataclass
class ExpLossProgress(ExpLossType):
    loss_percent: float


@dataclasses.dataclass
class PlayerEvent(Event):
    player: Player


class LevelUpEvent(PlayerEvent):
    pass


@dataclasses.dataclass
class SinglePlayerEvent(PlayerEvent):
    message: str
    gain_amount: int


@dataclasses.dataclass
class BadPlayerEvent(PlayerEvent):
    event_type: EventType
    exp_loss: ExpLossType


class NewPlayerEvent(BadPlayerEvent):
    def __init__(self, player: Player, exp_loss: ExpLossType):
        self.player = player
        self.event_type = EventType.LOUD_NOISE
        self.exp_loss = exp_loss
