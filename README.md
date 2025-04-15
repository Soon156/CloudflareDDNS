# Cloudflare DDNS Docker

A lightweight Docker container that automatically updates Cloudflare DNS records with your current public IP address.

## Features

- Automatically updates Cloudflare DNS A records with your public IP
- Containerized for easy deployment and management
- Simple configuration using environment variables
- Checks public IP at configurable intervals
- Supports both Cloudflare API tokens and Global API keys
- Creates DNS records if they don't exist
- Detailed logging

## Prerequisites

- Docker installed on your host system
- Cloudflare account with a domain
- Cloudflare API token or Global API key
- Cloudflare Zone ID for your domain

## Quick Start

1. Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  app:
    image: fawefs156/cloudflare-ddns:latest
    container_name: cloudflare-ddns # change this base on your preference
    environment:
      - CHECK_INTERVAL=300 # Update interval in seconds
      - CF_EMAIL=your-email@example.com
      - CF_TOKEN=your-api-token # Use either CF_TOKEN or CF_KEY
      # - CF_KEY=your-global-api-key
      - CF_ZONE_ID=your-zone-id
      - CF_RECORD_NAME=your-domain.com
      - CF_TTL=1
      - CF_PROXIED=false

    restart: unless-stopped
```

2. Start the container:

```bash
docker-compose up -d
```
### Using Docker Command

```bash
# Run the container
docker run -d \
  --name cloudflare-ddns \
  --restart unless-stopped \
  -e CHECK_INTERVAL=300 \
  -e CF_EMAIL=your-email@example.com \
  -e CF_TOKEN=your-api-token \
  -e CF_ZONE_ID=your-zone-id \
  -e CF_RECORD_NAME=your-domain.com \
  -e CF_TTL=1 \
  -e CF_PROXIED=false \
  cloudflare-ddns
```

## Configuration

Configure the container using the following environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CHECK_INTERVAL` | No | Time in seconds between IP checks (default: 300) | `300` |
| `CF_EMAIL` | Yes | Your Cloudflare account email | `user@example.com` |
| `CF_TOKEN` | Yes* | Your Cloudflare API token | `Abc123Xyz789...` |
| `CF_KEY` | Yes* | Alternative to CF_TOKEN: Your Cloudflare Global API key | `global-api-key` |
| `CF_ZONE_ID` | Yes | Zone ID for your domain (found in Cloudflare dashboard) | `abc123def456...` |
| `CF_RECORD_NAME` | Yes | The domain/subdomain to update | `ddns.example.com` |
| `CF_TTL` | No | TTL value for DNS record (default: 1 - automatic) | `1` |
| `CF_PROXIED` | No | Whether to proxy through Cloudflare (default: false) | `false` |

*You must provide either `CF_TOKEN` (recommended) or `CF_KEY`

## Security Recommendations

For enhanced security, use a Cloudflare API token instead of a Global API key. You can create a token with limited permissions:

1. Go to Cloudflare dashboard → My Profile → API Tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template or create a custom token with:
   - Zone:DNS:Edit permissions
   - Include only the specific zone you want to update

## Logs and Monitoring

View logs with:

```bash
docker logs -f cloudflare-ddns
```

## Troubleshooting

Common issues:
- "API Error: Authentication error": Check your CF_EMAIL and CF_TOKEN/CF_KEY
- "Missing required configuration": Ensure all required environment variables are set
- "Record does not exist": The script will attempt to create the record
- "Failed to find a valid IP": Network issue, check container's internet connectivity

## License

This project is licensed under the MIT License