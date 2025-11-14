from __future__ import annotations

import re
from typing import Iterable


WHITESPACE_REGEX = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    normalized = text.replace("\u00a0", " ")
    normalized = WHITESPACE_REGEX.sub(" ", normalized)
    return normalized.strip()


def normalize_metadata(metadata: dict) -> dict:
    return {k: (normalize_text(v) if isinstance(v, str) else v) for k, v in metadata.items()}

