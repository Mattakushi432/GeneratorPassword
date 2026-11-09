"""User preferences, stored as JSON in %APPDATA%\\GeneratorPassword.

Only preferences are stored — never passwords or history.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from passgen import APP_NAME
from passgen.core.generator import MAX_LENGTH, MAX_WORDS, MIN_LENGTH, MIN_WORDS, SYMBOLS

LANGUAGES = ("uk", "en")
THEMES = ("system", "light", "dark")
SEPARATORS = ("-", " ", ".", "_", "")
CLIPBOARD_TIMEOUTS = (0, 15, 30, 60, 120)


@dataclass
class Settings:
    language: str = "uk"
    theme: str = "system"
    # Password mode
    length: int = 20
    count: int = 1
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    symbol_set: str = SYMBOLS
    exclude_ambiguous: bool = False
    exclude_chars: str = ""
    require_each: bool = True
    # Passphrase mode
    words: int = 6
    separator: str = "-"
    capitalize: bool = True
    add_number: bool = True
    # Security
    clipboard_timeout: int = 30
    keep_history: bool = True

    def normalized(self) -> "Settings":
        """Return a copy with every field forced into its valid range."""
        s = Settings(**asdict(self))
        if s.language not in LANGUAGES:
            s.language = "uk"
        if s.theme not in THEMES:
            s.theme = "system"
        s.length = min(max(int(s.length), MIN_LENGTH), MAX_LENGTH)
        s.count = min(max(int(s.count), 1), 50)
        s.words = min(max(int(s.words), MIN_WORDS), MAX_WORDS)
        if s.separator not in SEPARATORS:
            s.separator = "-"
        if s.clipboard_timeout not in CLIPBOARD_TIMEOUTS:
            s.clipboard_timeout = 30
        s.symbol_set = str(s.symbol_set)[:64] or SYMBOLS
        s.exclude_chars = str(s.exclude_chars)[:64]
        return s


def default_path() -> Path:
    """Portable build (.exe): settings live next to the executable, so the app
    leaves nothing behind in the user profile. Falls back to %APPDATA% when the
    exe folder is read-only (e.g. Program Files) and when running from source."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if os.access(exe_dir, os.W_OK):
            return exe_dir / f"{APP_NAME}.settings.json"
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_NAME / "settings.json"


def load(path: Path | None = None) -> Settings:
    path = path or default_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    defaults = Settings()
    kwargs = {}
    for f in fields(Settings):
        value = raw.get(f.name, getattr(defaults, f.name))
        if type(value) is not type(getattr(defaults, f.name)):
            value = getattr(defaults, f.name)  # wrong type in file → default
        kwargs[f.name] = value
    return Settings(**kwargs).normalized()


def save(settings: Settings, path: Path | None = None) -> None:
    path = path or default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
