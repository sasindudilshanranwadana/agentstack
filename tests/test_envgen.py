from wizard.envgen import compose_files, generate_env
from wizard.components import resolve_selection


def test_compose_files_cover_selection():
    sel = resolve_selection([])
    files = compose_files(sel)
    assert any("omniroute" in f for f in files)
    assert all(
        f.startswith("stacks/") and f.endswith("docker-compose.yml") for f in files
    )


def test_env_uses_user_value_when_provided():
    env = generate_env({"omniroute"}, {}, {"OMNIROUTE_API_KEY": "sk-user"})
    assert env.get("OMNIROUTE_API_KEY") == "sk-user"


def test_env_never_invents_secret_for_missing_key():
    env = generate_env({"omniroute"}, {}, {})
    assert env.get("OMNIROUTE_API_KEY", "") == ""


def test_env_includes_integration_keys():
    env = generate_env(set(), {"notification": "telegram"}, {"TELEGRAM_BOT_TOKEN": "x"})
    assert "TELEGRAM_CHAT_ID" in env


def test_env_supports_multiple_providers():
    # Spec §5: LLM providers are multi-select. Picking two must wire both keys.
    env = generate_env(set(), {"provider": ("openai", "anthropic")}, {})
    assert "OPENAI_API_KEY" in env and "ANTHROPIC_API_KEY" in env
