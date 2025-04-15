import os
import requests
import re
import logging
import time
from datetime import datetime

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
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
                ip = response.text.strip().split('=')[-1] if '=' in response.text else response.text.strip()
                if ipv4_regex.match(ip):
                    return ip
        except requests.RequestException:
            continue
    logging.error("Failed to find a valid IP.")
    return None


class DDNSUpdater:
    def __init__(self):
        self.lastUpdate = datetime.now()
        self.check_interval = int(os.environ.get('CHECK_INTERVAL', 300))
        
        # Get credentials from environment variables
        self.email = os.environ.get('CF_EMAIL')
        self.key = os.environ.get('CF_KEY')
        self.token = os.environ.get('CF_TOKEN')
        self.zone_id = os.environ.get('CF_ZONE_ID')
        self.record_name = os.environ.get('CF_RECORD_NAME')
        self.ttl = int(os.environ.get('CF_TTL', '1'))
        self.proxied = os.environ.get('CF_PROXIED', 'false').lower() == 'true'
        
        # Validate configuration
        if not (self.email and (self.key or self.token) and self.zone_id and self.record_name):
            logging.error("Missing required environment variables. Please set CF_EMAIL, CF_TOKEN/CF_KEY, CF_ZONE_ID, and CF_RECORD_NAME.")
            raise ValueError("Missing required configuration")
            
        logging.info(f"DDNS Updater initialized for {self.record_name}")
        logging.info(f"Check interval: {self.check_interval} seconds")
        
    def get_headers(self):
        headers = {
            "X-Auth-Email": self.email,
            "Content-Type": "application/json"
        }
        
        # Set authorization header based on available credentials
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            headers["X-Auth-Key"] = self.key
            
        return headers
            
    def get_dns_record(self, ip):
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records?type=A&name={self.record_name}"

        try:
            logging.info(f"Checking DNS record for {self.record_name}")
            response = requests.get(url, headers=self.get_headers()).json()

            if not response.get("success", False):
                error_msg = response.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                logging.error(f"API Error: {error_msg}")
                return

            if response.get("result_info", {}).get("count", 0) == 0:
                logging.warning(f"Record does not exist for {self.record_name}, creating new record")
                self.create_dns_record(ip)
                return

            old_ip = response["result"][0]["content"]
            if ip == old_ip:
                logging.info(f"IP ({ip}) for {self.record_name} has not changed")
                return

            record_identifier = response["result"][0]["id"]
            self.update_dns_record(record_identifier, ip)

        except requests.RequestException as e:
            logging.error(f"Failed to get DNS record: {e}")
        except KeyError as e:
            logging.error(f"Unexpected API response format: {e}")
        except Exception as e:
            logging.error(f"Error processing {self.record_name}: {e}")
            
    def create_dns_record(self, ip):
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records"
        data = {
            "type": "A",
            "name": self.record_name,
            "content": ip,
            "ttl": self.ttl,
            "proxied": self.proxied
        }
        
        try:
            response = requests.post(url, json=data, headers=self.get_headers()).json()
            if response and response.get("success", False):
                logging.info(f"Created new DNS record for {self.record_name} with IP {ip}")
            else:
                error_msg = response.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                logging.error(f"Failed to create DNS record: {error_msg}")
        except requests.RequestException as e:
            logging.error(f"Failed to create DNS record: {e}")

    def update_dns_record(self, record_identifier, ip):
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records/{record_identifier}"
        data = {
            "type": "A",
            "name": self.record_name,
            "content": ip,
            "ttl": self.ttl,
            "proxied": self.proxied
        }
        
        try:
            response = requests.patch(url, json=data, headers=self.get_headers()).json()
            if response and response.get("success", False):
                logging.info(f"Updated {self.record_name} to {ip}")
            else:
                error_msg = response.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                logging.error(f"Failed to update DNS record: {error_msg}")
        except requests.RequestException as e:
            logging.error(f"Failed to update DNS record: {e}")

    def check_time(self):
        time.sleep(1)
        diff = (datetime.now() - self.lastUpdate).total_seconds()
        if diff > self.check_interval:
            self.lastUpdate = datetime.now()
            return True
        else:
            return False

    def run(self):
        logging.info("Starting DDNS updater")
        # Run immediately on startup
        self.main()
        
        # Then run on interval
        while True:
            if self.check_time():
                self.main()

    def main(self):
        ip = get_public_ip()
        if not ip:
            logging.error("Could not determine public IP")
            return
        logging.info(f"Current public IP: {ip}")
        self.get_dns_record(ip)


if __name__ == "__main__":
    try:
        updater = DDNSUpdater()
        updater.run()
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        # Exit with error code
        exit(1)
