"""Flet user interface."""

from __future__ import annotations

import asyncio
import string

import flet as ft

from passgen import __version__
from passgen import settings as settings_mod
from passgen.core import generator as gen
from passgen.core.breach import pwned_count
from passgen.core.clipboard import ClipboardError, SecureClipboard
from passgen.core.strength import LEVEL_KEYS, analyze, crack_seconds, level_for_bits, \
    OFFLINE_FAST_RATE, OFFLINE_SLOW_RATE
from passgen.i18n import LANGUAGE_NAMES, I18n

SEED_COLOR = ft.Colors.INDIGO
LEVEL_COLORS = (ft.Colors.RED_400, ft.Colors.DEEP_ORANGE_400, ft.Colors.AMBER_600,
                ft.Colors.LIGHT_GREEN_600, ft.Colors.GREEN_600)
DIGIT_COLOR = ft.Colors.BLUE_400
SYMBOL_COLOR = ft.Colors.ORANGE_600
MONO_FONT = "Consolas"
HISTORY_LIMIT = 30
SEPARATOR_KEYS = {"-": "sep_dash", " ": "sep_space", ".": "sep_dot", "_": "sep_underscore", "": "sep_none"}


def colored_spans(text: str) -> list[ft.TextSpan]:
    """Split a password into spans so digits and symbols stand out."""
    spans: list[ft.TextSpan] = []
    for ch in text:
        if ch in string.digits:
            color = DIGIT_COLOR
        elif ch.isalpha():
            color = None
        else:
            color = SYMBOL_COLOR
        if spans and spans[-1].data == color:
            spans[-1].text += ch
        else:
            spans.append(ft.TextSpan(ch, style=ft.TextStyle(color=color), data=color))
    return spans


def card(*controls: ft.Control, title: str | None = None, expand: bool | int | None = None) -> ft.Container:
    items = []
    if title:
        items.append(ft.Text(title, size=15, weight=ft.FontWeight.W_600))
    items.extend(controls)
    return ft.Container(
        content=ft.Column(items, spacing=10, tight=True),
        padding=18,
        border_radius=14,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        expand=expand,
    )


class PasswordApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.s = settings_mod.load()
        self.i18n = I18n(self.s.language)
        self.clipboard = SecureClipboard()
        self.history: list[str] = []
        self.results: list[str] = []
        self.nav_index = 0
        self._clip_token = 0
        self._breach_token = 0

    # ---------------------------------------------------------------- helpers
    def t(self, key: str, **kw) -> str:
        return self.i18n.t(key, **kw)

    def save(self) -> None:
        try:
            settings_mod.save(self.s)
        except OSError:
            pass  # preferences are a convenience; never crash over them

    def toast(self, message: str, error: bool = False) -> None:
        self.page.show_dialog(ft.SnackBar(
            ft.Text(message, color=ft.Colors.ON_ERROR_CONTAINER if error else None),
            bgcolor=ft.Colors.ERROR_CONTAINER if error else None,
            behavior=ft.SnackBarBehavior.FLOATING,
            width=440,
            duration=2500,
        ))

    def password_options(self) -> gen.PasswordOptions:
        s = self.s
        return gen.PasswordOptions(
            length=s.length, lowercase=s.lowercase, uppercase=s.uppercase, digits=s.digits,
            symbols=s.symbols, symbol_set=s.symbol_set, exclude_ambiguous=s.exclude_ambiguous,
            exclude_chars=s.exclude_chars, require_each=s.require_each,
        )

    def passphrase_options(self) -> gen.PassphraseOptions:
        s = self.s
        return gen.PassphraseOptions(words=s.words, separator=s.separator,
                                     capitalize=s.capitalize, add_number=s.add_number)

    # ------------------------------------------------------------- lifecycle
    def start(self) -> None:
        page = self.page
        page.title = self.t("app_title")
        page.window.width = 1080
        page.window.height = 780
        page.window.min_width = 860
        page.window.min_height = 640
        page.window.prevent_close = True
        page.window.on_event = self.on_window_event
        page.padding = 0
        page.theme = ft.Theme(color_scheme_seed=SEED_COLOR)
        page.dark_theme = ft.Theme(color_scheme_seed=SEED_COLOR)
        page.on_keyboard_event = self.on_key
        self.apply_theme()
        self.build()
        self.regenerate()

    async def on_window_event(self, e: ft.WindowEvent) -> None:
        if e.type == ft.WindowEventType.CLOSE:
            self.clipboard.clear_if_owned()  # never leave a secret behind
            self.history.clear()
            self.results.clear()
            await self.page.window.destroy()

    def apply_theme(self) -> None:
        self.page.theme_mode = {"light": ft.ThemeMode.LIGHT, "dark": ft.ThemeMode.DARK}.get(
            self.s.theme, ft.ThemeMode.SYSTEM)

    # ----------------------------------------------------------------- layout
    def build(self) -> None:
        """(Re)build the whole UI — used at start and after a language change."""
        self.page.title = self.t("app_title")
        self.rail = ft.NavigationRail(
            selected_index=self.nav_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=96,
            group_alignment=-0.85,
            leading=ft.Container(ft.Icon(ft.Icons.SHIELD, size=34, color=ft.Colors.PRIMARY),
                                 padding=ft.Padding.only(top=18, bottom=8)),
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.PASSWORD, label=self.t("nav_password")),
                ft.NavigationRailDestination(icon=ft.Icons.TEXT_FIELDS, label=self.t("nav_passphrase")),
                ft.NavigationRailDestination(icon=ft.Icons.SECURITY, label=self.t("nav_checker")),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED,
                                             selected_icon=ft.Icons.SETTINGS, label=self.t("nav_settings")),
            ],
            on_change=self.on_nav,
        )
        self.body = ft.Container(expand=True, padding=ft.Padding.symmetric(horizontal=24, vertical=20))
        self.history_panel = ft.Container(width=300, padding=ft.Padding.only(top=20, right=20, bottom=20))
        self.page.controls.clear()
        self.page.add(ft.Row(
            [self.rail, ft.VerticalDivider(width=1), self.body, self.history_panel],
            expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ))
        self.show_section()

    def on_nav(self, e) -> None:
        self.nav_index = e.control.selected_index
        self.show_section()
        if self.nav_index in (0, 1):
            self.regenerate()

    def show_section(self) -> None:
        builders = (self.build_password_view, self.build_passphrase_view,
                    self.build_checker_view, self.build_settings_view)
        self.body.content = builders[self.nav_index]()
        self.history_panel.visible = self.s.keep_history and self.nav_index in (0, 1)
        self.history_panel.content = self.build_history()
        self.page.update()

    # ------------------------------------------------------- output display
    def build_output(self) -> ft.Control:
        self.output_column = ft.Column(spacing=6, tight=True, scroll=ft.ScrollMode.AUTO)
        self.strength_bar = ft.ProgressBar(value=0, bar_height=8, border_radius=4)
        self.strength_label = ft.Text(weight=ft.FontWeight.W_600)
        self.entropy_label = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.crack_label = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        actions = ft.Row([
            ft.FilledButton(self.t("generate"), icon=ft.Icons.REFRESH, on_click=self.on_generate,
                            tooltip="Ctrl+G"),
            ft.OutlinedButton(self.t("copy_all") if self.s.count > 1 and self.nav_index == 0 else self.t("copy"),
                              icon=ft.Icons.CONTENT_COPY, on_click=lambda _: self.copy_secret("\n".join(self.results)),
                              tooltip="Ctrl+Shift+C"),
        ], spacing=10)
        return card(
            ft.Container(self.output_column, height=150 if self.s.count > 1 and self.nav_index == 0 else None,
                         padding=ft.Padding.symmetric(vertical=6)),
            self.strength_bar,
            ft.Row([self.strength_label, self.entropy_label], spacing=14,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.crack_label,
            actions,
        )

    def render_results(self, bits: float) -> None:
        single = len(self.results) == 1
        rows = []
        for value in self.results:
            rows.append(ft.Row([
                ft.Text(spans=colored_spans(value), size=26 if single else 16, font_family=MONO_FONT,
                        selectable=True, expand=True, no_wrap=False),
                ft.IconButton(ft.Icons.CONTENT_COPY, icon_size=18, tooltip=self.t("copy"),
                              on_click=lambda _, v=value: self.copy_secret(v)),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
        self.output_column.controls = rows

        level = level_for_bits(bits)
        self.strength_bar.value = min(bits / 128, 1.0)
        self.strength_bar.color = LEVEL_COLORS[level]
        self.strength_label.value = self.t(LEVEL_KEYS[level])
        self.strength_label.color = LEVEL_COLORS[level]
        self.entropy_label.value = self.t("entropy", bits=round(bits))
        self.crack_label.value = self.t("crack_fast", time=self.i18n.duration(crack_seconds(bits, OFFLINE_FAST_RATE)))

    def regenerate(self, remember: bool = False) -> None:
        if self.nav_index not in (0, 1):
            return
        try:
            if self.nav_index == 0:
                opts = self.password_options()
                self.results = [gen.generate_password(opts) for _ in range(self.s.count)]
                bits = gen.password_entropy(opts)
            else:
                opts = self.passphrase_options()
                self.results = [gen.generate_passphrase(opts)]
                bits = gen.passphrase_entropy(opts)
        except gen.GenerationError as err:
            self.results = []
            self.output_column.controls = [ft.Text(self.t(err.code), color=ft.Colors.ERROR)]
            self.strength_bar.value = 0
            self.strength_label.value = self.entropy_label.value = self.crack_label.value = ""
            self.page.update()
            return
        self.render_results(bits)
        if remember:
            self.remember(self.results)
        self.page.update()

    def on_generate(self, _=None) -> None:
        self.regenerate(remember=True)

    # -------------------------------------------------------------- clipboard
    def copy_secret(self, text: str) -> None:
        if not text:
            return
        try:
            self.clipboard.copy(text)
        except ClipboardError:
            self.toast(self.t("copy_failed"), error=True)
            return
        self.remember(text.split("\n"))
        timeout = self.s.clipboard_timeout
        self._clip_token += 1
        if timeout:
            self.toast(self.t("copied_timer", sec=timeout))
            self.page.run_task(self._auto_clear, self._clip_token, timeout)
        else:
            self.toast(self.t("copied"))

    async def _auto_clear(self, token: int, timeout: int) -> None:
        await asyncio.sleep(timeout)
        if token == self._clip_token and self.clipboard.clear_if_owned():
            self.toast(self.t("clipboard_cleared"))

    # ---------------------------------------------------------------- history
    def remember(self, values: list[str]) -> None:
        if not self.s.keep_history:
            return
        for v in values:
            if v in self.history:
                self.history.remove(v)
            self.history.insert(0, v)
        del self.history[HISTORY_LIMIT:]
        if self.history_panel.visible:
            self.history_panel.content = self.build_history()

    def build_history(self) -> ft.Control:
        if not self.history:
            items: list[ft.Control] = [ft.Text(self.t("history_empty"), size=12, color=ft.Colors.ON_SURFACE_VARIANT)]
        else:
            items = [
                ft.Row([
                    ft.Text(v, font_family=MONO_FONT, size=13, expand=True, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS, tooltip=v),
                    ft.IconButton(ft.Icons.CONTENT_COPY, icon_size=16, tooltip=self.t("copy"),
                                  on_click=lambda _, val=v: self.copy_secret(val)),
                ], spacing=2)
                for v in self.history
            ]

        def clear(_):
            self.history.clear()
            self.history_panel.content = self.build_history()
            self.page.update()

        return card(
            ft.Text(self.t("history_hint"), size=11, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Column(items, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            ft.TextButton(self.t("clear_history"), icon=ft.Icons.DELETE_SWEEP, on_click=clear,
                          disabled=not self.history),
            title=self.t("history"),
            expand=True,
        )

    # ---------------------------------------------------------- option binding
    def bind_bool(self, name: str):
        def handler(e):
            setattr(self.s, name, bool(e.control.value))
            self.save()
            self.regenerate()
        return handler

    def view(self, title: str, *controls: ft.Control) -> ft.Control:
        return ft.Column(
            [ft.Text(title, size=26, weight=ft.FontWeight.BOLD), *controls],
            spacing=16, scroll=ft.ScrollMode.AUTO, expand=True,
        )

    def labeled_slider(self, key: str, attr: str, lo: int, hi: int, on_done=None) -> ft.Control:
        value_text = ft.Text(str(getattr(self.s, attr)), weight=ft.FontWeight.BOLD, width=40,
                             text_align=ft.TextAlign.RIGHT)

        def changed(e):
            v = int(e.control.value)
            value_text.value = str(v)
            if v != getattr(self.s, attr):
                setattr(self.s, attr, v)
                self.regenerate()

        def done(_):
            self.save()
            if on_done:
                on_done()

        return ft.Row([
            ft.Text(self.t(key), width=110),
            ft.Slider(min=lo, max=hi, divisions=hi - lo, value=getattr(self.s, attr), expand=True,
                      on_change=changed, on_change_end=done),
            value_text,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # ------------------------------------------------------------- password
    def build_password_view(self) -> ft.Control:
        s = self.s

        def text_option(attr: str, label: str, width: int):
            def changed(e):
                setattr(self.s, attr, e.control.value)
                self.save()
                self.regenerate()
            return ft.TextField(label=label, value=getattr(s, attr), width=width, dense=True,
                                text_style=ft.TextStyle(font_family=MONO_FONT), on_change=changed)

        def count_done():
            self.show_section()  # output box height / button label depend on the count
            self.regenerate()

        charsets = ft.Column([
            ft.Checkbox(label=self.t("lowercase"), value=s.lowercase, on_change=self.bind_bool("lowercase")),
            ft.Checkbox(label=self.t("uppercase"), value=s.uppercase, on_change=self.bind_bool("uppercase")),
            ft.Checkbox(label=self.t("digits"), value=s.digits, on_change=self.bind_bool("digits")),
            ft.Checkbox(label=self.t("symbols"), value=s.symbols, on_change=self.bind_bool("symbols")),
        ], spacing=0)

        advanced = ft.ExpansionTile(
            title=ft.Text(self.t("advanced")),
            leading=ft.Icon(ft.Icons.TUNE),
            controls_padding=ft.Padding.only(left=12, bottom=12),
            controls=[
                ft.Switch(label=self.t("require_each"), value=s.require_each, on_change=self.bind_bool("require_each")),
                ft.Switch(label=self.t("exclude_ambiguous"), value=s.exclude_ambiguous,
                          on_change=self.bind_bool("exclude_ambiguous")),
                ft.Row([text_option("symbol_set", self.t("symbol_set"), 320),
                        text_option("exclude_chars", self.t("exclude_chars"), 200)], wrap=True),
            ],
        )

        return self.view(
            self.t("nav_password"),
            self.build_output(),
            card(
                self.labeled_slider("length", "length", gen.MIN_LENGTH, gen.MAX_LENGTH),
                self.labeled_slider("count", "count", 1, 20, on_done=count_done),
                charsets,
                advanced,
            ),
        )

    # ----------------------------------------------------------- passphrase
    def build_passphrase_view(self) -> ft.Control:
        s = self.s

        def sep_changed(e):
            self.s.separator = e.control.value if e.control.value != "none" else ""
            self.save()
            self.regenerate()

        return self.view(
            self.t("nav_passphrase"),
            ft.Text(self.t("passphrase_hint"), color=ft.Colors.ON_SURFACE_VARIANT),
            self.build_output(),
            card(
                self.labeled_slider("words", "words", gen.MIN_WORDS, gen.MAX_WORDS),
                ft.Dropdown(
                    label=self.t("separator"), width=260, value=s.separator or "none",
                    options=[ft.DropdownOption(key=k or "none", text=self.t(v)) for k, v in SEPARATOR_KEYS.items()],
                    on_select=sep_changed,
                ),
                ft.Switch(label=self.t("capitalize"), value=s.capitalize, on_change=self.bind_bool("capitalize")),
                ft.Switch(label=self.t("add_number"), value=s.add_number, on_change=self.bind_bool("add_number")),
            ),
        )

    # -------------------------------------------------------------- checker
    def build_checker_view(self) -> ft.Control:
        bar = ft.ProgressBar(value=0, bar_height=8, border_radius=4)
        level = ft.Text(weight=ft.FontWeight.W_600)
        entropy = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        fast = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        slow = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        warnings = ft.Column(spacing=4)
        breach_result = ft.Text()

        def update(e):
            self._breach_token += 1  # invalidate any in-flight breach result
            breach_result.value = ""
            value = field.value or ""
            if not value:
                bar.value, level.value, entropy.value, fast.value, slow.value = 0, "", "", "", ""
                warnings.controls = []
                self.page.update()
                return
            r = analyze(value)
            bar.value = min(r.bits / 128, 1.0)
            bar.color = level.color = LEVEL_COLORS[r.level]
            level.value = self.t(r.level_key)
            entropy.value = self.t("entropy", bits=round(r.bits))
            fast.value = self.t("crack_fast", time=self.i18n.duration(r.offline_fast_seconds))
            slow.value = self.t("crack_slow", time=self.i18n.duration(r.offline_slow_seconds))
            if r.warnings:
                warnings.controls = [
                    ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, size=16, color=ft.Colors.AMBER_700),
                            ft.Text(self.t(w), expand=True)]) for w in r.warnings]
            else:
                warnings.controls = [ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_600),
                                             ft.Text(self.t("no_warnings"))])]
            self.page.update()

        async def check_breach(_):
            value = field.value or ""
            if not value:
                return
            self._breach_token += 1
            token = self._breach_token
            breach_result.value, breach_result.color = self.t("breach_checking"), None
            self.page.update()
            try:
                count = await asyncio.to_thread(pwned_count, value)
            except OSError:
                count = None
            if token != self._breach_token:
                return  # the text changed meanwhile
            if count is None:
                breach_result.value, breach_result.color = self.t("breach_error"), ft.Colors.ERROR
            elif count:
                breach_result.value, breach_result.color = self.t("breach_found", count=f"{count:,}".replace(",", " ")), ft.Colors.ERROR
            else:
                breach_result.value, breach_result.color = self.t("breach_clean"), ft.Colors.GREEN_600
            self.page.update()

        field = ft.TextField(label=self.t("checker_input"), password=True, can_reveal_password=True,
                             autofocus=True, text_style=ft.TextStyle(font_family=MONO_FONT, size=18),
                             on_change=update, max_length=256)

        return self.view(
            self.t("checker_title"),
            ft.Row([ft.Icon(ft.Icons.LOCK_OUTLINE, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(self.t("checker_hint"), color=ft.Colors.ON_SURFACE_VARIANT)]),
            card(field, bar, ft.Row([level, entropy], spacing=14), fast, slow, warnings),
            card(
                ft.Text(self.t("breach_hint"), size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.OutlinedButton(self.t("check_breach"), icon=ft.Icons.TRAVEL_EXPLORE, on_click=check_breach),
                breach_result,
            ),
        )

    # ------------------------------------------------------------- settings
    def build_settings_view(self) -> ft.Control:
        s = self.s

        def lang_changed(e):
            self.s.language = e.control.value
            self.i18n = I18n(self.s.language)
            self.save()
            self.build()

        def theme_changed(e):
            self.s.theme = next(iter(e.control.selected))
            self.save()
            self.apply_theme()
            self.page.update()

        def timeout_changed(e):
            self.s.clipboard_timeout = int(e.control.value)
            self.save()

        def history_changed(e):
            self.s.keep_history = bool(e.control.value)
            if not self.s.keep_history:
                self.history.clear()
            self.save()

        return self.view(
            self.t("nav_settings"),
            card(
                ft.Dropdown(
                    label=self.t("language"), width=260, value=s.language,
                    leading_icon=ft.Icons.LANGUAGE,
                    options=[ft.DropdownOption(key=k, text=v) for k, v in LANGUAGE_NAMES.items()],
                    on_select=lang_changed,
                ),
                ft.Text(self.t("theme")),
                ft.SegmentedButton(
                    selected=[s.theme],
                    segments=[
                        ft.Segment(value="system", label=self.t("theme_system"), icon=ft.Icons.BRIGHTNESS_AUTO),
                        ft.Segment(value="light", label=self.t("theme_light"), icon=ft.Icons.LIGHT_MODE),
                        ft.Segment(value="dark", label=self.t("theme_dark"), icon=ft.Icons.DARK_MODE),
                    ],
                    on_change=theme_changed,
                ),
                title=self.t("appearance_title"),
            ),
            card(
                ft.Dropdown(
                    label=self.t("clipboard_timeout"), width=260, value=str(s.clipboard_timeout),
                    leading_icon=ft.Icons.TIMER_OUTLINED,
                    options=[ft.DropdownOption(key=str(v), text=self.t("timeout_never") if v == 0
                                               else self.t("timeout_sec", sec=v))
                             for v in settings_mod.CLIPBOARD_TIMEOUTS],
                    on_select=timeout_changed,
                ),
                ft.Switch(label=self.t("keep_history"), value=s.keep_history, on_change=history_changed),
                title=self.t("security_title"),
            ),
            card(
                ft.Text(self.t("about_text")),
                ft.Text(self.t("shortcuts"), size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(f"v{__version__}", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                title=self.t("about_title"),
            ),
        )

    # ------------------------------------------------------------- keyboard
    def on_key(self, e: ft.KeyboardEvent) -> None:
        key = (e.key or "").upper()
        if e.ctrl and not e.shift and key == "G":
            self.on_generate()
        elif e.ctrl and e.shift and key == "C" and self.nav_index in (0, 1):
            self.copy_secret("\n".join(self.results))


async def main(page: ft.Page) -> None:
    PasswordApp(page).start()
