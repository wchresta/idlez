import abc
import dataclasses
from typing import Optional, Type, TypeVar

from idlez.store import Player
import idlez.events.components as _components

_C = TypeVar("_C", bound=_components.Component)


class Event:
    pass


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
class TwoPlayerEvent(PlayerEvent):
    other_player: Player


@dataclasses.dataclass
class PlayerFightEvent(TwoPlayerEvent):
    player_wins: bool
    player_exp_diff_amount: int
    other_player_exp_diff_amount: int


@dataclasses.dataclass(slots=True)
class ComponentEvent(abc.ABC, Event):
    needs_components: list[Type[_components.Component]]
    components: dict[Type[_components.Component], _components.Component]

    def __init__(self, *comps: _components.Component) -> None:
        self.components = {}
        for c in comps:
            self.components[c.__class__] = c

    def safe_component(self, t: Type[_C]) -> Optional[_C]:
        return self.components.get(t)  # type: ignore

    def component(self, t: Type[_C]) -> _C:
        c = self.safe_component(t)
        if c is None:
            raise _components.NoSuchComponentError(
                f"{__name__} does not have component {t}"
            )
        return c

    def has_component(self, t: Type[_C]) -> bool:
        return t in self.components


class PlayerNoiseEvent(ComponentEvent):
    needs_components = [_components.Player, _components.AllPlayerExpLoss]


class NewPlayerEvent(ComponentEvent):
    needs_components = [_components.Player, _components.AllPlayerExpLoss]
