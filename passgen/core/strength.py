"""Offline strength estimation for an arbitrary (user-typed) password.

A small zxcvbn-style model: the password is split into the cheapest
sequence of patterns (dictionary words, keyboard walks, sequences,
repeats, years, random characters) and the guess-cost of that split is
reported in bits. It is conservative on purpose: patterns an attacker
would try first are cheap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

from passgen.core.generator import load_wordlist

MAX_INPUT = 256

OFFLINE_FAST_RATE = 1e11  # fast hash (MD5/NTLM) on a GPU cluster, guesses/s
OFFLINE_SLOW_RATE = 1e4   # slow hash (bcrypt/argon2), guesses/s

LEVEL_THRESHOLDS = (28, 36, 60, 80)  # bits → levels 0..4

KEYBOARD_ROWS = (
    "`1234567890-=",
    "qwertyuiop[]\\",
    "asdfghjkl;'",
    "zxcvbnm,./",
    "йцукенгшщзхї",
    "фівапролджє",
    "ячсмитьбю",
    "1qaz2wsx3edc4rfv5tgb6yhn7ujm8ik9ol0p",
)

LEET = str.maketrans({"@": "a", "4": "a", "3": "e", "1": "i", "!": "i", "0": "o",
                      "$": "s", "5": "s", "7": "t", "+": "t", "8": "b", "9": "g"})

COMMON_WORDS = frozenset("""
password passw0rd pass qwerty qwertz azerty letmein welcome admin administrator
login user root master monkey dragon football baseball soccer hockey batman
superman iloveyou trustno1 sunshine princess shadow michael jennifer jordan
hunter ranger buster thomas robert charlie daniel andrew joshua matthew
starwars whatever freedom secret summer winter spring autumn love lover
hello hello123 computer internet google facebook apple samsung microsoft windows
cookie chocolate cheese pepper ginger orange banana flower killer pokemon
nintendo playstation minecraft fortnite zxcvbn asdfgh abc123 changeme default
access mustang harley ferrari porsche tigger maggie ginger silver golden
diamond yankees liverpool arsenal chelsea barcelona madrid london paris
ukraine kyiv kiev lviv odesa kharkiv slava ukraini parol kotik zaychik
sonechko solnyshko sobaka koshka lyubov natasha olena oksana andriy dmytro
sergey sergiy oleksandr ivan maksym bogdan mykola volodymyr
пароль котик зайчик сонечко любов україна слава київ привіт кохання
""".split())

LEVEL_KEYS = ("lvl_very_weak", "lvl_weak", "lvl_fair", "lvl_strong", "lvl_very_strong")


@dataclass
class StrengthReport:
    bits: float
    level: int
    offline_fast_seconds: float
    offline_slow_seconds: float
    warnings: list[str] = field(default_factory=list)

    @property
    def level_key(self) -> str:
        return LEVEL_KEYS[self.level]


def level_for_bits(bits: float) -> int:
    return sum(bits >= t for t in LEVEL_THRESHOLDS)


def crack_seconds(bits: float, rate: float) -> float:
    """Average time to find the password (half of the search space)."""
    if bits <= 1:
        return 0.0
    exponent = bits - 1 - math.log2(rate)
    return math.inf if exponent > 1000 else 2.0 ** exponent


def pool_size(password: str) -> int:
    size = 0
    if any("a" <= c <= "z" for c in password):
        size += 26
    if any("A" <= c <= "Z" for c in password):
        size += 26
    if any(c.isdigit() and c.isascii() for c in password):
        size += 10
    if any(c.isascii() and not c.isalnum() for c in password):
        size += 33
    if any(not c.isascii() and c.isalpha() for c in password):
        size += 66  # Cyrillic (Ukrainian) upper + lower
    if any(not c.isascii() and not c.isalpha() for c in password):
        size += 100
    return max(size, 1)


def _is_repeat(s: str) -> bool:
    return len(s) >= 3 and len(set(s)) == 1


def _is_sequence(s: str) -> bool:
    if len(s) < 3:
        return False
    step = ord(s[1]) - ord(s[0])
    if abs(step) != 1:
        return False
    return all(ord(b) - ord(a) == step for a, b in zip(s, s[1:]))


def _is_keyboard(s: str) -> bool:
    if len(s) < 4:
        return False
    low = s.lower()
    return any(low in row or low in row[::-1] for row in KEYBOARD_ROWS)


def _is_year(s: str) -> bool:
    return len(s) == 4 and s.isdigit() and 1900 <= int(s) <= 2039


@lru_cache(maxsize=1)
def _english_words() -> frozenset[str]:
    try:
        return frozenset(w for w in load_wordlist() if len(w) >= 4)
    except (OSError, RuntimeError):
        return frozenset()


def _dictionary_bits(s: str) -> tuple[float, str] | None:
    if len(s) < 4:
        return None
    low = s.lower()
    normalized = low.translate(LEET)
    for dictionary, label in ((COMMON_WORDS, "warn_common"), (_english_words(), "warn_dictionary")):
        if low in dictionary:
            extra = 0.0
        elif normalized in dictionary:
            extra = 1.0  # leet substitution adds roughly one bit
        else:
            continue
        if s != low:
            extra += 1.0 if s[0].isupper() and s[1:] == low[1:] else 2.0
        return math.log2(len(dictionary)) + extra, label
    return None


def analyze(password: str) -> StrengthReport:
    password = password[:MAX_INPUT]
    n = len(password)
    if n == 0:
        return StrengthReport(0.0, 0, 0.0, 0.0, ["warn_empty"])

    char_bits = math.log2(pool_size(password))
    inf = float("inf")
    best = [0.0] + [inf] * n
    kind: list[str | None] = [None] * (n + 1)
    start = [0] * (n + 1)

    for i in range(1, n + 1):
        # Random single character.
        best[i] = best[i - 1] + char_bits
        kind[i], start[i] = "char", i - 1
        for j in range(max(0, i - 40), i - 2):
            chunk = password[j:i]
            cost = None
            label = None
            dict_match = _dictionary_bits(chunk)
            if dict_match is not None:
                cost, label = dict_match
            elif _is_repeat(chunk):
                cost, label = char_bits + math.log2(len(chunk)), "warn_repeat"
            elif _is_sequence(chunk):
                cost, label = char_bits + math.log2(len(chunk)) + 1, "warn_sequence"
            elif _is_keyboard(chunk):
                cost, label = math.log2(len("".join(KEYBOARD_ROWS))) + math.log2(len(chunk)) + 1, "warn_keyboard"
            elif _is_year(chunk):
                cost, label = math.log2(140), "warn_year"
            if cost is not None and best[j] + cost < best[i]:
                best[i], kind[i], start[i] = best[j] + cost, label, j

    warnings: list[str] = []
    i = n
    while i > 0:
        if kind[i] not in (None, "char") and kind[i] not in warnings:
            warnings.append(kind[i])
        i = start[i]

    bits = best[n]
    if level_for_bits(bits) == len(LEVEL_THRESHOLDS):
        warnings = []  # patterns don't matter once the guess cost is this high
    if n < 12:
        warnings.append("warn_short")
    classes = sum([
        any(c.islower() for c in password),
        any(c.isupper() for c in password),
        any(c.isdigit() for c in password),
        any(not c.isalnum() for c in password),
    ])
    if classes < 3 and bits < 60:
        warnings.append("warn_few_classes")

    return StrengthReport(
        bits=bits,
        level=level_for_bits(bits),
        offline_fast_seconds=crack_seconds(bits, OFFLINE_FAST_RATE),
        offline_slow_seconds=crack_seconds(bits, OFFLINE_SLOW_RATE),
        warnings=warnings,
    )
