import dataclasses
from typing import Any, Optional, Callable
import enum
import asyncio
import random

from idlez import events
from idlez.store import Player, Store


class IdleZError(Exception):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerNotFound(IdleZError):
    player_id: int


class NoiseType(enum.Enum):
    SPEAK = 1


@dataclasses.dataclass
class Emitter:
    event_handlers: list[Callable[[events.Event], Any]]
    event_queue: list[events.Event]

    def emit(self, evt: events.Event) -> None:
        self.event_queue.append(evt)

    async def send_events(self):
        for evt in self.event_queue:
            for handler in self.event_handlers:
                if asyncio.iscoroutinefunction(handler):
                    await handler(evt)
                else:
                    handler(evt)
        self.event_queue.clear()

    def register_handler(self, handler: Callable[[events.Event], Any]):
        self.event_handlers.append(handler)


@dataclasses.dataclass
class IdleZ(Emitter):
    store: Store

    def player(self, uid: int) -> Optional[Player]:
        return self.store.players.get(uid)

    def make_noise(self, noise_type: NoiseType, player_id: int, message: str) -> None:
        player = self.player(player_id)
        if not player:
            raise PlayerNotFound(player_id=player_id)
        player.experience -= player.level

        if random.random() < 0.05:
            self.all_lose_experience(5600)
            self.emit(
                events.BadPlayerEvent(
                    player=player, event_type=events.EventType.LOUD_NOISE, exp_loss=5600
                )
            )

    def new_player(self, player: Player) -> None:
        self.store.players[player.id] = player

        # Everyone loses experience if a new player joins
        self.all_lose_experience(1200)

        self.emit(events.NewPlayerEvent(player, exp_loss=1200))

    def all_lose_experience(self, amount: int) -> None:
        for player_id in self.store.players:
            self.lose_experience(player_id=player_id, amount=amount)

    def gain_experience(self, player_id: int, amount: int) -> None:
        player = self.player(player_id)
        player.experience += amount

        if self.experience_for_level(player.level + 1) <= player.experience:
            self.level_up(player.id)

    def level_up(self, player_id):
        player = self.player(player_id)
        player.level += 1

        self.emit(events.LevelUpEvent(player))

    def lose_experience(self, player_id: int, amount: int) -> None:
        self.player(player_id).experience -= amount

    async def tick(self, seconds_diff: int) -> None:
        for player in self.store.players.values():
            self.gain_experience(player.id, seconds_diff)
        await self.send_events()

    @staticmethod
    def experience_for_level(lvl: int) -> int:
        base = 6000  # 10 minutes
        step = 1.16
        if lvl <= 60:
            return base * step**lvl
        return base * step**60 + (864000 * (lvl - 60))
