---
type: device
status: online
mode: active
latency_ms: 7.1
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-21 17:52:17
---

# Home Assistant

> Automation hub · Docker on Home Base Mac

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 7.1 ms |
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
| ↔ [[Devices/ZBook Server|ZBook Server]] | Windows portproxy | bidirectional | data | up | :8123 LAN bridge |
| ↔ [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | data | up | HA container bind mount |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | HTTP / Web UI | bidirectional | management | up | Dashboard · Obsidian refresh |
| → [[Devices/Kitchen Speaker|Kitchen Speaker]] | Google Cast protocol | downstream | control | up | TTS · media control |
| → [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | downstream | control | degraded | Tuya integration |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
| → [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Home Assistant app | bidirectional | control | up | HA Companion · unknown |
