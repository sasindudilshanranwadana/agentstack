import pytest

from wizard.components import resolve_selection, CORE_IDS


def test_empty_selection_yields_core():
    assert resolve_selection([]) == set(CORE_IDS)


def test_selecting_hermes_pulls_in_its_requirements():
    assert {"omniroute", "mem0"} <= resolve_selection(["hermes"])


def test_recommended_component_keeps_core():
    out = resolve_selection(["monitoring"])
    assert CORE_IDS <= out and "monitoring" in out


def test_unknown_id_raises():
    with pytest.raises(KeyError):
        resolve_selection(["not-a-thing"])


def test_host_gateway_filtered_out_on_macos():
    from wizard.components import filter_by_platform

    resolved = resolve_selection(["host-gateway", "hermes"])
    out = filter_by_platform(resolved, "macos")
    assert "host-gateway" not in out and "hermes" in out


def test_core_survives_platform_filter_everywhere():
    from wizard.components import filter_by_platform, CORE_IDS as core

    for plat in ("linux", "macos", "windows"):
        assert core <= filter_by_platform(resolve_selection([]), plat)
