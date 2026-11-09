"""Have I Been Pwned "Pwned Passwords" check using k-anonymity.

Only the first 5 hex characters of the password's SHA-1 hash ever leave
the machine; the response is padded so its size reveals nothing either.
The check is opt-in and runs only when the user presses the button.
"""

from __future__ import annotations

import hashlib
import urllib.request
from typing import Callable

API_URL = "https://api.pwnedpasswords.com/range/{prefix}"
USER_AGENT = "GeneratorPassword-desktop"


def _fetch(prefix: str, timeout: float) -> str:
    req = urllib.request.Request(
        API_URL.format(prefix=prefix),
        headers={"User-Agent": USER_AGENT, "Add-Padding": "true"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https URL)
        return resp.read().decode("utf-8")


def pwned_count(password: str, timeout: float = 8.0,
                fetch: Callable[[str, float], str] = _fetch) -> int:
    """Return how many times the password appears in known breaches (0 = not found)."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # noqa: S324 (protocol requires SHA-1)
    prefix, suffix = digest[:5], digest[5:]
    for line in fetch(prefix, timeout).splitlines():
        found, _, count = line.strip().partition(":")
        if found == suffix:
            try:
                return int(count)  # padding entries have count 0
            except ValueError:
                return 0
    return 0
