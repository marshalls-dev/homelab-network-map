---
type: device
status: online
mode: active
latency_ms: 88.7
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# W09N Smart Frame

> HA kiosk display

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 88.7 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.113 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
NexFoto W09N · Android 4.4.2 · WallPanel

## Services
- Firefox
- /frame-panel dashboard

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi 2.4 GHz | bidirectional | routing | up | Frame on 2.4 GHz SSID |
| → [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | downstream | data | up | Loads /frame-panel from Home Base HA |
