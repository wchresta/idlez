import pytest
import asyncio
import discord
from unittest import mock
import dataclasses
import idlez.events as events
import idlez.events.components as components
from idlez.bot import IdleZBot
from idlez.data import Data
from idlez.game import IdleZ
from idlez.store import Player

GUILD_ID = 10
PLAYER_1 = Player(id=1, name="player1", experience=1000, level=2, guild_id=GUILD_ID)


@dataclasses.dataclass
class NoiseTestCase:
    event: events.Event
    want: str


def make_noise(loss: components.ExpLossType):
    return events.PlayerNoiseEvent(
        components.Player(PLAYER_1),
        components.AllPlayerExpLoss(loss),
    )


def make_np(loss: components.ExpLossType):
    return events.NewPlayerEvent(
        components.Player(PLAYER_1),
        components.AllPlayerExpLoss(loss),
    )


@pytest.mark.parametrize(
    "test_case",
    [
        NoiseTestCase(
            event=make_noise(components.ExpLossFix(300)),
            want="loud noise; player_name=player1, exp_loss=300",
        ),
        NoiseTestCase(
            event=make_noise(components.ExpLossProgress(0.1)),
            want="loud noise; player_name=player1, exp_loss=almost no",
        ),
        NoiseTestCase(
            event=make_noise(components.ExpLossProgress(0.999)),
            want="loud noise; player_name=player1, exp_loss=all",
        ),
        NoiseTestCase(
            event=make_noise(components.ExpLossProgress(0.55)),
            want="loud noise; player_name=player1, exp_loss=a lot of",
        ),
        NoiseTestCase(
            event=make_np(components.ExpLossFix(300)),
            want="new player; player_name=player1, exp_loss=300",
        ),
        NoiseTestCase(
            event=make_np(components.ExpLossProgress(0.3)),
            want="new player; player_name=player1, exp_loss=some",
        ),
        NoiseTestCase(
            event=events.LevelUpEvent(components.Player(player=PLAYER_1)),
            want="level up; player_name=player1, ttl=16 minutes, 47 seconds",
        ),
        NoiseTestCase(
            event=events.SinglePlayerEvent(
                components.Player(player=PLAYER_1),
                components.ExpEffect(exp_diffs={PLAYER_1.id: 300}),
                components.EventMessage(
                    message="single player {player_name}, time_gain={time_gain}"
                ),
            ),
            want="single player player1, time_gain=5 minutes",
        ),
    ],
    ids=[
        "noise, exp_loss=300",
        "noise, exp_loss=almost no",
        "noise, exp_loss=all",
        "noise, exp_loss=a lot of",
        "new player, exp_loss=300",
        "new player, exp_loss=some",
        "level up, new_level=3, ttl=3000",
        "single_player_event",
    ],
)
def test_noise(test_case: NoiseTestCase):
    event_messages = {
        "loud_noise": [
            "loud noise; player_name={player_name}, exp_loss={exp_loss}",
        ],
        "new_player": [
            "new player; player_name={player_name}, exp_loss={exp_loss}",
        ],
        "level_up": [
            "level up; player_name={player_name}, ttl={ttl}",
        ],
    }
    data = Data(event_messages=event_messages, elements=None, encounters=None)  # type: ignore
    game = IdleZ(store=None, data=data, event_queue=[], event_handlers=[])  # type: ignore

    channel = mock.Mock(send=mock.AsyncMock(spec=discord.TextChannel.send))  # type: ignore
    bot = IdleZBot(game=game, intents=None, store_path=None, data=data)  # type: ignore
    bot.channel = {GUILD_ID: channel}

    asyncio.run(bot.on_game_event(test_case.event))
    channel.send.assert_awaited_once_with(test_case.want)  # type: ignore
