---
type: device
status: online
mode: active
latency_ms: 24.6
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-07 12:06:57
---

# Home Assistant

> Automation hub · Docker container

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 24.6 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | https://desktop-d1h9i0p-1.tailf11422.ts.net |
| **HA state** | — |

## Hardware
Docker · Trusted Networks auth

## Services
- /live-kiosk
- /frame-panel
- Tuya plugs
- Cast
- Robot Intercom

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/ZBook Server|ZBook Server]] | Windows portproxy | bidirectional | data | up | :8123 LAN bridge |
| ↔ [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | data | up | HA container bind mount |
| ↔ [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | HTTP / Web UI | bidirectional | management | up | Dashboard · Obsidian refresh |
| → [[Devices/Kitchen speaker|Kitchen speaker]] | Google Cast protocol | downstream | control | degraded | TTS · media control |
| → [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | downstream | control | degraded | Tuya integration |
| → [[Devices/Chromecast|Chromecast]] | Google Cast protocol | downstream | control | up | Cast discovery |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
| → [[Devices/Home Panel Droid|Home Panel Droid]] | Home Assistant app | bidirectional | control | up | HA Companion · home |
| → [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | Home Assistant app | bidirectional | control | degraded | HA Companion · home |
| → [[Devices/iPad|iPad]] | Home Assistant app | bidirectional | control | up | HA Companion · unknown |
| → [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | Home Assistant app | bidirectional | control | degraded | HA Companion · home |
| → [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | Home Assistant app | bidirectional | control | degraded | HA Companion · home |
