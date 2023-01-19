from idlez.data import PlayerFight
import pytest
from unittest import mock
import random as _random
from idlez import events
import idlez.events.components as components
from idlez.data import (
    Data,
    Elements,
    Loot,
    BodyCrate,
    Crate,
    Encounters,
    SingleGainRandomEncounter,
    EffectType,
)
from idlez.game import IdleZ, NoiseType
from idlez.store import Experience, Level, Store, Player

GUILD_ID = 10
EXP_FOR_LVL_2 = 1121


def make_player(id: int, exp: Experience, lvl: Level):
    return Player(
        id=id, name=f"player{id}", experience=exp, level=lvl, guild_id=GUILD_ID
    )


@pytest.mark.parametrize(
    "randint,random,want_evt",
    [
        (
            [28],
            [0.01, 0.2],
            events.PlayerNoiseEvent(
                components.Player(
                    make_player(
                        1, 1200 - 28 - int((1200 - 28 - EXP_FOR_LVL_2) * 0.2), 2
                    )
                ),
                components.AllPlayerExpLoss(components.ExpLossProgress(0.2)),
            ),
        ),
    ],
)
def test_noise_intake(
    randint: list[int],
    random: list[float],
    want_evt: events.Event,
):
    fake_random = mock.Mock(
        spec=_random.Random,
        randint=mock.Mock(side_effect=randint),
        random=mock.Mock(side_effect=random),
    )
    store = Store({1: make_player(1, 1200, 2)})
    game = IdleZ(
        store=store, data=None, event_queue=[], event_handlers=[], random=fake_random  # type: ignore
    )

    game.make_noise(NoiseType.SPEAK, 1, "Someone said something")

    assert game.event_queue == [want_evt]


@pytest.mark.parametrize(
    "random,want_evt,want_exp",
    [
        (
            [0.01],
            events.SinglePlayerEvent(
                make_player(1, 1000 + int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2), 1),
                "{player_name} a_loot in_crate on_body {time_gain}",
                gain_amount=int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2),
            ),
            1000 + int((EXP_FOR_LVL_2 - 1000) * 0.3 * 0.2),
        ),
    ],
)
def test_single_player_encounter(
    random: list[float], want_evt: events.Event, want_exp: Experience
):
    fake_random = mock.Mock(
        spec=_random.Random,
        random=mock.Mock(side_effect=random),
        choice=mock.Mock(side_effect=lambda xs: list(xs)[0]),  # type: ignore
    )
    store = Store({1: make_player(1, 1000, 1)})
    data = Data(
        event_messages=dict(),
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
            ],
            player_fight=[],
        ),
    )
    game = IdleZ(
        store=store, data=data, event_queue=[], event_handlers=[], random=fake_random
    )

    game.single_player_event()

    assert store.players[1].experience == want_exp
    assert game.event_queue == [want_evt]


@pytest.mark.parametrize(
    "random,want_evt",
    [
        (
            [0.0, 0.6, 0.3, 0.3],
            events.PlayerFightEvent(
                player=make_player(1, 1336, 2),
                other_player=make_player(2, 1353, 2),
                player_wins=True,
                player_exp_diff_amount=136,
                other_player_exp_diff_amount=-47,
            ),
        ),
    ],
)
def test_player_fight_event(
    random: list[float],
    want_evt: events.Event,
):
    fake_random = mock.Mock(
        spec=_random.Random,
        random=mock.Mock(side_effect=random),
        choice=mock.Mock(side_effect=lambda xs: list(xs)[0]),  # type: ignore
    )
    store = Store({1: make_player(1, 1200, 2), 2: make_player(2, 1400, 2)})
    data = Data(
        event_messages=dict(),
        elements=Elements(
            loot=[Loot(a_loot="a_loot", category="category", worth=0.2)],
            body_crate=[BodyCrate(on_body="on_body", worth=0.3)],
            crate=[Crate(in_crate="in_crate", worth=0.1)],
        ),
        encounters=Encounters(
            single_gain_random=[],
            player_fight=[
                PlayerFight(
                    success_message="{player_name} wins over {other_player_name}, diff: {time_diff}",
                    fail_message="{player_name} wins over {other_player_name}, diff: {time_diff}",
                )
            ],
        ),
    )
    game = IdleZ(
        store=store, data=data, event_queue=[], event_handlers=[], random=fake_random
    )

    game.two_player_event()

    assert game.event_queue == [want_evt]
