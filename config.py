import json
import tkinter as tk
from tkinter import simpledialog
import logging


def save_to_file(user_data):
    with open('config.json', 'w') as file:
        json.dump(user_data, file, indent=4)


class Config:
    def __init__(self, config_file='config.json'):
        # Default values
        self.defaults = {
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
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """Load the configuration from the JSON file."""
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
        except FileNotFoundError:
            logging.info("Configuration file not found.")
            self.get_user_input()
            self.load_config()
            return  # Return early to avoid overwriting user data with defaults

        # Set class variables with values from the config file or default values
        for key, default_value in self.defaults.items():
            setattr(self, key, config.get(key, default_value))

    def get_user_input(self):
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        # Dictionary to store user inputs
        user_data = {}

        # List of prompts for user inputs
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

        # Get multiple inputs from the user
        for key, prompt in prompts.items():
            user_input = simpledialog.askstring("Input", prompt)
            if user_input is not None:
                if key in ['proxy', 'silent', 'message', 'start']:
                    user_data[key] = user_input.lower() in ['true', '1']
                elif key in ['ttl', 'check_interval']:
                    user_data[key] = int(user_input) if user_input.isdigit() else self.defaults[key]
                else:
                    user_data[key] = user_input
            else:
                user_data[key] = self.defaults.get(key, "No input provided")

        # Save the collected data to a JSON file
        save_to_file(user_data)
        logging.info("Values saved to config.json")
