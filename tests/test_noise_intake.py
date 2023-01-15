import pytest
import asyncio
from unittest import mock
import dataclasses
import random as _random
import json
from idlez import events
from idlez.data import (
    Data,
    Elements,
    Loot,
    BodyCrate,
    Crate,
    Encounters,
    SingleGainRandomEncounter,
    EffectType,
    EncounterType,
)
from idlez.bot import IdleZBot
from idlez.game import IdleZ, NoiseType
from idlez.store import Store, Player

GUILD_ID = 10
EXP_FOR_LVL_2 = 1121


def make_player(exp, lvl):
    return Player(id=1, name="player1", experience=exp, level=lvl, guild_id=GUILD_ID)


@pytest.mark.parametrize(
    "randint,random,want_evt,want_exp",
    [
        (
            [28],
            [0.01, 0.2],
            events.BadPlayerEvent(
                make_player(1200 - 28 - int((1200 - 28 - EXP_FOR_LVL_2) * 0.2), 2),
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
    store = Store({1: make_player(1200, 2)})
    game = IdleZ(
        store=store, data=None, event_queue=[], event_handlers=[], random=fake_random
    )

    game.make_noise(NoiseType.SPEAK, 1, "Someone said something")

    assert store.players[1].experience == want_exp
    assert game.event_queue == [want_evt]


@pytest.mark.parametrize(
    "random,want_evt,want_exp",
    [
        (
            [0.01],
            events.SinglePlayerEvent(
                make_player(1000 + int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2), 1),
                "{player_name} a_loot in_crate on_body {time_gain}",
                gain_amount=int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2),
            ),
            1000 + int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2),
        ),
    ],
)
def test_single_player_encounter(random, want_evt, want_exp):
    fake_random = mock.Mock(
        spec=_random.Random,
        random=mock.Mock(side_effect=random),
        choice=mock.Mock(side_effect=lambda xs: list(xs)[0]),
    )
    store = Store({1: make_player(1000, 1)})
    data = Data(
        event_messages=None,
        elements=Elements(
            loot=[Loot(a_loot="a_loot", category="category", worth=0.2)],
            body_crate=[BodyCrate(on_body="on_body", worth=0.3)],
            crate=[Crate(in_crate="in_crate", worth=0.1)],
        ),
        encounters=Encounters(
            single_gain_random=[
                SingleGainRandomEncounter(
                    effect=EffectType.GAIN_EXP_ELEMENT_SUM,
                    elements=["loot", "body_crate", "crate"],
                    message="{player_name} {a_loot} {in_crate} {on_body} {time_gain}",
                )
            ]
        ),
    )
    game = IdleZ(
        store=store, data=data, event_queue=[], event_handlers=[], random=fake_random
    )

    game.single_player_event()

    assert store.players[1].experience == want_exp
    assert game.event_queue == [want_evt]
