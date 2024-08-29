import json
import tkinter as tk
import logging
from tkinter import messagebox

defaults = {
    'start': False,
    'silent': True,
    'message': True,
    'check_interval': 600,
    'proxy': False,
    'ttl': 600,
    'record_name': "",
    'zone_identifier': "",
    'auth_key': "",
    'auth_method': "token",
    'auth_email': "",
}

prompts = {
    'auth_email': " ⃰ Auth Email:",
    'auth_key': " ⃰ Auth Key:",
    'zone_identifier': " ⃰ Zone Identifier:",
    'record_name': " ⃰ Record Name:",
    'ttl': "TTL (seconds):",
    'proxy': "Enable Proxy (True/False):",
    'check_interval': "Check Interval (seconds):",
    'message': "Enable Messages (True/False):",
    'silent': "Enable Silent Mode (True/False):",
    'start': "Windows Startup (True/False):",
    'auth_method': "Auth Method (token/basic):",
}


def save_to_file(user_data):
    with open('config.json', 'w') as file:
        json.dump(user_data, file, indent=4)


class Config:
    def __init__(self, config_file='config.json'):
        self.required_fields = ['auth_email', 'auth_key', 'zone_identifier', 'record_name']
        self.config_file = config_file
        self.dialog = None
        self.user_data = {}
        self.config = {}
        self.load_config()

        for key in self.required_fields:
            if self.config[key] == "" or self.config[key] is None:
                self.custom_dialog(prompts[key], key)
                self.config[key] = self.user_data[key]

        self.start = self.config["start"]
        self.silent = self.config["silent"]
        self.message = self.config["message"]
        self.check_interval = self.config["check_interval"]
        self.proxy = self.config["proxy"]
        self.ttl = self.config["ttl"]
        self.record_name = self.config["record_name"]
        self.zone_identifier = self.config["zone_identifier"]
        self.auth_key = self.config["auth_key"]
        self.auth_method = self.config["auth_method"]
        self.auth_email = self.config["auth_email"]

    def load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_file, 'r') as file:
                self.config = json.load(file)
        except FileNotFoundError:
            logging.info("Configuration file not found.")
            self.get_user_input()
            return

            # Set class variables with values from the config file or default values
        for key, default_value in defaults.items():
            value = self.config.get(key, default_value)
            if value == "" or value is None:
                value = default_value
            self.config[key] = value
        logging.info("Values load from config.json")

    def update_from_user_data(self):
        """Update class attributes from user input or defaults."""
        for key, default_value in defaults.items():
            value = self.user_data.get(key, default_value)
            # Apply default if value is None or an empty string
            if value == "" or value is None:
                value = default_value
            self.user_data[key] = value
        self.config = self.user_data

    def get_user_input(self):
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        for key, prompt in prompts.items():
            self.custom_dialog(prompt, key)
        self.update_from_user_data()
        save_to_file(self.user_data)
        logging.info("Values saved to config.json")

    def custom_dialog(self, prompt, key):
        """Create a custom dialog to ask for user input."""
        self.dialog = tk.Toplevel()
        self.dialog.title("Cloudflare DDNS")

        try:
            self.dialog.iconphoto(True, tk.PhotoImage(file="cloudflare-icon.png"))
        except tk.TclError:
            logging.warning("Icon file not found. Proceeding without icon.")

        # Create a label and entry widget
        label = tk.Label(self.dialog, text=prompt, padx=10, pady=10)
        label.pack()
        entry = tk.Entry(self.dialog, width=50)
        entry.pack(padx=10, pady=10)

        # Add an OK button
        ok_button = tk.Button(self.dialog, text="OK", command=lambda: self.check_value(entry, key))
        ok_button.pack(pady=10)

        # Center the dialog on the screen
        self.dialog.update_idletasks()
        width, height = self.dialog.winfo_width(), self.dialog.winfo_height()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        self.dialog.wait_window()  # Wait for the dialog to close

    def check_value(self, entry, key):
        value = entry.get()
        if not value and key in self.required_fields:
            messagebox.showwarning("Missing Fields", "This field is required!")
        else:
            self.user_data[key] = value
            self.dialog.destroy()
