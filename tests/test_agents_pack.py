"""The Hermes agents/skills starter pack is present and well-formed.

Each shipped skill is a `<name>/SKILL.md` with YAML frontmatter that Hermes can
load. We don't depend on a YAML parser here — the frontmatter keys we require
are simple `key:` lines in the leading `---` block.
"""
import os

PACK = os.path.join(os.path.dirname(__file__), "..", "stacks", "core", "hermes", "agents")
SHIPPED = ("code-review", "diagnosing-bugs", "stack-doctor")
REQUIRED_KEYS = ("name", "description", "version", "license", "author")


def _frontmatter(text):
    assert text.startswith("---"), "SKILL.md must open with a --- frontmatter block"
    end = text.index("\n---", 3)
    return text[3:end]


def test_shipped_skills_exist():
    for skill in SHIPPED:
        assert os.path.isfile(os.path.join(PACK, skill, "SKILL.md")), f"{skill}/SKILL.md missing"


def test_each_skill_has_required_frontmatter():
    for skill in SHIPPED:
        text = open(os.path.join(PACK, skill, "SKILL.md"), encoding="utf-8").read()
        fm = _frontmatter(text)
        for key in REQUIRED_KEYS:
            assert f"{key}:" in fm, f"{skill}: frontmatter missing '{key}'"
        assert "license: MIT" in fm, f"{skill}: shipped skills must be MIT"


def test_name_matches_directory():
    for skill in SHIPPED:
        fm = _frontmatter(open(os.path.join(PACK, skill, "SKILL.md"), encoding="utf-8").read())
        assert f"name: {skill}" in fm, f"{skill}: frontmatter name must match directory"
