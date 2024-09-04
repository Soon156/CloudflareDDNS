The script, **Cloudflare DDNS Updater**, automates the process of updating DNS records for a domain managed by Cloudflare, ensuring that the DNS always points to the correct public IP address. Here's a summary for the README:

---

# Cloudflare DDNS Updater

This Python script automates the management of Dynamic DNS (DDNS) records for a domain hosted on Cloudflare. It periodically checks the public IP address of your machine and updates the DNS record if the IP has changed, ensuring that your domain always points to your current IP.

## Key Features:
- **Automatic IP Detection:** Retrieves the current public IP address using multiple services.
- **DNS Record Management:** Checks and updates the DNS `A` record for your domain using the Cloudflare API.
- **System Tray Integration:** A system tray icon allows manual updates, toggling startup behavior, and exiting the application.
- **Windows Startup:** Optionally configures the application to run at system startup.
- **Notifications:** Provides notifications for successful updates, errors, and other events.

## Requirements:
- Python 3.x
- Required Python packages: `requests`, `pystray`, `notifypy`, `Pillow`
- Detailed in `requirements.txt`

## Usage:
1. **Configuration:** Ensure that the `config.py` file contains the necessary Cloudflare API credentials and other configurations.
2. **Running the Script:** Execute the script to start monitoring and updating your DNS records automatically.
3. **System Tray:** Use the tray icon to manually trigger an update, enable/disable startup, or exit the application.

This tool is especially useful for users with a dynamic IP who need to keep their domain pointing to the correct address without manual intervention.

---

## Configuration

The script uses a configuration file that defines various settings for its operation. Below is an overview of the configuration options:

```javascript
{
    "auth_email": "",
    "auth_key": "",
    "zone_identifier": "",
    "record_name": "",
    "start": true,
    "silent": true,
    "message": true,
    "check_interval": 600,
    "proxy": false,
    "ttl": 600,
    "auth_method": "token"
}
```

### Configuration Options:

- **`auth_email`** (`str`):
  - **Description**: The email address associated with the Cloudflare account (required when using the global API key).
  - **Default**: `""` (Empty string, must be set by the user if using a global API key).

- **`auth_key`** (`str`):
  - **Description**: The API token or global API key used for authentication with Cloudflare.
  - **Default**: `""` (Empty string, must be set by the user).

- **`zone_identifier`** (`str`):
  - **Description**: The Cloudflare Zone ID associated with the domain.
  - **Default**: `""` (Empty string, must be set by the user).

- **`record_name`** (`str`):
  - **Description**: The DNS record name that should be updated (e.g., `subdomain.example.com`).
  - **Default**: `""` (Empty string, must be set by the user).

- **`start`** (`bool`):
  - **Description**: Determines if the script should automatically run at Windows startup.
  - **Default**: `False` (The script will not start automatically unless changed to `True`).

- **`silent`** (`bool`):
  - **Description**: Controls whether the script runs in silent mode. When enabled, notifications are minimized, showing only critical messages such as errors.
  - **Default**: `True` (Silent mode is enabled by default).

- **`message`** (`bool`):
  - **Description**: Specifies whether informational messages should be displayed as notifications.
  - **Default**: `True` (Notifications for messages are enabled).

- **`check_interval`** (`int`):
  - **Description**: Defines the time interval (in seconds) between IP address checks.
  - **Default**: `600` (The IP is checked every 10 minutes).

- **`proxy`** (`bool`):
  - **Description**: Indicates whether to enable Cloudflare's proxy service for the DNS record.
  - **Default**: `False` (Proxy is disabled by default).

- **`ttl`** (`int`):
  - **Description**: Sets the TTL (Time-To-Live) for the DNS record, in seconds.
  - **Default**: `600` (The DNS record TTL is set to 10 minutes).

- **`auth_method`** (`str`):
  - **Description**: The method of authentication, either `"token"` for API token or `"key"` for global API key.
  - **Default**: `"token"` (Uses API token for authentication by default).