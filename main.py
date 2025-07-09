from gui import PasswordGeneratorApp
from password_logic import PasswordGenerator


def main():
    """The main function to start the application."""
    password_generator = PasswordGenerator()
    app = PasswordGeneratorApp(generator=password_generator)
    app.mainloop()


if __name__ == "__main__":
    main()
