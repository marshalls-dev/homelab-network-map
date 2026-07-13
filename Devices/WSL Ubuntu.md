---
type: device
status: online
mode: active
latency_ms: null
packet_loss_pct: null
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# WSL Ubuntu

> Docker engine on ZBook

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | — |
| **Packet loss** | — |
| **Address** | 172.27.133.182 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Ubuntu WSL2 · Docker

## Services
- Docker
- Minecraft Paper+Geyser

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/ZBook Server|ZBook Server]] | Docker bridge (WSL2) | bidirectional | management | up | Hyper-V virtual switch |
| → [[Devices/Minecraft Paper|Minecraft Paper]] | Docker bridge (WSL2) | bidirectional | data | up | Paper server container |
