---
type: device
status: online
mode: active
latency_ms: 5.2
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# Home Assistant

> Automation hub · Docker on Home Base Mac

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 5.2 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.8 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Docker Compose · Trusted Networks auth

## Services
- /live-kiosk
- /frame-panel
- Tuya plugs
- Cast
- Robot Intercom
- go2rtc :1984

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Docker bridge (WSL2) | bidirectional | data | up | Docker Compose on Home Base Mac |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | HTTP / Web UI | bidirectional | management | up | HA UI · dashboards |
| → [[Devices/Kitchen Speaker|Kitchen Speaker]] | Google Cast protocol | downstream | control | up | TTS · media control |
| → [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | downstream | control | degraded | Tuya integration |
| → [[Devices/Plug 1 · Desk|Plug 1 · Desk]] | Cloud API (Tuya) | downstream | control | degraded | Tuya via Home Assistant |
| → [[Devices/Plug 2 · Shed|Plug 2 · Shed]] | Cloud API (Tuya) | downstream | control | degraded | Tuya via Home Assistant |
| → [[Devices/Plug 3 · Command Central|Plug 3 · Command Central]] | Cloud API (Tuya) | downstream | control | degraded | Tuya via Home Assistant |
| → [[Devices/Plug 4|Plug 4]] | Cloud API (Tuya) | downstream | control | degraded | Tuya via Home Assistant |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
| → [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Home Assistant app | bidirectional | control | up | HA Companion · unknown |
