# Hermes agents & skills pack

This directory mounts read-only into Hermes at `/opt/data/agents`. It holds the
**sanitized starter pack** of skills that ship with agentstack, plus whatever
you add yourself. Nothing personal or secret belongs here — it ships in the
public repo and is covered by the repo-wide sanitization scan.

## What ships

Three original, general-purpose skills (MIT, authored for agentstack):

| Skill | What it does |
|-------|--------------|
| `code-review` | Review a diff/PR for correctness, security, maintainability |
| `diagnosing-bugs` | Root-cause a bug with a reproduce → hypothesize → test loop |
| `stack-doctor` | Diagnose a running agentstack deployment (Hermes ↔ OmniRoute ↔ mem0) |

Each is a `<name>/SKILL.md` with YAML frontmatter (`name`, `description`,
`version`, `license`, `author`, `platforms`, `tags`) — the format Hermes loads.
Copy one as a template for your own.

## Adding your own

Drop a `your-skill/SKILL.md` here (same frontmatter) and restart Hermes, or
mount a different directory by setting `AGENTSTACK_AGENTS` in `.env`.

## Using third-party skill packs

We **reference** external packs with install instructions rather than
redistributing them, so their authors keep attribution and you get them from
source. A large general catalog is **ECC** (Everything Claude Code,
`affaan-m/ECC`, MIT) — clone it and copy the skills you want into this
directory, keeping each file's `license:` and `origin:` lines intact. Only ship
a third-party skill onward if its license permits it and you preserve its
attribution.

> Keep personal, income-related, or deployment-specific skills out of this
> directory — they are for your private store (`~/.hermes/skills`), not the
> public pack.
