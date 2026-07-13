---
type: device
status: online
mode: active
latency_ms: 0.5
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# MacBook Pro (This Mac)

> Daily driver · mf-mac-905

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 0.5 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.227 |
| **Tailscale** | 100.88.199.80 |
| **HA state** | — |

## Hardware
MF-MAC-905 · marshalls

## Services
- Obsidian
- Cursor
- Tailscale

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Daily driver Mac |
| → [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | bidirectional | management | up | SSH · SMB · basement services |
| → [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | bidirectional | management | up | HA UI · dashboards |
| → [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | bidirectional | management | up | Home Base Mac · deploy |
| → [[Devices/ZBook Server|ZBook Server]] | Tailscale overlay | bidirectional | routing | up | Remote access overlay |
