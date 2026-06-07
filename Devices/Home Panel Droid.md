---
type: device
status: online
mode: active
latency_ms: 66.7
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-07 12:06:57
---

# Home Panel Droid

> HA kiosk display

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 66.7 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.113 |
| **Tailscale** | — |
| **HA state** | device_tracker.home_panel_droid: home |

## Hardware
NexFoto W09N · Android 4.4.2 · WallPanel

## Services
- Firefox
- /frame-panel dashboard

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi 2.4 GHz | bidirectional | routing | up | Frame on 2.4 GHz SSID |
| → [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | downstream | data | up | Loads /frame-panel tiles |
| → [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 2.4 GHz | downstream | data | up | HTTP to HA portproxy |
| ↔ [[Devices/Home Assistant|Home Assistant]] | Home Assistant app | bidirectional | control | up | HA Companion · home |
