from wizard.cli import parse_choice

OPTS = ("alpha", "beta", "gamma")


def test_empty_returns_default():
    assert parse_choice("", OPTS, "beta") == "beta"


def test_valid_index():
    assert parse_choice("1", OPTS, "beta") == "alpha"
    assert parse_choice("3", OPTS, "beta") == "gamma"


def test_zero_is_invalid_not_last():
    assert parse_choice("0", OPTS, "beta") == "beta"


def test_negative_is_invalid():
    assert parse_choice("-1", OPTS, "beta") == "beta"


def test_out_of_range_is_default():
    assert parse_choice("99", OPTS, "beta") == "beta"


def test_non_numeric_is_default():
    assert parse_choice("xyz", OPTS, "beta") == "beta"
