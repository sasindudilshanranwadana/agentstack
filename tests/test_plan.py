from wizard.plan import build_install_plan, InstallPlan
from wizard.components import CORE_IDS


def _plan(selected, consented, platform="linux"):
    return build_install_plan(
        selected=selected,
        consented=consented,
        integration_choices={"provider": ("openai",)},
        user_values={"OPENAI_API_KEY": "sk-x"},
        platform=platform,
    )


def test_core_always_present():
    assert CORE_IDS <= _plan([], []).components


def test_optin_excluded_without_consent():
    assert "host-gateway" not in _plan(["host-gateway"], []).components


def test_optin_included_with_consent():
    assert "host-gateway" in _plan(["host-gateway"], ["host-gateway"]).components


def test_host_gateway_dropped_on_macos_even_with_consent():
    p = _plan(["host-gateway"], ["host-gateway"], platform="macos")
    assert "host-gateway" not in p.components


def test_plan_lists_compose_files_and_env():
    p = _plan([], [])
    assert all(f.startswith("stacks/") for f in p.compose_files)
    assert p.env.get("OPENAI_API_KEY") == "sk-x"


def test_plan_is_immutable():
    assert isinstance(_plan([], []), InstallPlan)
