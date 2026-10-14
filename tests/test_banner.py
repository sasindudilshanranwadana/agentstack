from wizard.banner import render_banner, FRAMES


def test_banner_credits_author():
    out = render_banner()
    assert "sasiverse" in out
    assert "Sasindu Dilshan Ranwadana" in out


def test_banner_names_product():
    assert "agentstack" in render_banner().lower()


def test_frames_nonempty():
    assert len(FRAMES) >= 1 and all(isinstance(f, str) and f for f in FRAMES)
