import abc
import dataclasses
from typing import Optional, Type, TypeVar

import idlez.events.components as _components

_C = TypeVar("_C", bound=_components.Component)


class Event:
    pass


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
    needs_components = [_components.Player, _components.ExpProgress]


class NewPlayerEvent(ComponentEvent):
    needs_components = [_components.Player, _components.ExpProgress]


class LevelUpEvent(ComponentEvent):
    needs_components = [_components.Player]


class SinglePlayerEvent(ComponentEvent):
    needs_components = [_components.Player, _components.ExpDiff]


class PlayerFightEvent(ComponentEvent):
    needs_components = [
        _components.Player,
        _components.OtherPlayer,
        _components.FightResult,
        _components.ExpDiff,
    ]
