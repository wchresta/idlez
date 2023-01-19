import dataclasses

from idlez.store import Player as _Player

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
class AllPlayerExpLoss(Input):
    exp_loss: ExpLossType


class NoSuchComponentError(Exception):
    pass
