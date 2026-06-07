---
type: device
status: online
mode: active
latency_ms: 5.0
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-07 12:06:57
---

# ZBook Server

> Home lab host (Windows + WSL2)

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 5.0 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | 100.97.161.68 |
| **HA state** | — |

## Hardware
HP ZBook · DESKTOP-D1H9I0P

## Services
- Home Assistant :8123
- Cockpit :9090
- Glances :61208
- SMB ZBookShare :445

## Port check
- **445**: open
- **61208**: open
- **8123**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi 5 GHz | bidirectional | routing | up | ZBook wireless uplink |
| → [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | management | up | Hyper-V virtual switch |
| → [[Devices/Home Assistant|Home Assistant]] | Windows portproxy | bidirectional | data | up | :8123 LAN bridge |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | bidirectional | management | up | SSH · SMB · HA UI |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Tailscale overlay | bidirectional | routing | up | Remote access overlay |
| ↔ [[Devices/Old MacBook Pro|Old MacBook Pro]] | Wi-Fi | bidirectional | management | up | LAN file share |
