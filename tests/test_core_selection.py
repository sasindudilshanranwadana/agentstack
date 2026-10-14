import os

from wizard.components import resolve_selection
from wizard.envgen import compose_files


def test_core_compose_files_all_exist():
    for rel in compose_files(resolve_selection([])):
        assert os.path.isfile(rel), rel


def test_core_is_exactly_three_files():
    assert len(compose_files(resolve_selection([]))) == 3
