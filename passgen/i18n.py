"""Ukrainian and English UI strings."""

from __future__ import annotations

import math

STRINGS: dict[str, dict[str, str]] = {
    "uk": {
        "app_title": "Генератор паролів",
        "nav_password": "Пароль",
        "nav_passphrase": "Фраза",
        "nav_checker": "Перевірка",
        "nav_settings": "Налаштування",
        "generate": "Згенерувати",
        "copy": "Копіювати",
        "copy_all": "Копіювати все",
        "show": "Показати",
        "hide": "Сховати",
        "length": "Довжина",
        "count": "Кількість",
        "lowercase": "Малі літери (a–z)",
        "uppercase": "Великі літери (A–Z)",
        "digits": "Цифри (0–9)",
        "symbols": "Символи",
        "symbol_set": "Набір символів",
        "exclude_ambiguous": "Без схожих символів (I l 1 O 0 o)",
        "exclude_chars": "Виключити символи",
        "require_each": "Хоча б один символ кожного типу",
        "advanced": "Додатково",
        "words": "Кількість слів",
        "separator": "Роздільник",
        "sep_dash": "Дефіс  -",
        "sep_space": "Пробіл",
        "sep_dot": "Крапка  .",
        "sep_underscore": "Підкреслення  _",
        "sep_none": "Без роздільника",
        "capitalize": "З великої літери",
        "add_number": "Додати цифру",
        "passphrase_hint": "Фразу з випадкових слів легко запам'ятати і важко зламати. Словник EFF, 7776 слів.",
        "entropy": "Ентропія: {bits} біт",
        "crack_fast": "Злам на GPU-фермі (швидкий хеш): {time}",
        "crack_slow": "Злам при надійному хешуванні (bcrypt): {time}",
        "lvl_very_weak": "Дуже слабкий",
        "lvl_weak": "Слабкий",
        "lvl_fair": "Середній",
        "lvl_strong": "Сильний",
        "lvl_very_strong": "Дуже сильний",
        "checker_title": "Перевірка надійності пароля",
        "checker_hint": "Перевірка відбувається локально — пароль нікуди не надсилається.",
        "checker_input": "Введіть пароль",
        "check_breach": "Перевірити у базі витоків",
        "breach_hint": "Онлайн-перевірка Have I Been Pwned: передаються лише перші 5 символів SHA-1 хешу (k-анонімність).",
        "breach_checking": "Перевіряю…",
        "breach_found": "⚠ Пароль знайдено у витоках {count} раз(ів). Не використовуйте його!",
        "breach_clean": "✓ Пароль не знайдено у відомих витоках.",
        "breach_error": "Не вдалося перевірити: немає з'єднання з мережею.",
        "warn_empty": "Пароль порожній.",
        "warn_common": "Містить поширене слово або пароль.",
        "warn_dictionary": "Містить словникові слова — додайте більше слів або символів.",
        "warn_repeat": "Містить повтори символів (ааа).",
        "warn_sequence": "Містить послідовність (abc, 123).",
        "warn_keyboard": "Містить клавіатурний шаблон (qwerty).",
        "warn_year": "Містить рік — його легко вгадати.",
        "warn_short": "Закороткий: використовуйте від 12 символів.",
        "warn_few_classes": "Додайте різні типи символів.",
        "no_warnings": "Очевидних слабких місць не знайдено.",
        "history": "Історія сесії",
        "history_hint": "Зберігається лише в пам'яті й зникає після закриття програми.",
        "history_empty": "Тут з'являться згенеровані паролі.",
        "clear_history": "Очистити",
        "copied": "Скопійовано. Не потрапить в історію буфера Windows.",
        "copied_timer": "Скопійовано. Буфер очиститься через {sec} с.",
        "clipboard_cleared": "Буфер обміну очищено.",
        "copy_failed": "Не вдалося скопіювати.",
        "language": "Мова",
        "theme": "Тема",
        "theme_system": "Як у системі",
        "theme_light": "Світла",
        "theme_dark": "Темна",
        "clipboard_timeout": "Автоочищення буфера обміну",
        "timeout_never": "Ніколи",
        "timeout_sec": "{sec} с",
        "keep_history": "Показувати історію сесії",
        "security_title": "Безпека",
        "appearance_title": "Вигляд",
        "about_title": "Про програму",
        "about_text": "Паролі створюються криптостійким генератором ОС (модуль secrets). "
                      "Програма не зберігає паролі на диску і не надсилає їх у мережу.",
        "shortcuts": "Гарячі клавіші: Ctrl+G — згенерувати, Ctrl+Shift+C — копіювати.",
        "err_no_charset": "Оберіть хоча б один тип символів.",
        "err_length": "Неприпустима довжина пароля.",
        "err_length_classes": "Довжина менша за кількість обраних типів символів.",
        "err_words": "Неприпустима кількість слів.",
        "time_instant": "миттєво",
        "time_never": "практично ніколи",
        "time_seconds": "секунда|секунди|секунд",
        "time_minutes": "хвилина|хвилини|хвилин",
        "time_hours": "година|години|годин",
        "time_days": "день|дні|днів",
        "time_months": "місяць|місяці|місяців",
        "time_years": "рік|роки|років",
        "time_centuries": "століття|століття|століть",
    },
    "en": {
        "app_title": "Password Generator",
        "nav_password": "Password",
        "nav_passphrase": "Passphrase",
        "nav_checker": "Checker",
        "nav_settings": "Settings",
        "generate": "Generate",
        "copy": "Copy",
        "copy_all": "Copy all",
        "show": "Show",
        "hide": "Hide",
        "length": "Length",
        "count": "Quantity",
        "lowercase": "Lowercase (a–z)",
        "uppercase": "Uppercase (A–Z)",
        "digits": "Digits (0–9)",
        "symbols": "Symbols",
        "symbol_set": "Symbol set",
        "exclude_ambiguous": "Avoid look-alikes (I l 1 O 0 o)",
        "exclude_chars": "Exclude characters",
        "require_each": "At least one of each selected type",
        "advanced": "Advanced",
        "words": "Number of words",
        "separator": "Separator",
        "sep_dash": "Dash  -",
        "sep_space": "Space",
        "sep_dot": "Dot  .",
        "sep_underscore": "Underscore  _",
        "sep_none": "No separator",
        "capitalize": "Capitalize words",
        "add_number": "Add a digit",
        "passphrase_hint": "A phrase of random words is easy to remember and hard to crack. EFF wordlist, 7776 words.",
        "entropy": "Entropy: {bits} bits",
        "crack_fast": "Cracking on a GPU farm (fast hash): {time}",
        "crack_slow": "Cracking with strong hashing (bcrypt): {time}",
        "lvl_very_weak": "Very weak",
        "lvl_weak": "Weak",
        "lvl_fair": "Fair",
        "lvl_strong": "Strong",
        "lvl_very_strong": "Very strong",
        "checker_title": "Password strength check",
        "checker_hint": "Analysis runs locally — your password is not sent anywhere.",
        "checker_input": "Enter a password",
        "check_breach": "Check breach database",
        "breach_hint": "Online Have I Been Pwned check: only the first 5 characters of the SHA-1 hash are sent (k-anonymity).",
        "breach_checking": "Checking…",
        "breach_found": "⚠ Found in data breaches {count} time(s). Do not use it!",
        "breach_clean": "✓ Not found in known data breaches.",
        "breach_error": "Check failed: no network connection.",
        "warn_empty": "Password is empty.",
        "warn_common": "Contains a common word or password.",
        "warn_dictionary": "Contains dictionary words — add more words or characters.",
        "warn_repeat": "Contains repeated characters (aaa).",
        "warn_sequence": "Contains a sequence (abc, 123).",
        "warn_keyboard": "Contains a keyboard pattern (qwerty).",
        "warn_year": "Contains a year — easy to guess.",
        "warn_short": "Too short: use 12 characters or more.",
        "warn_few_classes": "Mix in more character types.",
        "no_warnings": "No obvious weaknesses found.",
        "history": "Session history",
        "history_hint": "Kept in memory only and gone when the app closes.",
        "history_empty": "Generated passwords will appear here.",
        "clear_history": "Clear",
        "copied": "Copied. Excluded from Windows clipboard history.",
        "copied_timer": "Copied. Clipboard will be cleared in {sec} s.",
        "clipboard_cleared": "Clipboard cleared.",
        "copy_failed": "Could not copy.",
        "language": "Language",
        "theme": "Theme",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "clipboard_timeout": "Auto-clear clipboard",
        "timeout_never": "Never",
        "timeout_sec": "{sec} s",
        "keep_history": "Show session history",
        "security_title": "Security",
        "appearance_title": "Appearance",
        "about_title": "About",
        "about_text": "Passwords come from the OS cryptographic random generator (secrets module). "
                      "The app never stores passwords on disk or sends them over the network.",
        "shortcuts": "Shortcuts: Ctrl+G — generate, Ctrl+Shift+C — copy.",
        "err_no_charset": "Select at least one character type.",
        "err_length": "Invalid password length.",
        "err_length_classes": "Length is shorter than the number of selected character types.",
        "err_words": "Invalid number of words.",
        "time_instant": "instantly",
        "time_never": "practically never",
        "time_seconds": "second|seconds",
        "time_minutes": "minute|minutes",
        "time_hours": "hour|hours",
        "time_days": "day|days",
        "time_months": "month|months",
        "time_years": "year|years",
        "time_centuries": "century|centuries",
    },
}

LANGUAGE_NAMES = {"uk": "Українська", "en": "English"}


def plural_index(lang: str, n: int) -> int:
    if lang == "uk":
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return 1
        return 2
    return 0 if n == 1 else 1


class I18n:
    def __init__(self, lang: str = "uk"):
        self.lang = lang if lang in STRINGS else "uk"

    def t(self, key: str, **kwargs) -> str:
        text = STRINGS[self.lang].get(key) or STRINGS["en"].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def plural(self, key: str, n: int) -> str:
        forms = self.t(key).split("|")
        return forms[min(plural_index(self.lang, n), len(forms) - 1)]

    def duration(self, seconds: float) -> str:
        if seconds < 1:
            return self.t("time_instant")
        if math.isinf(seconds):
            return self.t("time_never")
        units = (
            ("time_centuries", 100 * 365.25 * 86400),
            ("time_years", 365.25 * 86400),
            ("time_months", 30.44 * 86400),
            ("time_days", 86400),
            ("time_hours", 3600),
            ("time_minutes", 60),
            ("time_seconds", 1),
        )
        for key, size in units:
            if seconds >= size:
                value = int(seconds // size)
                if key == "time_centuries" and value >= 1_000_000:
                    return self.t("time_never")
                return f"{value:,}".replace(",", " ") + " " + self.plural(key, value)
        return self.t("time_instant")
