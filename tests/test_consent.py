from wizard.components import apply_consent, resolve_selection


def test_optin_dropped_without_consent():
    resolved = resolve_selection(["host-gateway"])
    assert "host-gateway" not in apply_consent(resolved, consented=[])


def test_optin_kept_with_consent():
    resolved = resolve_selection(["host-gateway"])
    assert "host-gateway" in apply_consent(resolved, consented=["host-gateway"])


def test_non_optin_unaffected_by_consent():
    resolved = resolve_selection(["monitoring"])
    assert "monitoring" in apply_consent(resolved, consented=[])
