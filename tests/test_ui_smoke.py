"""Builds every screen and fires every handler against a fake Flet page.

Flet validates control properties on construction, so this catches wrong
property names/types without opening a window.
"""

import asyncio
from types import SimpleNamespace

import flet as ft
import pytest

from passgen.ui import app as ui


class FakePage:
    def __init__(self):
        self.controls = []
        self.window = SimpleNamespace()
        self.dialogs = []
        self.tasks = []

    def add(self, *c):
        self.controls.extend(c)

    def update(self):
        pass

    def show_dialog(self, d):
        self.dialogs.append(d)

    def run_task(self, fn, *args):
        self.tasks.append((fn, args))


class FakeClipboard:
    def __init__(self):
        self.value = None

    def copy(self, text):
        self.value = text

    def clear_if_owned(self):
        had = self.value is not None
        self.value = None
        return had


def ev(**kw):
    return SimpleNamespace(control=SimpleNamespace(**kw))


def walk(control):
    yield control
    for attr in ("content", "controls", "leading", "segments", "options"):
        child = getattr(control, attr, None)
        if isinstance(child, list):
            for c in child:
                yield from walk(c)
        elif isinstance(child, ft.BaseControl):
            yield from walk(child)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    a = ui.PasswordApp(FakePage())
    a.clipboard = FakeClipboard()
    a.start()
    return a


def test_password_screen_generates(app):
    assert len(app.results) == 1 and len(app.results[0]) == app.s.length
    app.on_generate()
    assert app.history == app.results


def test_every_section_builds_in_both_languages(app):
    for lang in ("uk", "en"):
        app.s.language = lang
        app.i18n = ui.I18n(lang)
        app.build()
        for idx in range(4):
            app.on_nav(ev(selected_index=idx))
            assert list(walk(app.body.content))


def test_copy_and_auto_clear(app):
    app.copy_secret(app.results[0])
    assert app.clipboard.value == app.results[0]
    fn, args = app.page.tasks[-1]
    app.s.clipboard_timeout = 0
    asyncio.run(fn(args[0], 0))
    assert app.clipboard.value is None


def test_options_errors_and_passphrase(app):
    for name in ("lowercase", "uppercase", "digits", "symbols"):
        app.bind_bool(name)(ev(value=False))
    assert app.results == []  # error shown instead of a password
    app.bind_bool("digits")(ev(value=True))
    assert app.results and app.results[0].isdigit()

    app.on_nav(ev(selected_index=1))
    assert len(app.results[0].split(app.s.separator)) == app.s.words


def test_keyboard_shortcuts(app):
    before = app.results[0]
    app.on_key(SimpleNamespace(key="G", ctrl=True, shift=False))
    assert app.results[0] != before
    app.on_key(SimpleNamespace(key="C", ctrl=True, shift=True))
    assert app.clipboard.value == app.results[0]


def test_close_wipes_clipboard_and_history(app):
    app.copy_secret(app.results[0])
    destroyed = []

    async def destroy():
        destroyed.append(True)

    app.page.window.destroy = destroy
    asyncio.run(app.on_window_event(SimpleNamespace(type=ft.WindowEventType.CLOSE)))
    assert destroyed and app.clipboard.value is None and not app.history
