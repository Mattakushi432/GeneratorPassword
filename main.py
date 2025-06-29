from gui import PasswordGeneratorApp
from password_logic import PasswordGenerator


def main():
    """The main function to start the application."""
    password_generator = PasswordGenerator()
    app = PasswordGeneratorApp(generator=password_generator)
    app.mainloop()


if __name__ == "__main__":
    try:
        import pyperclip
    except ImportError:
        print("The 'pyperclip' library was not found. Attempting to install...")
        import subprocess
        import sys

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
        except Exception as e:
            print(f"Failed to install pyperclip: {e}")
            print("Please install it manually: pip install pyperclip")
            sys.exit(1)

    main()

