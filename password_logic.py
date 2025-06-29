import string
import random

class PasswordGenerator:
    """Responsible for the basic logic of password generation."""
    def generate(self, length: int, use_lowercase: bool, use_uppercase: bool, use_digits: bool, use_symbols: bool) -> str | None:
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
            return None

        password = "".join(random.choice(char_set) for _ in range(length))
        return password

