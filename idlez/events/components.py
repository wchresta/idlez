import dataclasses

from idlez.store import Experience, Player as _Player, PlayerId

Name = str


class ExpLossType:
    pass


@dataclasses.dataclass
class ExpLossFix(ExpLossType):
    loss_amount: int


@dataclasses.dataclass
class ExpLossProgress(ExpLossType):
    loss_percent: float


class Component:
    pass


class Input(Component):
    pass


@dataclasses.dataclass
class Player(Input):
    player: _Player


@dataclasses.dataclass
class OtherPlayer(Input):
    player: _Player


@dataclasses.dataclass
class AllPlayerExpLoss(Component):
    exp_loss: ExpLossType


@dataclasses.dataclass
class ExpEffect(Component):
    exp_diffs: dict[PlayerId, Experience]


@dataclasses.dataclass
class FightResult(Component):
    player_wins: bool


@dataclasses.dataclass
class EventMessage(Component):
    message: str


class NoSuchComponentError(Exception):
    pass
