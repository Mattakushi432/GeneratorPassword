import math
import string

import pytest

from passgen import settings as settings_mod
from passgen.core import breach, generator as g, strength
from passgen.i18n import STRINGS, I18n


# ---------- password generation ----------

def test_password_has_requested_length_and_charset():
    opts = g.PasswordOptions(length=32, symbols=False)
    for _ in range(50):
        pw = g.generate_password(opts)
        assert len(pw) == 32
        assert set(pw) <= set(string.ascii_letters + string.digits)


def test_require_each_guarantees_every_class():
    opts = g.PasswordOptions(length=4)
    for _ in range(300):
        pw = g.generate_password(opts)
        assert any(c.islower() for c in pw)
        assert any(c.isupper() for c in pw)
        assert any(c.isdigit() for c in pw)
        assert any(c in string.punctuation for c in pw)


def test_exclusions_are_respected():
    opts = g.PasswordOptions(length=64, exclude_ambiguous=True, exclude_chars="abcXYZ#")
    banned = set(g.AMBIGUOUS) | set("abcXYZ#")
    for _ in range(50):
        assert not banned & set(g.generate_password(opts))


def test_custom_symbol_set_and_overlap_dedup():
    opts = g.PasswordOptions(lowercase=True, uppercase=False, digits=False,
                             symbols=True, symbol_set="a!! ", length=10)
    classes = g.build_classes(opts)
    assert classes == [string.ascii_lowercase, "!"]  # 'a' deduped, space dropped


@pytest.mark.parametrize("opts,code", [
    (g.PasswordOptions(lowercase=False, uppercase=False, digits=False, symbols=False), "err_no_charset"),
    (g.PasswordOptions(length=3), "err_length"),
    (g.PasswordOptions(length=500), "err_length"),
    (g.PasswordOptions(length=4, exclude_chars=string.punctuation), None),
])
def test_invalid_options(opts, code):
    if code is None:
        g.generate_password(opts)
        return
    with pytest.raises(g.GenerationError) as exc:
        g.generate_password(opts)
    assert exc.value.code == code


def test_entropy_without_requirement_is_length_times_log2_pool():
    opts = g.PasswordOptions(length=10, require_each=False)
    assert g.password_entropy(opts) == pytest.approx(10 * math.log2(94))


def test_entropy_with_requirement_matches_brute_force_count():
    import itertools
    opts = g.PasswordOptions(length=4, lowercase=True, uppercase=False, digits=True, symbols=False,
                             exclude_chars=string.ascii_lowercase[3:] + "3456789")
    # pool: abc + 012; count strings of len 4 with ≥1 letter and ≥1 digit by brute force
    expected = sum(1 for s in itertools.product("abc012", repeat=4)
                   if set(s) & set("abc") and set(s) & set("012"))
    assert expected == 6 ** 4 - 2 * 3 ** 4
    assert g.password_entropy(opts) == pytest.approx(math.log2(expected))


def test_passwords_are_not_repeated():
    opts = g.PasswordOptions(length=16)
    assert len({g.generate_password(opts) for _ in range(500)}) == 500


# ---------- passphrase ----------

def test_wordlist_is_full_eff_list():
    words = g.load_wordlist()
    assert len(words) == 7776
    assert words[0] == "abacus" and words[-1] == "zoom"


def test_passphrase_structure():
    opts = g.PassphraseOptions(words=5, separator=".", capitalize=True, add_number=True)
    phrase = g.generate_passphrase(opts)
    parts = phrase.split(".")
    assert len(parts) == 5
    assert all(p[0].isupper() for p in parts)
    assert sum(any(c.isdigit() for c in p) for p in parts) == 1


def test_passphrase_entropy():
    opts = g.PassphraseOptions(words=6, add_number=False)
    assert g.passphrase_entropy(opts) == pytest.approx(6 * math.log2(7776))
    with pytest.raises(g.GenerationError):
        g.generate_passphrase(g.PassphraseOptions(words=2))


# ---------- strength ----------

@pytest.mark.parametrize("pw", ["password", "qwerty123", "12345678", "aaaaaaaa", "P@ssw0rd", "Kyiv1991"])
def test_weak_passwords_are_weak(pw):
    assert strength.analyze(pw).level <= 1


def test_random_password_is_very_strong():
    pw = g.generate_password(g.PasswordOptions(length=20))
    report = strength.analyze(pw)
    assert report.level == 4
    assert report.offline_fast_seconds > 1e9


def test_strength_warnings():
    assert "warn_keyboard" in strength.analyze("qwertyuiop").warnings
    assert "warn_common" in strength.analyze("Dragon").warnings
    assert "warn_year" in strength.analyze("xk#1987").warnings
    assert "warn_short" in strength.analyze("abc").warnings
    assert strength.analyze("").warnings == ["warn_empty"]


def test_crack_seconds_monotonic():
    assert strength.crack_seconds(40, 1e4) > strength.crack_seconds(40, 1e11)
    assert math.isinf(strength.crack_seconds(5000, 1))


# ---------- breach (no network) ----------

def test_pwned_count_parses_response_and_sends_only_prefix():
    sent = {}

    def fake_fetch(prefix, timeout):
        sent["prefix"] = prefix
        # SHA1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        return "0018A45C4D1DEF81644B54AB7F969B88D65:0\r\n1E4C9B93F3F0682250B6CF8331B7EE68FD8:42\r\n"

    assert breach.pwned_count("password", fetch=fake_fetch) == 42
    assert sent["prefix"] == "5BAA6"
    assert breach.pwned_count("something-else", fetch=lambda p, t: "") == 0


# ---------- i18n ----------

def test_translations_have_identical_keys():
    assert set(STRINGS["uk"]) == set(STRINGS["en"])


def test_ukrainian_plurals_and_duration():
    i = I18n("uk")
    assert i.plural("time_years", 1) == "рік"
    assert i.plural("time_years", 3) == "роки"
    assert i.plural("time_years", 11) == "років"
    assert i.plural("time_years", 22) == "роки"
    assert i.duration(0.5) == "миттєво"
    assert i.duration(120) == "2 хвилини"
    assert I18n("en").duration(3600) == "1 hour"
    assert I18n("en").duration(math.inf) == "practically never"


# ---------- settings ----------

def test_settings_roundtrip_and_validation(tmp_path):
    path = tmp_path / "s.json"
    s = settings_mod.Settings(language="en", length=42, theme="dark")
    settings_mod.save(s, path)
    assert settings_mod.load(path) == s

    path.write_text('{"language": "ru", "length": 9999, "theme": 5, "count": "x"}', encoding="utf-8")
    loaded = settings_mod.load(path)
    assert loaded.language == "uk"
    assert loaded.length == g.MAX_LENGTH
    assert loaded.theme == "system"
    assert loaded.count == 1

    path.write_text("not json", encoding="utf-8")
    assert settings_mod.load(path) == settings_mod.Settings()


def test_portable_settings_path_next_to_exe(tmp_path, monkeypatch):
    exe = tmp_path / "GeneratorPassword.exe"
    monkeypatch.setattr(settings_mod.sys, "frozen", True, raising=False)
    monkeypatch.setattr(settings_mod.sys, "executable", str(exe))
    assert settings_mod.default_path() == tmp_path / "GeneratorPassword.settings.json"
