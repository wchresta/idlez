import abc
import dataclasses
from typing import Literal

from idlez.store import Experience, Player as _Player, PlayerId

ALL_PLAYERS = "ALL_PLAYERS"

EffectTarget = PlayerId | Literal["ALL_PLAYERS"]

Name = str


class Component(abc.ABC):
    def message_fields(self) -> dict[str, str | int | float]:
        return {}

    def player_message_fields(
        self, player_id: PlayerId
    ) -> dict[str, str | int | float]:
        return {}


class Input(Component):
    pass


@dataclasses.dataclass
class Player(Input):
    player: _Player

    def message_fields(self) -> dict[str, str | int | float]:
        return {
            "player_id": self.player.id,
            "player_name": self.player.name,
        }


@dataclasses.dataclass
class OtherPlayer(Input):
    player: _Player

    def message_fields(self) -> dict[str, str | int | float]:
        return {
            "other_player_id": self.player.id,
            "other_player_name": self.player.name,
        }


@dataclasses.dataclass
class ExpDiff(Component):
    exp_diffs: dict[EffectTarget, Experience]

    def message_fields(self) -> dict[str, str | int | float]:
        all_exp_diff = self.exp_diffs.get(ALL_PLAYERS, 0)
        if all_exp_diff:
            return {"all_exp_diff": all_exp_diff}
        return {}

    def player_message_fields(
        self, player_id: PlayerId
    ) -> dict[str, str | int | float]:
        all_exp_diff = self.exp_diffs.get(ALL_PLAYERS, 0)
        player_exp_diff = self.exp_diffs.get(player_id, 0) + all_exp_diff
        if player_exp_diff:
            return {
                "player_exp_diff": player_exp_diff,
            }
        return {}


@dataclasses.dataclass
class ExpProgress(Component):
    exp_progress: dict[EffectTarget, float]

    def message_fields(self) -> dict[str, str | int | float]:
        all_exp_progress = self.exp_progress.get(ALL_PLAYERS, 0)
        if all_exp_progress:
            return {"all_exp_progress": all_exp_progress}
        return {}

    def player_message_fields(
        self, player_id: PlayerId
    ) -> dict[str, str | int | float]:
        all_exp_progress = self.exp_progress.get(ALL_PLAYERS, 0)
        player_exp_progress = self.exp_progress.get(player_id, 0) + all_exp_progress
        if player_exp_progress:
            return {
                "player_exp_progress": player_exp_progress,
            }
        return {}


@dataclasses.dataclass
class FightResult(Component):
    player_wins: bool


@dataclasses.dataclass
class EventMessage(Component):
    message: str


class NoSuchComponentError(Exception):
    pass
