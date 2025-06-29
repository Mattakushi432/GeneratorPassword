import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

from password_logic import PasswordGenerator


class PasswordGeneratorApp(tk.Tk):
    """A class for creating the graphical interface of an application."""

    def __init__(self, generator: PasswordGenerator):
        super().__init__()

        self.generator = generator
        self.result_text = None
        self._configure_window()
        self._create_variables()
        self._create_widgets()

    def _configure_window(self):
        """Customizes the main window."""
        self.title("Password generator")
        self.geometry("450x500")
        self.resizable(True, True)
        self.minsize(450, 500)

        # Setting style
        style = ttk.Style(self)
        style.configure("TLabel", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 10, "bold"))
        style.configure("TEntry", font=("Helvetica", 11))
        style.configure("TCheckbutton", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))

    def _create_variables(self):
        """Creates variables to store the state of widgets."""
        self.length_var = tk.IntVar(value=12)
        self.count_var = tk.IntVar(value=1)
        self.use_lowercase_var = tk.BooleanVar(value=True)
        self.use_uppercase_var = tk.BooleanVar(value=True)
        self.use_digits_var = tk.BooleanVar(value=True)
        self.use_symbols_var = tk.BooleanVar(value=False)

    def _create_widgets(self):
        """Creates and places all interface elements."""
        frame = ttk.Frame(self, padding="20")
        frame.pack(fill="both", expand=True)

        header_label = ttk.Label(frame, text="Generation settings", style="Header.TLabel")
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Password length
        ttk.Label(frame, text="Password length:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.length_var, width=10).grid(row=1, column=1, sticky="w", pady=5)

        # CheckBox
        ttk.Label(frame, text="Use of symbols:", style="Header.TLabel").grid(
            row=3, column=0, columnspan=2, pady=(20, 10), sticky="w")
        ttk.Checkbutton(frame, text="Lowercase letters (a-z)", variable=self.use_lowercase_var).grid(
            row=4, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(frame, text="Capital letters (A-Z)", variable=self.use_uppercase_var).grid(
            row=5, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(frame, text="Numbers (0-9)", variable=self.use_digits_var).grid(
            row=6, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(frame, text="Special characters (! @ # $% ^ & *).", variable=self.use_symbols_var).grid(
            row=7, column=0, columnspan=2, sticky="w")

        ttk.Button(frame, text="Generate", command=self._on_generate_click).grid(
            row=8, column=0, columnspan=2, pady=20)

        self.result_text = tk.Text(frame, height=8, width=50, font=("Courier New", 10), relief="solid", borderwidth=1)
        self.result_text.grid(row=9, column=0, columnspan=2, sticky="nsew")

        ttk.Button(frame, text="Copy all", command=self._copy_to_clipboard).grid(
            row=10, column=0, columnspan=2, pady=(10, 0))

    def _on_generate_click(self):
        """Handler for clicking the ‘Generate’ button."""
        try:
            length = self.length_var.get()
            count = self.count_var.get()
            if length <= 0 or count <= 0:
                messagebox.showerror("Error", "The length and quantity must be greater than zero.")
                return
        except tk.TclError:
            messagebox.showerror("Error", "Enter the correct numbers for length and quantity.")
            return
        passwords = []
        for _ in range(count):
            password = self.generator.generate(
                length=length,
                use_lowercase=self.use_lowercase_var.get(),
                use_uppercase=self.use_uppercase_var.get(),
                use_digits=self.use_digits_var.get(),
                use_symbols=self.use_symbols_var.get()
            )
            if password is None:
                messagebox.showwarning("Attention", "Select at least one character type.")
                return
            passwords.append(password)

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(passwords))

    def _copy_to_clipboard(self):
        """Copies generated passwords to the clipboard."""
        text_to_copy = self.result_text.get(1.0, tk.END).strip()
        if text_to_copy:
            pyperclip.copy(text_to_copy)
            messagebox.showinfo("Copied", "Passwords copied to clipboard!")
        else:
            messagebox.showwarning("Empty", "There are no passwords to copy.")
