import idlez.bot


def test_human_secs():
    assert idlez.bot.human_secs(1) == "1 second"
    assert idlez.bot.human_secs(2) == "2 seconds"
    assert idlez.bot.human_secs(60) == "1 minute"
    assert idlez.bot.human_secs(61) == "1 minute, 1 second"
    assert idlez.bot.human_secs(121) == "2 minutes, 1 second"
    assert idlez.bot.human_secs(2 * 60 * 60) == "2 hours"
    assert idlez.bot.human_secs(2 * 60 * 60 + 2) == "2 hours, 2 seconds"
    assert idlez.bot.human_secs(25 * 60 * 60) == "1 day, 1 hour"
