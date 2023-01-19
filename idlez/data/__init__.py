import abc
from re import findall
import dataclasses
import collections
import enum
import json
import importlib.resources
from typing import Any, Callable
import random as _random


class EncounterType(enum.Enum):
    SINGLE_GAIN_RANDOM = "single_gain_random"


class EffectType(enum.Enum):
    GAIN_EXP_ELEMENT_SUM = "gain_exp_element_sum"


class EventType(enum.Enum):
    NEW_PLAYER = "new_player"
    LEVEL_UP = "level_up"
    LOUD_NOISE = "loud_noise"


class Element(abc.ABC):
    def format_map(self) -> dict[str, str | int | float]:
        return dict()


@dataclasses.dataclass(frozen=True, slots=True)
class Loot(Element):
    a_loot: str
    category: str
    worth: float

    def format_map(self) -> dict[str, str | int | float]:
        return {"a_loot": self.a_loot, "loot_category": self.category}


@dataclasses.dataclass(frozen=True, slots=True)
class Crate(Element):
    in_crate: str
    worth: float

    def format_map(self) -> dict[str, str | int | float]:
        return {"in_crate": self.in_crate}


@dataclasses.dataclass(frozen=True, slots=True)
class BodyCrate:
    on_body: str
    worth: float

    def format_map(self) -> dict[str, str | int | float]:
        return {"on_body": self.on_body}


@dataclasses.dataclass(frozen=True, slots=True)
class SingleGainRandomEncounter:
    effect: EffectType
    elements: list[str]
    message: str
    type: EncounterType = EncounterType.SINGLE_GAIN_RANDOM

    @staticmethod
    def from_dict(edict: dict[str, Any]) -> "SingleGainRandomEncounter":
        return SingleGainRandomEncounter(
            effect=EffectType(edict["effect"]),
            elements=edict["elements"],
            message=edict["message"],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerFight:
    success_message: str
    fail_message: str

    @staticmethod
    def from_dict(edict: dict[str, Any]) -> "PlayerFight":
        return PlayerFight(
            success_message=edict["success_message"],
            fail_message=edict["fail_message"],
        )


EventMessages = dict[str, list[str]]


@dataclasses.dataclass(frozen=True, slots=True)
class Elements:
    loot: list[Loot]
    crate: list[Crate]
    body_crate: list[BodyCrate]

    @staticmethod
    def from_dict(edict: dict[str, Any]) -> "Elements":
        return Elements(
            loot=[Loot(**l) for l in edict["loot"]],
            crate=[Crate(**c) for c in edict["crate"]],
            body_crate=[BodyCrate(**b) for b in edict["body_crate"]],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Encounters:
    single_gain_random: list[SingleGainRandomEncounter]
    player_fight: list[PlayerFight]

    @staticmethod
    def from_dict(edict: dict[str, Any]) -> "Encounters":
        return Encounters(
            single_gain_random=[
                SingleGainRandomEncounter.from_dict(d)
                for d in edict["single_gain_random"]
            ],
            player_fight=[PlayerFight.from_dict(d) for d in edict["player_fight"]],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Data:
    event_messages: EventMessages
    elements: Elements
    encounters: Encounters

    @staticmethod
    def from_lib_resources() -> "Data":
        def load(file: str) -> dict[str, Any]:
            return json.loads(importlib.resources.read_text("idlez.data", file))

        return Data(
            event_messages=load("event_messages.json"),
            elements=Elements.from_dict(load("elements.json")),
            encounters=Encounters.from_dict(load("encounters.json")),
        )


@dataclasses.dataclass(frozen=True, slots=True)
class PickedSingleEncounter:
    message: str
    worth: float


@dataclasses.dataclass(frozen=True, slots=True)
class DataPicker:
    data: Data
    random: _random.Random = dataclasses.field(default_factory=_random.Random)

    def pick_element(self, element: str) -> Loot | Crate | BodyCrate:
        if element == "loot":
            return self.random.choice(self.data.elements.loot)
        if element == "crate":
            return self.random.choice(self.data.elements.crate)
        if element == "body_crate":
            return self.random.choice(self.data.elements.body_crate)
        raise NotImplementedError(element)

    def pick_single_encounter(self) -> PickedSingleEncounter:
        enc: SingleGainRandomEncounter = self.random.choice(
            self.data.encounters.single_gain_random
        )
        chosen_elements = {elem: self.pick_element(elem) for elem in enc.elements}

        combined_format_map = dict(
            player_name="{player_name}",
            time_gain="{time_gain}",
            **collections.ChainMap(*(e.format_map() for e in chosen_elements.values()))
        )
        combined_worth = sum(e.worth for e in chosen_elements.values()) / len(
            chosen_elements
        )

        message = eval_template(enc.message, combined_format_map)

        return PickedSingleEncounter(
            message=message,
            worth=combined_worth,
        )

    def fill_event_message(self, type: EventType, params: dict[str, str | int]) -> str:
        ts = self.data.event_messages[type.value]
        t = self.random.choice(ts)
        return eval_template(t, params)

    def fill_player_fight_message(
        self, player_wins: bool, params: dict[str, str | int]
    ) -> str:
        ts = self.data.encounters.player_fight
        t = self.random.choice(ts)
        if player_wins:
            return eval_template(t.success_message, params)
        return eval_template(t.fail_message, params)


TEMPLATE_FORMATTERS: dict[str, Callable[[str], str]] = {
    "capitalize": str.capitalize,
    "upper": str.upper,
    "lower": str.lower,
}


def eval_template(template: str, params: dict[str, str] | dict[str, str | int]) -> str:
    form_params = params.copy()
    for ident_fmt in findall(r"\{([^|}]+\|[^|}]+)\}", template):
        ident, fmt = ident_fmt.split("|")
        value = params.get(ident)
        if value is None:
            continue
        formatter = TEMPLATE_FORMATTERS.get(fmt)
        if formatter is None:
            continue
        form_params[ident_fmt] = formatter(str(value))
    return template.format_map(form_params)
