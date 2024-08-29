import os
import sys
import threading
import winreg
import requests
import re
import logging
import time
from config import Config
from notifypy import Notify
from PIL import Image
import pystray
from datetime import datetime

# App Name
app_name = "Cloudflare DDNS"

# Set up logging
logging.basicConfig(level=logging.INFO, filename='ddns_updater.log', format='%(asctime)s - %(levelname)s - %(message)s')

notify = Notify(
    default_notification_title="DDNS Updater",
    default_application_name="Cloudflare DDNS",
    default_notification_icon="cloudflare-icon.png"
)


def get_public_ip():
    ipv4_regex = re.compile(r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.'
                            r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.'
                            r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\.'
                            r'([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])')
    for url in ['https://cloudflare.com/cdn-cgi/trace', 'https://api.ipify.org', 'https://ipv4.icanhazip.com']:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                ip = response.text.strip().split('=')[-1]
                if ipv4_regex.match(ip):
                    return ip
        except requests.RequestException:
            continue
    logging.error("Failed to find a valid IP.")
    return None


class DDNSUpdater:
    def __init__(self):
        self.manualChecking = False
        self.lastUpdate = datetime.now()
        self.config = None
        self.exit = False
        self.refresh_config()
        self.icon = None

        # Start the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.system_tray)
        tray_thread.daemon = True  # Allows the thread to exit when the main program exits
        tray_thread.start()

    def system_tray(self):
        image = Image.open("cloudflare-icon.png")
        self.icon = pystray.Icon("DDNS", image, "Cloudflare DDNS", menu=pystray.Menu(
            pystray.MenuItem("Update DNS", self.after_click),
            pystray.MenuItem("Window Startup", self.after_click),
            pystray.MenuItem("Exit", self.after_click)))
        self.icon.run()

    def after_click(self, icon, query):
        if str(query) == "Update DNS":
            self.manualChecking = True
        elif str(query) == "Window Startup":
            self.check_startup_entry_exists()
        elif str(query) == "Exit":
            self.icon.stop()
            self.exit = True

    def check_startup_entry_exists(self):
        try:
            # Open the registry key for user-specific startup programs
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE  # Use KEY_SET_VALUE to modify the registry
            )

            try:
                # Try to read the registry value
                winreg.QueryValueEx(reg_key, app_name)
                # If no exception is raised, the value exists
                exists = True
            except FileNotFoundError:
                # If the file is not found, the value does not exist
                exists = False

            if exists:
                winreg.DeleteValue(reg_key, app_name)
                self.send_message("Startup launch enable", False, True)
            else:
                # Determine the path to the executable or script
                executable_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
                # Add or update the registry value
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, executable_path)
                self.send_message("Startup launch disable", False, True)

            winreg.CloseKey(reg_key)
        except Exception as e:
            if 'Access is denied' in str(e):
                self.send_message("Try again after run as admin!", True)
                return
            self.send_message(str(e), True)

    def refresh_config(self):
        self.config = Config()

    def get_dns_record(self):
        headers = {
            "X-Auth-Email": self.config.auth_email,
            "Authorization": f"Bearer {self.config.auth_key}" if self.config.auth_method == "token" else f"X-Auth-Key: {self.config.auth_key}",
            "Content-Type": "application/json"
        }
        url = f"https://api.cloudflare.com/client/v4/zones/{self.config.zone_identifier}/dns_records?type=A&name={self.config.record_name}"
        try:
            response = requests.get(url, headers=headers)
            return response.json() if response.status_code == 200 else None
        except requests.RequestException as e:
            logging.error(f"Failed to get DNS record: {e}")
            return None

    def update_dns_record(self, record_identifier, ip):
        headers = {
            "X-Auth-Email": self.config.auth_email,
            "Authorization": f"Bearer {self.config.auth_key}" if self.config.auth_method == "token" else f"X-Auth-Key: {self.config.auth_key}",
            "Content-Type": "application/json"
        }
        url = f"https://api.cloudflare.com/client/v4/zones/{self.config.zone_identifier}/dns_records/{record_identifier}"
        data = {
            "type": "A",
            "name": self.config.record_name,
            "content": ip,
            "ttl": self.config.ttl,
            "proxied": self.config.proxy
        }
        try:
            response = requests.patch(url, json=data, headers=headers)
            return response.json() if response.status_code == 200 else None
        except requests.RequestException as e:
            logging.error(f"Failed to update DNS record: {e}")
            return None

    def send_message(self, msg, error=False, notification=False):
        print(msg)
        notify.message = str(msg)
        notify_thread = threading.Thread(target=notify.send(block=False))
        if error:
            if not self.config.silent:
                notify_thread.start()
                logging.error(msg)
        else:
            if not self.config.silent and not self.config.message or notification:
                notify_thread.start()
                logging.info(msg)

    def check_time(self):
        time.sleep(1)
        diff = (datetime.now() - self.lastUpdate).total_seconds()
        print(diff)
        if diff > self.config.check_interval:
            self.lastUpdate = datetime.now()
            return True
        else:
            return False

    def run(self):
        self.main()
        while not self.exit:
            if self.check_time() or self.manualChecking:
                self.main()
            else:
                continue

    def main(self):
        self.manualChecking = False
        self.refresh_config()
        ip = get_public_ip()
        if not ip:
            return
        logging.info("Check Initiated")
        record = self.get_dns_record()

        if not record or record.get("result_info", {}).get("count", 0) == 0:
            self.send_message(
                f"Record does not exist, perhaps create one first? ({ip} for {self.config.record_name})", True)
            return

        old_ip = record["result"][0]["content"]
        if ip == old_ip:
            self.send_message(f"IP ({ip}) for {self.config.record_name} has not changed.", False)
            return

        record_identifier = record["result"][0]["id"]
        update = self.update_dns_record(record_identifier, ip)

        if update and update.get("success", False):
            self.send_message(f"{ip} {self.config.record_name} DDNS updated.", False)
        else:
            self.send_message(f"{ip} {self.config.record_name} DDNS failed for {record_identifier} ({ip}).", True)
        return


if __name__ == "__main__":
    updater = DDNSUpdater()
    updater.run()
