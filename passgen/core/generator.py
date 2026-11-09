"""Cryptographically secure password and passphrase generation.

All randomness comes from the ``secrets`` module (the OS CSPRNG,
``BCryptGenRandom`` on Windows). Nothing here touches the disk or network.
"""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path

LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SYMBOLS = string.punctuation
# Characters that are easy to confuse when read or typed by hand.
AMBIGUOUS = "Il1|O0o`'\""

MIN_LENGTH = 4
MAX_LENGTH = 128
MIN_WORDS = 3
MAX_WORDS = 12

WORDLIST_PATH = Path(__file__).resolve().parent.parent / "assets" / "eff_large_wordlist.txt"


class GenerationError(ValueError):
    """Raised when options make generation impossible. ``code`` is an i18n key."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PasswordOptions:
    length: int = 20
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    symbol_set: str = SYMBOLS
    exclude_ambiguous: bool = False
    exclude_chars: str = ""
    require_each: bool = True


def build_classes(opts: PasswordOptions) -> list[str]:
    """Return the selected character classes, filtered and mutually disjoint."""
    wanted: list[str] = []
    if opts.lowercase:
        wanted.append(LOWERCASE)
    if opts.uppercase:
        wanted.append(UPPERCASE)
    if opts.digits:
        wanted.append(DIGITS)
    if opts.symbols:
        wanted.append(opts.symbol_set)

    banned = set(opts.exclude_chars)
    if opts.exclude_ambiguous:
        banned |= set(AMBIGUOUS)

    seen: set[str] = set()
    classes: list[str] = []
    for chars in wanted:
        cleaned = []
        for ch in chars:
            # Skip whitespace/control chars, banned chars and duplicates.
            if ch in banned or ch in seen or not ch.isprintable() or ch.isspace():
                continue
            seen.add(ch)
            cleaned.append(ch)
        if cleaned:
            classes.append("".join(cleaned))
    return classes


def _validate(opts: PasswordOptions, classes: list[str]) -> None:
    if not classes:
        raise GenerationError("err_no_charset")
    if not MIN_LENGTH <= opts.length <= MAX_LENGTH:
        raise GenerationError("err_length")
    if opts.require_each and opts.length < len(classes):
        raise GenerationError("err_length_classes")


def generate_password(opts: PasswordOptions) -> str:
    """Generate one password.

    With ``require_each`` the result is drawn *uniformly* from all strings that
    contain at least one character of every selected class (rejection
    sampling), so ``password_entropy`` is exact rather than an estimate.
    """
    classes = build_classes(opts)
    _validate(opts, classes)
    pool = "".join(classes)
    class_sets = [set(c) for c in classes]

    while True:
        candidate = "".join(secrets.choice(pool) for _ in range(opts.length))
        if not opts.require_each or all(any(ch in cs for ch in candidate) for cs in class_sets):
            return candidate


def password_entropy(opts: PasswordOptions) -> float:
    """Exact entropy in bits of ``generate_password`` for these options."""
    classes = build_classes(opts)
    _validate(opts, classes)
    sizes = [len(c) for c in classes]
    total = sum(sizes)
    length = opts.length
    if not opts.require_each:
        return length * math.log2(total)

    # Inclusion–exclusion: strings over the pool that miss no class.
    count = 0
    for k in range(len(sizes) + 1):
        for missing in combinations(sizes, k):
            count += (-1) ** k * (total - sum(missing)) ** length
    return math.log2(count)


@lru_cache(maxsize=1)
def load_wordlist(path: Path = WORDLIST_PATH) -> tuple[str, ...]:
    """Load the EFF large diceware wordlist (7776 words)."""
    words = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if parts:
                words.append(parts[-1])
    if len(set(words)) != len(words) or len(words) < 1000:
        raise RuntimeError("Wordlist is corrupted")
    return tuple(words)


@dataclass(frozen=True)
class PassphraseOptions:
    words: int = 6
    separator: str = "-"
    capitalize: bool = True
    add_number: bool = True


def generate_passphrase(opts: PassphraseOptions, wordlist: tuple[str, ...] | None = None) -> str:
    if not MIN_WORDS <= opts.words <= MAX_WORDS:
        raise GenerationError("err_words")
    wordlist = wordlist or load_wordlist()
    chosen = [secrets.choice(wordlist) for _ in range(opts.words)]
    if opts.capitalize:
        chosen = [w.capitalize() for w in chosen]
    if opts.add_number:
        idx = secrets.randbelow(len(chosen))
        chosen[idx] = chosen[idx] + str(secrets.randbelow(10))
    return opts.separator.join(chosen)


def passphrase_entropy(opts: PassphraseOptions, wordlist_size: int | None = None) -> float:
    size = wordlist_size or len(load_wordlist())
    bits = opts.words * math.log2(size)
    if opts.add_number:
        bits += math.log2(10) + math.log2(opts.words)
    return bits
