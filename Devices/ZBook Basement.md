---
type: device
status: online
mode: active
latency_ms: null
packet_loss_pct: null
tags: [homelab, homeassistant]
generated: 2026-06-07 12:06:57
---

# ZBook Basement

> Basement camera feed · go2rtc in WSL

| Field | Value |
|-------|-------|
| **Reachability** | **online** |
| **Mode** | **active** |
| **Ping avg** | — |
| **Packet loss** | — |
| **Address** | 172.27.128.1 |
| **Tailscale** | — |
| **HA state** | Basement Webcam: idle |

## Hardware
go2rtc · camera.172_27_128_1

## Services
- RTSP
- HA picture-glance

## Connections
| Link | Medium | Direction | Traffic | Path | Notes |
|------|--------|-----------|---------|------|-------|
| → [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | — | upstream | up | Camera stream to HA |
| → [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | — | upstream | up | go2rtc in WSL |
| → [[Devices/ZBook Server|ZBook Server]] | Logical / documented link | — | upstream | up | Host camera passthrough |
