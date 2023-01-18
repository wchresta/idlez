import idlez.data


def test_data_loads():
    data = idlez.data.Data.from_lib_resources()

    picker = idlez.data.DataPicker(data=data)

    picker.pick_single_encounter()


def test_data_picker_fill_event_message():
    picker = idlez.data.DataPicker(
        data=idlez.data.Data(
            event_messages={
                idlez.data.EventType.LEVEL_UP.value: [
                    "{player_name|capitalize} Text {new_level}. time: {ttl|upper}"
                ]
            },
            elements=idlez.data.Elements(loot=[], crate=[], body_crate=[]),
            encounters=idlez.data.Encounters(single_gain_random=[]),
        )
    )

    got = picker.fill_event_message(
        type=idlez.data.EventType.LEVEL_UP,
        params={
            "player_name": "player_name",
            "new_level": 24,
            "ttl": "some time",
        },
    )

    assert got == "Player_name Text 24. time: SOME TIME"
