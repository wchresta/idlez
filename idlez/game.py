import dataclasses
import math
from typing import Any, Optional, Callable
import enum
import asyncio
import random as _random

from idlez import data as _data
import idlez.events as events
import idlez.events.components as components
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
    data: _data.Data

    data_picker: _data.DataPicker = dataclasses.field(init=False)
    player_idle_state_callback: Callable[
        [PlayerId, GuildId], IdleState
    ] = lambda _p, _g: IdleState.ONLINE

    random: _random.Random = dataclasses.field(default_factory=_random.Random)
    _exp_for_level: dict[Level, Experience] = dataclasses.field(
        default_factory=dict, init=False
    )

    def __post_init__(self):
        self.data_picker = _data.DataPicker(self.data)

    async def tick(self, seconds_diff: int) -> None:
        for player in self.store.players.values():
            self.gain_experience(player.id, seconds_diff)

        # Once every 30 minutes, 1 player event
        # Once every hour, 2 player event
        if self.random.random() < float(seconds_diff) / 1800.0:
            self.single_player_event()
        elif self.random.random() < float(seconds_diff) / 3600.0:
            self.two_player_event()

        await self.send_events()

    def player(self, player_id: PlayerId) -> Optional[Player]:
        return self.store.players.get(player_id)

    def online_players(self) -> list[Player]:
        on_players: list[Player] = []
        for p in self.store.players.values():
            idle_state = self.player_idle_state_callback(p.id, p.guild_id)
            if idle_state in [IdleState.ONLINE, IdleState.AWAY]:
                on_players.append(p)
        return on_players

    def make_noise(self, player_id: PlayerId) -> None:
        player = self.player(player_id)
        if not player:
            raise PlayerNotFound(player_id=player_id)
        exp_for_next_lvl = self.experience_for_next_level(player_id)
        if exp_for_next_lvl is not None:
            player.experience -= self.random.randint(1, exp_for_next_lvl)

        if self.random.random() < 0.05:
            progress_percent = self.random.random()
            self.all_lose_progress(progress_percent)

            self.emit(
                events.PlayerNoiseEvent(
                    components.Player(player=player),
                    components.AllPlayerExpLoss(
                        exp_loss=components.ExpLossProgress(progress_percent)
                    ),
                )
            )

    def single_player_event(self) -> None:
        on_players = self.online_players()
        if len(on_players) <= 0:
            return
        player = self.random.choice(on_players)
        picked = self.data_picker.pick_single_encounter()
        amount = self.gain_progress(player.id, 0.3 * picked.worth)

        if amount > 0:
            self.emit(
                events.SinglePlayerEvent(
                    components.Player(player=player),
                    components.ExpEffect(exp_diffs={player.id: amount}),
                    components.EventMessage(message=picked.message),
                )
            )

    def two_player_event(self) -> None:
        on_players = self.online_players()
        if len(on_players) <= 0:
            return
        player = self.random.choice(on_players)

        other_player = self.random.choice(
            [p for p in self.store.players.values() if p != player]
        )

        # Half the time, switch online player with maybe offline player
        if self.random.random() > 0.5:
            player, other_player = other_player, player

        success = self.random.random() * player.level > other_player.level / 2

        # >1 if player has more experience than other_player
        player_percent_diff = player.experience / other_player.experience
        other_player_percent_diff = 1 / player_percent_diff

        if success:
            if player.experience > other_player.experience:
                # Player won, while being the better player
                # player_percent_diff > 1, other_player_percent_diff < 1
                player_scale = max(2 - player_percent_diff, 0)
                other_player_scale = other_player_percent_diff
            else:
                # Player won while being the weaker player
                # player_percent_diff < 1, other_player_percent_diff > 1
                player_scale = 2 - player_percent_diff
                other_player_scale = other_player_percent_diff

            player_exp_diff_amount = self.gain_progress(
                player.id, 0.1 + player_scale * self.random.random() / 5
            )
            other_player_exp_diff_amount = self.lose_progress(
                other_player.id, 0.1 + other_player_scale * self.random.random() / 5
            )
        else:
            if player.experience > other_player.experience:
                # Player lost, while being the better player
                # player_percent_diff > 1, other_player_percent_diff < 1
                player_scale = player_percent_diff
                other_player_scale = max(2 - other_player_percent_diff, 0)
            else:
                # Player lost while being the weaker player
                # player_percent_diff < 1, other_player_percent_diff > 1
                player_scale = player_percent_diff
                other_player_scale = 2 - other_player_percent_diff

            player_exp_diff_amount = self.lose_progress(
                player.id, 0.1 + player_scale * self.random.random() / 5
            )
            other_player_exp_diff_amount = self.gain_progress(
                other_player.id, 0.1 + other_player_scale * self.random.random() / 5
            )

        self.emit(
            events.PlayerFightEvent(
                components.Player(player=player),
                components.OtherPlayer(player=other_player),
                components.FightResult(player_wins=success),
                components.ExpEffect(
                    exp_diffs={
                        player.id: player_exp_diff_amount,
                        other_player.id: other_player_exp_diff_amount,
                    },
                ),
            )
        )

    def new_player(self, player: Player) -> None:
        self.store.players[player.id] = player

        # Everyone loses experience if a new player joins
        progress_percent = self.random.random() / 2
        self.all_lose_progress(progress_percent)

        self.emit(
            events.NewPlayerEvent(
                components.Player(player=player),
                components.AllPlayerExpLoss(
                    exp_loss=components.ExpLossProgress(progress_percent)
                ),
            )
        )

    def all_gain_experience(self, amount: Experience) -> None:
        for player_id in self.store.players:
            self.gain_experience(player_id=player_id, amount=amount)

    def all_lose_progress(self, percent: float) -> None:
        for player_id in self.store.players:
            self.lose_progress(player_id, percent)

    def lose_progress(self, player_id: PlayerId, percent: float) -> Experience:
        level_progress = self.level_progress(player_id)
        if level_progress is None:
            return 0
        amount = -int(percent * level_progress)
        if not amount < 0:
            return 0
        self.gain_experience(player_id=player_id, amount=amount)
        return amount

    def gain_experience(
        self,
        player_id: PlayerId,
        amount: Experience,
        gain_offline_experience: bool = False,
    ) -> None:
        player = self.player(player_id)
        if not player:
            return

        if amount < 0:
            # Player is going to lose experience
            lower_bound = self.experience_for_level(player.level)
            # Do not lose more experience than experience need for the current level
            player.experience = max(lower_bound, player.experience + amount)
            return

        idle_state = self.player_idle_state_callback(player_id, player.guild_id)
        if not gain_offline_experience and idle_state == IdleState.OFFLINE:
            return

        if idle_state == IdleState.ONLINE:
            player.experience += amount
        else:
            player.experience += self.random.randint(0, amount)

        if self.experience_for_level(player.level + 1) <= player.experience:
            self.level_up(player.id)

    def gain_progress(self, player_id: PlayerId, percent: float) -> Experience:
        player = self.player(player_id)
        if not player:
            return 0

        next_exp = self.experience_for_next_level(player_id)
        if next_exp is None:
            return 0
        amount = int(percent * next_exp)
        if not amount > 0:
            return 0

        self.gain_experience(player_id, amount)
        return amount

    def level_up(self, player_id: PlayerId) -> None:
        player = self.player(player_id)
        if not player:
            return
        player.level += 1

        self.emit(events.LevelUpEvent(components.Player(player=player)))

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
