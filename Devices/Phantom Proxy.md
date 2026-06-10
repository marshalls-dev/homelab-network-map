---
type: device
status: online
mode: standby
latency_ms: 38.8
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-06-09 23:10:49
---

# Phantom Proxy

> Xbox LAN discovery beacon · Docker host net

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **standby** |
| **Ping avg** | 38.8 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Docker host network on ZBook

## Services
- Bedrock LAN UDP :19132

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | bidirectional | data | up | Host-network phantom |
| ↔ [[Devices/Minecraft Paper|Minecraft Paper]] | Logical / documented link | bidirectional | data | up | Geyser backend :19133 |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
