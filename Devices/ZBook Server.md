---
type: device
status: online
mode: active
latency_ms: 9.0
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# ZBook Server

> Basement server (Windows · RTSP · media)

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 9.0 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | 100.97.161.68 |
| **HA state** | — |

## Hardware
HP ZBook · DESKTOP-D1H9I0P

## Services
- Glances :61209
- Basement RTSP :8554
- Jellyfin :8096
- SMB ZBookShare :445
- Phantom LAN :19132
- Ollama :11434

## Port check
- **445**: open
- **61209**: open
- **8096**: open
- **8554**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi 5 GHz | bidirectional | routing | up | ZBook wireless uplink |
| → [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | management | up | Hyper-V virtual switch |
| → [[Devices/Jellyfin|Jellyfin]] | Logical / documented link | bidirectional | management | up | Native Windows service · reads D:\ |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | bidirectional | management | up | SSH · SMB · basement services |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Tailscale overlay | bidirectional | routing | up | Remote access overlay |
| ↔ [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | bidirectional | management | up | LAN · basement camera ingest |
| → [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | downstream | upstream | up | Basement RTSP → go2rtc on Home Base Mac |
