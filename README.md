# PC Link for Home Assistant

A [Home Assistant](https://www.home-assistant.io/) custom integration that lets you monitor and control a Windows PC running [pc-link](https://github.com/vadimtitov/pc-link) — a lightweight Go HTTP server for remote PC power management.

## Features

- **Switch entity** — shows whether your PC is on or off and lets you control it from HA dashboards, automations, and scripts
- **Wake-on-LAN** — turns the PC on by sending a magic packet
- **Sleep / Hibernate / Shutdown** — turns the PC off using your preferred method
- **Polling** — periodically checks the PC's health endpoint with a configurable interval
- **Options flow** — change turn-off action and polling interval without re-adding the integration

## Requirements

- A Windows PC running [pc-link](https://github.com/vadimtitov/pc-link)
- The PC must be on the same LAN as your Home Assistant instance (required for Wake-on-LAN)
- Wake-on-LAN must be enabled in the PC's BIOS/UEFI and network adapter settings

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top-right corner and select **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Search for "PC Link" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/pc_link` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **PC Link**
3. Enter the required fields:
   - **Host** — IP address of the PC running pc-link
   - **Port** — Port pc-link listens on (default: `8990`)
   - **API Token** — Bearer token configured in pc-link
   - **MAC Address** — MAC address of the PC's network adapter (for Wake-on-LAN)
   - **Turn-off action** — What happens when the switch is turned off: `sleep`, `hibernate`, or `shutdown`
   - **Polling interval** — How often to check PC status in seconds (default: `30`, minimum: `5`)

The integration validates connectivity during setup by querying the `/api/health` endpoint.

### Changing options

After setup, you can change the **turn-off action** and **polling interval** from the integration's options page:

**Settings > Devices & Services > PC Link > Configure**
