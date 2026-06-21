---
type: device
status: online
mode: active
latency_ms: 7.2
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-21 17:52:17
---

# ZBook Server

> Basement server (Windows · RTSP · media)

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 7.2 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | 100.97.161.68 |
| **HA state** | — |

## Hardware
HP ZBook · DESKTOP-D1H9I0P

## Services
- Glances :61209
- Basement RTSP :8554
- SMB ZBookShare :445
- Ollama :11434

## Port check
- **445**: open
- **61209**: open
- **8554**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi 5 GHz | bidirectional | routing | up | ZBook wireless uplink |
| → [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | management | up | Hyper-V virtual switch |
| → [[Devices/Home Assistant|Home Assistant]] | Windows portproxy | bidirectional | data | up | :8123 LAN bridge |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | bidirectional | management | up | SSH · SMB · HA UI |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Tailscale overlay | bidirectional | routing | up | Remote access overlay |
| ↔ [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | bidirectional | management | up | LAN file share |
| → [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | — | upstream | up | Basement webcam via go2rtc |
