"""Swappable integration templating for the agentstack wizard.

Each integration choice (a notification channel, an LLM provider, an ingress
mode) maps to the set of env keys it needs. Values are always placeholders
(empty strings) here; real values are supplied by the user at install time and
written only to a local .env. Swapping one integration for another is a wizard
answer, not a code change (see §5 of the design spec).
"""

from __future__ import annotations

NOTIFICATIONS = ("telegram", "discord", "slack", "email", "none")
PROVIDERS = ("openai", "anthropic", "google", "openrouter", "local")
INGRESS = ("domain-tls", "localhost")

_NOTIFICATION_KEYS: dict[str, tuple[str, ...]] = {
    "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
    "discord": ("DISCORD_WEBHOOK_URL",),
    "slack": ("SLACK_WEBHOOK_URL",),
    "email": ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_TO"),
    "none": (),
}

_PROVIDER_KEYS: dict[str, tuple[str, ...]] = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "google": ("GOOGLE_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "local": (),
}

_INGRESS_KEYS: dict[str, tuple[str, ...]] = {
    "domain-tls": ("DOMAIN", "ACME_EMAIL"),
    "localhost": (),
}

_KINDS: dict[str, dict[str, tuple[str, ...]]] = {
    "notification": _NOTIFICATION_KEYS,
    "provider": _PROVIDER_KEYS,
    "ingress": _INGRESS_KEYS,
}


def render_integration(kind: str, choice: str) -> dict[str, str]:
    """Return the placeholder env keys a given integration choice needs.

    Raises ValueError on an unknown kind or an unknown choice for that kind.
    """
    if kind not in _KINDS:
        raise ValueError(f"unknown integration kind: {kind!r}")
    options = _KINDS[kind]
    if choice not in options:
        raise ValueError(f"unknown {kind} choice: {choice!r}")
    return {key: "" for key in options[choice]}
