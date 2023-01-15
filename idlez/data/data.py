import dataclasses
import collections
import enum
import json
import importlib.resources
from typing import Mapping
import random as _random
from idlez.store import PlayerId


class EncounterType(enum.Enum):
    SINGLE_GAIN_RANDOM = "single_gain_random"


class EffectType(enum.Enum):
    GAIN_EXP_ELEMENT_SUM = "gain_exp_element_sum"


class EventType(enum.Enum):
    NEW_PLAYER = "new_player"
    LEVEL_UP = "level_up"
    LOUD_NOISE = "loud_noise"


@dataclasses.dataclass(frozen=True, slots=True)
class Loot:
    a_loot: str
    category: str
    worth: float

    def format_map(self):
        return {"a_loot": self.a_loot, "loot_category": self.category}


@dataclasses.dataclass(frozen=True, slots=True)
class Crate:
    in_crate: str
    worth: float

    def format_map(self):
        return {"in_crate": self.in_crate}


@dataclasses.dataclass(frozen=True, slots=True)
class BodyCrate:
    on_body: str
    worth: float

    def format_map(self):
        return {"on_body": self.on_body}


@dataclasses.dataclass(frozen=True, slots=True)
class SingleGainRandomEncounter:
    effect: EffectType
    elements: list[str]
    message: str
    type: EncounterType = EncounterType.SINGLE_GAIN_RANDOM

    @staticmethod
    def from_dict(edict: dict) -> "SingleGainRandomEncounter":
        return SingleGainRandomEncounter(
            effect=EffectType(edict["effect"]),
            elements=edict["elements"],
            message=edict["message"],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class EventMessages:
    event_messages: dict[str, list[str]]


@dataclasses.dataclass(frozen=True, slots=True)
class Elements:
    loot: list[Loot]
    crate: list[Crate]
    body_crate: list[BodyCrate]

    @staticmethod
    def from_dict(edict: dict) -> "Elements":
        return Elements(
            loot=[Loot(**l) for l in edict["loot"]],
            crate=[Crate(**c) for c in edict["crate"]],
            body_crate=[BodyCrate(**b) for b in edict["body_crate"]],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Encounters:
    single_gain_random: list[SingleGainRandomEncounter]

    def from_dict(edict: dict) -> "Encounters":
        return Encounters(
            single_gain_random=[
                SingleGainRandomEncounter.from_dict(d)
                for d in edict["single_gain_random"]
            ],
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Data:
    event_messages: EventMessages
    elements: Elements
    encounters: Encounters

    @staticmethod
    def from_lib_resources() -> "Data":
        def load(file):
            return json.loads(importlib.resources.read_text("idlez.data", file))

        return Data(
            EventMessages(load("event_messages.json")),
            Elements.from_dict(load("elements.json")),
            Encounters.from_dict(load("encounters.json")),
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

        message = enc.message.format_map(combined_format_map)

        return PickedSingleEncounter(
            message=message,
            worth=combined_worth,
        )

    def fill_event_message(self, type: EventType, params: Mapping[str, str | int]):
        ts = self.data.event_messages[type.value]
        t = self.random.choice(ts)
        return t.format_map(params)
