import ctypes
import sys
import threading
import winreg
import requests
import re
import logging
import time

import config as cf
from config import Config
from config import folder_path
from notifypy import Notify
from PIL import Image
import pystray
from datetime import datetime

# App Name
app_name = "Cloudflare DDNS"
key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Set up logging
logging.basicConfig(level=logging.INFO, filename=folder_path + '\\ddns_updater.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Folder-path: " + folder_path)

notify = Notify(
    default_notification_title="DDNS Updater",
    default_application_name=app_name,
    default_notification_icon=folder_path + "\\cloudflare-icon.png",
    default_notification_application_name=app_name
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
        self.config = Config()
        self.exit = False
        self.icon = None

        # Start the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.system_tray)
        tray_thread.daemon = True  # Allows the thread to exit when the main program exits
        tray_thread.start()

    def system_tray(self):
        image = Image.open(folder_path + "\\cloudflare-icon.png")
        self.icon = pystray.Icon("DDNS", image, "Cloudflare DDNS", menu=pystray.Menu(
            pystray.MenuItem("Update DNS", self.after_click),
            pystray.MenuItem("Window Startup", self.after_click),
            pystray.MenuItem("Exit", self.after_click)))
        self.icon.run()

    def after_click(self, icon, query):
        if str(query) == "Update DNS":
            self.manualChecking = True
        elif str(query) == "Window Startup":
            print("Click!")
            self.check_startup_entry_exists(True)
        elif str(query) == "Exit":
            self.icon.stop()
            self.exit = True

    def check_startup_entry_exists(self, option=False):
        exe_path = folder_path + '\\CloudflareDDNS.exe'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, app_name)
            if option:
                self.check_admin()
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                    logging.info("Startup: " + str(self.config.start))
                    if self.config.start:
                        winreg.DeleteValue(key, app_name)
                        self.config.start = False
                        self.config.config["start"] = False
                        self.send_message("Startup Disable", False, True)
                    else:
                        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                        self.config.start = True
                        self.config.config["start"] = True
                        self.send_message("Startup Enabled!", False, True)
                    cf.save_to_file(self.config.config)
                winreg.CloseKey(key)
        except FileNotFoundError:
            if self.config.start or option:
                self.check_admin()
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                    self.config.start = True
                    self.config.config["start"] = True
                    cf.save_to_file(self.config.config)
                    if option:
                        self.send_message("Startup Enabled!", True)
                    else:
                        logging.info("Startup set to enabled")
        except Exception as e:
            if 'Access is denied' in str(e):
                self.send_message("Please run the application as admin!", True)
            self.send_message(str(e), True)
        self.config.load_config()

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
        notify_thread = threading.Thread(target=lambda: notify.send(block=False))
        if self.manualChecking:
            notification = True
            self.manualChecking = False

        # Handle when self.config.silent is True
        if self.config.silent:
            if error:
                logging.error(msg)
                notify_thread.start()
            elif notification:
                logging.info(msg)
                notify_thread.start()
        else:
            # Handle when self.config.silent is False
            logging.info(msg)
            if self.config.message or error or notification:
                notify_thread.start()

    def check_time(self):
        time.sleep(1)
        diff = (datetime.now() - self.lastUpdate).total_seconds()
        if diff > self.config.check_interval:
            self.lastUpdate = datetime.now()
            return True
        else:
            return False

    def check_admin(self):
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except AttributeError:
            is_admin = False

        if not is_admin:
            # Run the script with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            self.exit = True

    def run(self):
        self.main()
        while not self.exit:
            if self.check_time() or self.manualChecking:
                self.main()
            else:
                continue

    def main(self):
        self.check_startup_entry_exists()
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
            self.send_message(f"IP ({ip}) for {self.config.record_name} has not changed.")
            return

        record_identifier = record["result"][0]["id"]
        update = self.update_dns_record(record_identifier, ip)

        if update and update.get("success", False):
            self.send_message(f"{ip} {self.config.record_name} DDNS updated.")
        else:
            self.send_message(f"{ip} {self.config.record_name} DDNS failed for {record_identifier} ({ip}).", True)


if __name__ == "__main__":
    updater = DDNSUpdater()
    updater.run()
