from wizard.preflight import detect_platform


def test_detects_linux():
    assert detect_platform("linux") == "linux"
    assert detect_platform("linux2") == "linux"


def test_detects_macos():
    assert detect_platform("darwin") == "macos"


def test_detects_windows():
    assert detect_platform("win32") == "windows"


def test_unknown_defaults_to_linux():
    assert detect_platform("sunos5") == "linux"
