---
type: device
status: online
mode: active
latency_ms: 57.7
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# HomeBase MacBook Pro

> Primary HA host · Home Base Mac

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 57.7 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.8 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
HomeBases-MBP · Tests-MacBook-Pro

## Services
- Home Assistant :8123
- go2rtc :1984
- Glances :61208
- Home Assistant Companion

## Port check
- **1984**: open
- **61208**: open
- **8123**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Home Base Mac · primary HA host |
| → [[Devices/Home Assistant|Home Assistant]] | Docker bridge (WSL2) | bidirectional | data | up | Docker Compose on Home Base Mac |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | bidirectional | management | up | Home Base Mac · deploy |
| → [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | bidirectional | management | up | LAN · basement camera ingest |
| ↔ [[Devices/Home Assistant|Home Assistant]] | Home Assistant app | bidirectional | control | up | HA Companion · unknown |
