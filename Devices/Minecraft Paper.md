---
type: device
status: online
mode: active
latency_ms: 5.8
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# Minecraft Paper

> Java + Bedrock cross-play · Docker

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 5.8 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Docker · 2G RAM · Geyser + Floodgate

## Services
- Java :25565
- Geyser backend :19133

## Port check
- **25565**: open


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | data | up | Paper server container |
| ↔ [[Devices/Phantom Proxy|Phantom Proxy]] | Windows portproxy | bidirectional | data | up | Windows Phantom → WSL Geyser :19133 |
| ↔ [[Devices/Xbox One|Xbox One]] | Minecraft Bedrock (UDP) | bidirectional | data | available | Bedrock gameplay · Geyser/Floodgate |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
