---
type: device
status: online
mode: active
latency_ms: 41.0
packet_loss_pct: 0.0
tags: [homelab, homeassistant]
generated: 2026-07-12 12:00:00
---

# Jellyfin

> Media server · VERBATIM HD (D:)

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | 41.0 ms |
| **Packet loss** | 0.0% |
| **Address** | 10.0.0.169 |
| **Tailscale** | — |
| **HA state** | — |

## Hardware
Native Windows app on ZBook (not Docker/WSL)

## Services
- HTTP :8096
- Library scan · D:\

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| ↔ [[Devices/Xbox One|Xbox One]] | HTTP / Web UI | bidirectional | data | available | Jellyfin app · streams from ZBook |
| ↔ [[Devices/ZBook Server|ZBook Server]] | Logical / documented link | bidirectional | management | up | Native Windows service · reads D:\ |
| ↔ [[Devices/Router Gateway|Router Gateway]] | Wi-Fi | bidirectional | routing | up | Helix / LAN Wi‑Fi |
