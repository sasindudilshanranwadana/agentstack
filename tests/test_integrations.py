import pytest

from wizard.integrations import render_integration, NOTIFICATIONS


def test_telegram_requires_token_and_chat():
    env = render_integration("notification", "telegram")
    assert "TELEGRAM_BOT_TOKEN" in env and "TELEGRAM_CHAT_ID" in env


def test_none_notification_yields_empty():
    assert render_integration("notification", "none") == {}


def test_localhost_ingress_needs_no_domain():
    assert "ACME_EMAIL" not in render_integration("ingress", "localhost")


def test_unknown_choice_raises():
    with pytest.raises(ValueError):
        render_integration("notification", "pigeon")


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        render_integration("telepathy", "telegram")


def test_notifications_roster_is_exposed():
    assert set(NOTIFICATIONS) == {"telegram", "discord", "slack", "email", "none"}
