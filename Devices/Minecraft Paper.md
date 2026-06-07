---
type: device
status: online
mode: standby
latency_ms: 40.0
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-07 12:06:57
---

# Minecraft Paper

> Java + Bedrock cross-play · Docker

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **standby** |
| **Ping avg** | 40.0 ms |
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
- **25565**: closed


## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | data | up | Paper server container |
| → [[Devices/Phantom Proxy|Phantom Proxy]] | Logical / documented link | bidirectional | data | up | Geyser backend :19133 |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
