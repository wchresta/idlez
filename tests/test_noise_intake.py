import pytest
import asyncio
from unittest import mock
import dataclasses
import random as _random
import json
from idlez import events
from idlez.bot import IdleZBot, Template
from idlez.game import IdleZ, NoiseType
from idlez.store import Store, Player

GUILD_ID = 10
EXP_FOR_LVL_2 = 1121


def make_player(exp):
    return Player(id=1, name="player1", experience=exp, level=2, guild_id=GUILD_ID)


@pytest.mark.parametrize(
    "randint,random,want_evt,want_exp",
    [
        (
            [28],
            [0.01, 0.2],
            events.BadPlayerEvent(
                make_player(1200 - 28 - int((1200 - 28 - EXP_FOR_LVL_2) * 0.2)),
                events.EventType.LOUD_NOISE,
                events.ExpLossProgress(0.2),
            ),
            1200 - 28 - int((1200 - 28 - EXP_FOR_LVL_2) * 0.2),
        ),
    ],
)
def test_noise_intake(randint, random, want_evt, want_exp):
    fake_random = mock.Mock(
        spec=_random.Random,
        randint=mock.Mock(side_effect=randint),
        random=mock.Mock(side_effect=random),
    )
    store = Store({1: make_player(1200)})
    game = IdleZ(store=store, event_queue=[], event_handlers=[], random=fake_random)

    game.make_noise(NoiseType.SPEAK, 1, "Someone said something")

    assert store.players[1].experience == want_exp
    assert game.event_queue == [want_evt]
