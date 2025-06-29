import customtkinter
from tkinter import messagebox
import pyperclip

from password_logic import PasswordGenerator

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")


class PasswordGeneratorApp(customtkinter.CTk):
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
        self.geometry("854x500")
        self.resizable(True, True)
        self.minsize(854, 500)

    def _create_variables(self):
        """Creates variables to store the state of widgets."""
        self.length_var = customtkinter.StringVar(value="12")
        self.count_var = customtkinter.StringVar(value="1")
        self.use_lowercase_var = customtkinter.BooleanVar(value=True)
        self.use_uppercase_var = customtkinter.BooleanVar(value=True)
        self.use_digits_var = customtkinter.BooleanVar(value=True)
        self.use_symbols_var = customtkinter.BooleanVar(value=False)

    def _create_widgets(self):
        """Creates and places all interface elements."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        setting_frame = customtkinter.CTkFrame(self, corner_radius=10)
        setting_frame.grid(row=0, column=0, padx=20, pady=20, sticky="new")
        setting_frame.grid_columnconfigure(1, weight=1)

        header_label = customtkinter.CTkLabel(setting_frame, text="Generation settings",
                                              font=customtkinter.CTkFont(size=20, weight="bold"))
        header_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        # Password length
        customtkinter.CTkLabel(setting_frame, text="Password length:").grid(
            row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        customtkinter.CTkEntry(setting_frame, textvariable=self.length_var).grid(
            row=1, column=1, padx=(10, 20), pady=10, sticky="w")

        # Number of password
        customtkinter.CTkLabel(setting_frame, text="Number of password").grid(
            row=2, column=0, padx=(20, 10), pady=5, sticky="w")
        customtkinter.CTkEntry(setting_frame, textvariable=self.count_var).grid(
            row=2, column=1, padx=(10, 20), pady=10, sticky="w")

        # CheckBox
        checkbox_frame = customtkinter.CTkFrame(self, corner_radius=10)
        checkbox_frame.grid(row=1, column=0, padx=20, pady=0, sticky="new")

        customtkinter.CTkLabel(checkbox_frame, text="Use of symbols:",
                               font=customtkinter.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(10, 5),
                                                                                        anchor="w")
        customtkinter.CTkCheckBox(checkbox_frame, text="Lowercase letters (a-z)",
                                  variable=self.use_lowercase_var).pack(padx=20, pady=5, anchor="w")
        customtkinter.CTkCheckBox(checkbox_frame, text="Numbers (0-9)",
                                  variable=self.use_digits_var).pack(padx=20, pady=5, anchor="w")
        customtkinter.CTkCheckBox(checkbox_frame, text="Special characters (!@#$...)",
                                  variable=self.use_symbols_var).pack(padx=20, pady=(5, 10), anchor="w")

        generate_button = customtkinter.CTkButton(self, text="Generate", command=self._on_generate_click, height=40,
                                                  font=customtkinter.CTkFont(size=14, weight="bold"))
        generate_button.grid(row=2, column=0, padx=20, pady=10)

        self.result_text = customtkinter.CTkTextbox(self, height=150, width=450, corner_radius=10, font=("Courier New", 12))
        self.result_text.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")

        copy_button = customtkinter.CTkButton(self, text="Copy all",
                                              command=self._copy_to_clipboard, fg_color="transparent", border_width=2)
        copy_button.grid(row=4, column=0, padx=20, pady=(0, 20))

    def _on_generate_click(self):
        """Handler for clicking the ‘Generate’ button."""
        try:
            length_str = self.length_var.get()
            count_str = self.count_var.get()
            if not length_str or not count_str:
                messagebox.showerror("Error", "The length and quantity fields cannot be empty.")
                return
            try:
                length = int(length_str)
                count = int(count_str)
            except ValueError:
                pass

        except ValueError:
            messagebox.showerror("Error", "Please enter whole numbers only.")
            return

        if length <= 0 or count <= 0:
            messagebox.showerror("Error", "The length and quantity must be greater than zero.")

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

        self.result_text.delete(1.0, "end")
        self.result_text.insert("end", "\n".join(passwords))

    def _copy_to_clipboard(self):
        """Copies generated passwords to the clipboard."""
        text_to_copy = self.result_text.get(1.0, "end").strip('\n')
        if not text_to_copy:
            messagebox.showwarning("Empty", "There are no passwords to copy.")
            return

        excel_friendly_text = f"{text_to_copy}"

        text_to_copy = "\n".join(excel_friendly_text)

        self.clipboard_clear()
        self.clipboard_append(excel_friendly_text)
        messagebox.showinfo("Copied", "Passwords are copied and ready to be pasted into Excel!")