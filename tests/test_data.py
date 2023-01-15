import idlez.data


def test_data_loads():
    data = idlez.data.Data.from_lib_resources()

    picker = idlez.data.DataPicker(data=data)

    picker.pick_single_encounter()
