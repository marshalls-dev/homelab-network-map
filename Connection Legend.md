# Connection Legend

How to read links in [[Network Map]] and [[network-graph.html]].

| Medium | Key | Line style |
|--------|-----|------------|
| Wi-Fi 2.4 GHz | `wifi_2g` | dashed |
| Wi-Fi 5 GHz | `wifi_5g` | solid |
| Wi-Fi | `wifi` | dashed |
| Gigabit Ethernet | `ethernet` | solid |
| Docker bridge (WSL2) | `docker_bridge` | dashed |
| Windows portproxy | `portproxy` | dashed |
| Tailscale overlay | `tailscale` | dashed |
| Cloud API (Tuya) | `cloud_api` | dashed |
| Google Cast protocol | `cast` | dashed |
| RTSP video stream | `rtsp` | solid |
| HTTP / Web UI | `http` | solid |
| Logical / documented link | `logical` | dashed |
| Bluetooth (personal) | `bluetooth` | dashed |
| Home Assistant app | `ha_mobile` | dashed |

## Traffic types
| Type | Meaning |
|------|---------|
| **routing** | IP packets to/from gateway |
| **management** | SSH, SMB, dashboards, admin |
| **control** | HA commands to devices |
| **data** | Media, game, or sensor payloads |
| **upstream** | Device → server (camera RTSP) |
| **downstream** | Server → device (dashboard, TTS) |

## Device modes
| Mode | Meaning |
|------|---------|
| **active** | Service running or device in use |
| **standby** | Reachable but idle |
| **playing / idle** | Cast speaker state (needs HA token) |
| **on / off / all_off** | Smart plug states (needs HA token) |
| **offline** | Ping/probe failed |
| **unknown** | Not probed or needs HA API token |

Set `HOMELAB_HA_TOKEN` for live plug/speaker/camera modes.
