import pytest
import asyncio
import discord
from unittest import mock
import dataclasses
import random
import json
from idlez import events
from idlez.bot import IdleZBot, Template
from idlez.game import IdleZ
from idlez.store import Player

GUILD_ID = 10
PLAYER_1 = Player(id=1, name="player1", experience=1000, level=2, guild_id=GUILD_ID)


@dataclasses.dataclass
class NoiseTestCase:
    event: events.Event
    want: str


@pytest.mark.parametrize(
    "test_case",
    [
        NoiseTestCase(
            event=events.BadPlayerEvent(
                PLAYER_1, events.EventType.LOUD_NOISE, events.ExpLossFix(300)
            ),
            want="loud noise; player_name=player1, exp_loss=300",
        ),
        NoiseTestCase(
            event=events.BadPlayerEvent(
                PLAYER_1, events.EventType.LOUD_NOISE, events.ExpLossProgress(0.1)
            ),
            want="loud noise; player_name=player1, exp_loss=almost no",
        ),
        NoiseTestCase(
            event=events.BadPlayerEvent(
                PLAYER_1, events.EventType.LOUD_NOISE, events.ExpLossProgress(0.999)
            ),
            want="loud noise; player_name=player1, exp_loss=all",
        ),
        NoiseTestCase(
            event=events.BadPlayerEvent(
                PLAYER_1, events.EventType.LOUD_NOISE, events.ExpLossProgress(0.55)
            ),
            want="loud noise; player_name=player1, exp_loss=a lot of",
        ),
        NoiseTestCase(
            event=events.NewPlayerEvent(PLAYER_1, events.ExpLossFix(300)),
            want="new player; player_name=player1, exp_loss=300",
        ),
        NoiseTestCase(
            event=events.NewPlayerEvent(PLAYER_1, events.ExpLossProgress(0.3)),
            want="new player; player_name=player1, exp_loss=some",
        ),
        NoiseTestCase(
            event=events.LevelUpEvent(PLAYER_1),
            want="level up; player_name=player1, ttl=16 minutes, 47 seconds",
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
    ],
)
def test_noise(test_case):
    templates = {
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
    templ = Template(templates)
    game = IdleZ(store=None, event_queue=[], event_handlers=[])

    channel = mock.Mock(send=mock.AsyncMock(spec=discord.TextChannel.send))
    bot = IdleZBot(game=game, intents=None, store_path=None, template=templ)
    bot.channel = {GUILD_ID: channel}

    asyncio.run(bot.on_game_event(test_case.event))
    channel.send.assert_awaited_once_with(test_case.want)
