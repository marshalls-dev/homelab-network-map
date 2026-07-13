---
type: device
status: online
mode: active
latency_ms: null
packet_loss_pct: 100.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# Xbox One

> Basement game + media client

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | — |
| **Packet loss** | 100.0% |
| **Address** | 10.0.0.145 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Xbox One · Minecraft Bedrock · Jellyfin app

## Services
- Jellyfin client
- Minecraft Bedrock LAN

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| → [[Devices/Phantom Proxy|Phantom Proxy]] | Minecraft Bedrock (UDP) | bidirectional | data | available | LAN discovery UDP :19132 · Friends tab |
| → [[Devices/Minecraft Paper|Minecraft Paper]] | Minecraft Bedrock (UDP) | bidirectional | data | available | Bedrock gameplay · Geyser/Floodgate |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Basement Xbox · LAN |
| → [[Devices/LG Basement Projector|LG Basement Projector]] | HDMI video | downstream | data | degraded | HDMI video → projector screen |
| → [[Devices/Jellyfin|Jellyfin]] | HTTP / Web UI | bidirectional | data | available | Jellyfin app · streams from ZBook |
