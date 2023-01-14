import dataclasses
import math
from typing import Any, Optional, Callable
import enum
import asyncio
import random as _random

from idlez import events
from idlez.store import Player, Store, PlayerId, Level, Experience, GuildId


class IdleZError(Exception):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerNotFound(IdleZError):
    player_id: PlayerId


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


class IdleState(enum.Enum):
    ONLINE = 1
    AWAY = 2
    OFFLINE = 3


@dataclasses.dataclass
class IdleZ(Emitter):
    store: Store
    player_idle_state_callback: Callable[
        [PlayerId, GuildId], IdleState
    ] = lambda _p, _g: IdleState.ONLINE
    random: _random.Random = dataclasses.field(default_factory=_random.Random)

    _exp_for_level: dict[Level, Experience] = dataclasses.field(
        default_factory=dict, init=False
    )

    def player(self, player_id: PlayerId) -> Optional[Player]:
        return self.store.players.get(player_id)

    def make_noise(
        self, noise_type: NoiseType, player_id: PlayerId, message: str
    ) -> None:
        player = self.player(player_id)
        if not player:
            raise PlayerNotFound(player_id=player_id)
        player.experience -= self.random.randint(
            1, self.experience_for_next_level(player_id)
        )

        if self.random.random() < 0.05:
            progress_percent = self.random.random()
            self.all_lose_progress(progress_percent)

            self.emit(
                events.BadPlayerEvent(
                    player=player,
                    event_type=events.EventType.LOUD_NOISE,
                    exp_loss=events.ExpLossProgress(progress_percent),
                )
            )

    def new_player(self, player: Player) -> None:
        self.store.players[player.id] = player

        # Everyone loses experience if a new player joins
        progress_percent = self.random.random() / 2
        self.all_lose_progress(progress_percent)

        self.emit(
            events.NewPlayerEvent(
                player, exp_loss=events.ExpLossProgress(progress_percent)
            )
        )

    def all_lose_experience(self, amount: Experience) -> None:
        for player_id in self.store.players:
            self.lose_experience(player_id=player_id, amount=amount)

    def all_lose_progress(self, percent: float) -> None:
        for player_id in self.store.players:
            amount = int(percent * self.level_progress(player_id))
            if amount > 0:
                self.lose_experience(player_id=player_id, amount=amount)

    def gain_experience(self, player_id: PlayerId, amount: Experience) -> None:
        player = self.player(player_id)
        if not player:
            return

        idle_state = self.player_idle_state_callback(player_id, player.guild_id)
        if idle_state == IdleState.OFFLINE:
            return

        if idle_state == IdleState.ONLINE:
            player.experience += amount
        else:
            player.experience += random.randint(0, amount)

        if self.experience_for_level(player.level + 1) <= player.experience:
            self.level_up(player.id)

    def level_up(self, player_id: PlayerId) -> None:
        player = self.player(player_id)
        if not player:
            return
        player.level += 1

        self.emit(events.LevelUpEvent(player))

    def lose_experience(self, player_id: PlayerId, amount: Experience) -> None:
        player = self.player(player_id)
        if not player:
            return
        lower_bound = self.experience_for_level(player.level)
        player.experience = max(lower_bound, player.experience - amount)

    async def tick(self, seconds_diff: int) -> None:
        for player in self.store.players.values():
            self.gain_experience(player.id, seconds_diff)
        await self.send_events()

    def level_progress(self, player_id: PlayerId) -> Optional[Experience]:
        player = self.player(player_id)
        if not player:
            return
        return player.experience - self.experience_for_level(player.level)

    def experience_for_next_level(self, player_id: PlayerId) -> Optional[Experience]:
        player = self.player(player_id)
        if not player:
            return
        return self.experience_for_level(player.level + 1) - player.experience

    def experience_for_level(self, lvl: Level) -> Experience:
        base = 600  # 10 minutes

        if lvl == 0:
            return 0
        if lvl == 1:
            return base

        cached = self._exp_for_level.get(lvl)
        if cached is not None:
            return cached

        lower_level_exp = self.experience_for_level(lvl - 1)
        step = 1.05 + math.exp(-lvl / 10)

        return int(lower_level_exp * step)
