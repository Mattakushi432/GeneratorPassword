import string
import secrets


class PasswordGenerator:
    """Responsible for the basic logic of password generation."""

    def generate(self, length: int, use_lowercase: bool, use_uppercase: bool,
                 use_digits: bool, use_symbols: bool) -> str | None:
        """Generates a random password based on the specified parameters.

        Args:
            length (int): Length of the password.
            use_lowercase (bool): Whether to include lowercase letters.
            use_uppercase (bool): Whether to include uppercase letters.
            use_digits (bool): Whether to include digits.
            use_symbols (bool): Whether to include symbols.
        Returns:
            str | None: The generated password or None if no character set is specified.
        """
        char_set = ""
        if use_lowercase:
            char_set += string.ascii_lowercase
        if use_uppercase:
            char_set += string.ascii_uppercase
        if use_digits:
            char_set += string.digits
        if use_symbols:
            char_set += string.punctuation

        if not char_set:
            return

        password = "".join(secrets.choice(char_set) for _ in range(length))
        return password

