"""Best-effort redaction of common credential patterns.

User-submitted logs frequently contain secrets that were never meant to
leave the originating system. Nexora redacts common patterns before the
content is stored, logged, or passed into any agent prompt. This is a
defense-in-depth measure, not a guarantee: users are still warned not to
submit secrets in the first place.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9_\-]{16,})")),
    ("bearer_token", re.compile(r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]{16,})")),
    ("password_field", re.compile(r"(?i)(password\s*[=:]\s*)(\S+)")),
    ("secret_field", re.compile(r"(?i)(secret\s*[=:]\s*)(\S+)")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL)),
    ("db_connection_string", re.compile(r"(?i)(postgres(?:ql)?|mysql|mongodb)://[^:\s]+:[^@\s]+@")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]

REDACTED_MARKER = "[REDACTED]"


def redact_secrets(text: str) -> tuple[str, list[str]]:
    """Redact known credential patterns.

    Returns the redacted text and a list of pattern names that were
    matched, so callers can warn the user about what was removed.
    """
    if not text:
        return text, []

    redacted = text
    matched: list[str] = []

    for name, pattern in _PATTERNS:
        def _replace(match: re.Match[str], _name: str = name) -> str:
            matched.append(_name)
            groups = match.groups()
            if groups:
                # Preserve the label (e.g. "password=") but redact the value.
                return f"{groups[0]}{REDACTED_MARKER}"
            return REDACTED_MARKER

        redacted = pattern.sub(_replace, redacted)

    return redacted, sorted(set(matched))
