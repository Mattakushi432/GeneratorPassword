# GeneratorPassword 2.0

Надійний генератор паролів для Windows 11 з інтерфейсом на Flet. Мови: українська та англійська.
A secure password generator for Windows 11 built with Flet. Languages: Ukrainian and English.

## Можливості / Features

- **Паролі** — довжина 4–128, до 20 штук за раз, власний набір символів, виключення схожих (`I l 1 O 0 o`) та будь-яких символів, гарантія «хоча б один символ кожного типу».
- **Парольні фрази** — 3–12 слів зі словника EFF (7776 слів), роздільник, великі літери, цифра.
- **Точна ентропія** — для паролів рахується точно (з урахуванням вимоги «кожного типу»), а не приблизно.
- **Перевірка надійності** будь-якого пароля локально: словники, клавіатурні шаблони (`qwerty`, `йцукен`), послідовності, повтори, роки; оцінка часу злому.
- **Перевірка витоків** (за бажанням) через Have I Been Pwned з k-анонімністю — у мережу йдуть лише 5 символів SHA-1 хешу.
- **Безпечний буфер обміну Windows** — скопійований пароль не потрапляє в історію буфера (Win+V) і хмарну синхронізацію; автоочищення через 15–120 с (лише якщо в буфері досі наш пароль) і при закритті програми.
- **Без слідів** — паролі ніколи не зберігаються на диск; історія сесії лише в пам'яті. На диск пишуться тільки налаштування (`%APPDATA%\GeneratorPassword\settings.json`).
- Світла / темна / системна тема, гарячі клавіші `Ctrl+G` (згенерувати) та `Ctrl+Shift+C` (копіювати).

## Запуск / Run

```powershell
pip install -r requirements.txt
python main.py
```

## Тести / Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

## Портативна версія .exe / Portable build

```powershell
pip install pyinstaller pillow
powershell -ExecutionPolicy Bypass -File packaging\build_portable.ps1
```

Результат — один файл `dist\GeneratorPassword.exe` (~64 МБ) без інсталятора і без змін у реєстрі.
Скрипт спочатку запускає тести, а поруч кладе `GeneratorPassword.exe.sha256`.

Портативний режим: налаштування зберігаються поруч з exe у `GeneratorPassword.settings.json`
(можна носити на флешці). Якщо папка лише для читання — використовується `%APPDATA%\GeneratorPassword`.

Single-file portable exe, no installer. Settings are stored next to the exe; falls back to `%APPDATA%`
when the folder is read-only.

## Структура / Layout

```
main.py                    entry point
passgen/core/generator.py  password & passphrase generation, exact entropy
passgen/core/strength.py   offline strength analysis
passgen/core/breach.py     HIBP k-anonymity check
passgen/core/clipboard.py  Windows clipboard (no history/cloud, auto-clear)
passgen/settings.py        preferences (JSON in %APPDATA%)
passgen/i18n.py            Ukrainian / English strings
passgen/ui/app.py          Flet UI
passgen/assets/            EFF large wordlist (CC BY 3.0, eff.org)
```
