# Homelab Network Map

Updated: **2026-06-21 17:52:17** from **MF-MAC-905** · Set `HOMELAB_HA_TOKEN` for plug/speaker modes

> **Not a live feed by default.** Obsidian Graph shows wiki-links (topology). Status refreshes when you run `python3 generate_network_map.py`. For auto-refresh, use `network-graph.html` with `--serve`.

## Quick views
- **Graph view** — Obsidian topology (static until refresh)
- **[[network-graph.html]]** — interactive map with medium colors, latency, path health
- **[[Connection Legend]]** — Wi-Fi vs Docker vs Cast explained

## Device status
| Device | Reachable | Mode | Ping |
|--------|-----------|------|------|
| [[Devices/Router Gateway|Router Gateway]] | online | active | 4.4 ms |
| [[Devices/ZBook Server|ZBook Server]] | online | active | 7.2 ms |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | online | active | — |
| [[Devices/Home Assistant|Home Assistant]] | online | active | 7.1 ms |
| [[Devices/Minecraft Paper|Minecraft Paper]] | online | standby | 6.3 ms |
| [[Devices/Phantom Proxy|Phantom Proxy]] | online | standby | 5.5 ms |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | online | active | 0.5 ms |
| [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | online | active | 95.7 ms |
| [[Devices/W09N Smart Frame|W09N Smart Frame]] | online | active | 113.4 ms |
| [[Devices/Kitchen Speaker|Kitchen Speaker]] | online | active | 6.3 ms |
| [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | unknown | unknown | — |
| [[Devices/ESP IoT · plug|ESP IoT · plug]] | online | active | 84.7 ms |
| [[Devices/Unknown · 10.0.0.145|Unknown · 10.0.0.145]] | online | active | 8.3 ms |
| [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | online | active | 113.2 ms |
| [[Devices/Unknown · 10.0.0.17|Unknown · 10.0.0.17]] | online | active | 80.9 ms |
| [[Devices/Unknown · 10.0.0.176|Unknown · 10.0.0.176]] | online | active | 115.0 ms |
| [[Devices/Unknown · 10.0.0.200|Unknown · 10.0.0.200]] | online | active | 130.2 ms |
| [[Devices/Unknown · 10.0.0.32|Unknown · 10.0.0.32]] | offline | offline | — |
| [[Devices/Unknown · 10.0.0.45|Unknown · 10.0.0.45]] | online | active | 33.0 ms |
| [[Devices/Unknown · 10.0.0.78|Unknown · 10.0.0.78]] | online | active | 75.4 ms |
| [[Devices/Unknown · 10.0.0.87|Unknown · 10.0.0.87]] | online | active | 25.6 ms |

## Connection map
| From | To | Medium | Traffic | Path | Notes |
|------|----|--------|---------|------|-------|
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 5 GHz | routing | up | ZBook wireless uplink |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | routing | up | Daily driver Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | routing | up | Family Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/W09N Smart Frame|W09N Smart Frame]] | Wi-Fi 2.4 GHz | routing | up | Frame on 2.4 GHz SSID |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Kitchen Speaker|Kitchen Speaker]] | Wi-Fi | routing | up | Google Home Mini |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya Wi-Fi plugs |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | management | up | Hyper-V virtual switch |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Home Assistant|Home Assistant]] | Windows portproxy | data | up | :8123 LAN bridge |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Home Assistant|Home Assistant]] | Docker bridge (WSL2) | data | up | HA container bind mount |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Docker bridge (WSL2) | data | up | Paper server container |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Docker bridge (WSL2) | data | up | Host-network phantom |
| [[Devices/Minecraft Paper|Minecraft Paper]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Logical / documented link | data | up | Geyser backend :19133 |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | SSH · SMB · HA UI |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | management | up | Dashboard · Obsidian refresh |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/ZBook Server|ZBook Server]] | Tailscale overlay | routing | up | Remote access overlay |
| [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | LAN file share |
| [[Devices/W09N Smart Frame|W09N Smart Frame]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | data | up | Loads /frame-panel tiles |
| [[Devices/W09N Smart Frame|W09N Smart Frame]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 2.4 GHz | data | up | HTTP to HA portproxy |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Kitchen Speaker|Kitchen Speaker]] | Google Cast protocol | control | up | TTS · media control |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | control | degraded | Tuya integration |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | upstream | up | Basement webcam via go2rtc |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · plug|ESP IoT · plug]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.145|Unknown · 10.0.0.145]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.17|Unknown · 10.0.0.17]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.176|Unknown · 10.0.0.176]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.200|Unknown · 10.0.0.200]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.32|Unknown · 10.0.0.32]] | Wi-Fi | routing | degraded | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.45|Unknown · 10.0.0.45]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.78|Unknown · 10.0.0.78]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.87|Unknown · 10.0.0.87]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Assistant|Home Assistant]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Home Assistant app | control | up | HA Companion · unknown |

```mermaid
flowchart LR
  RouterGatewa[Router Gateway]
  ZBookServer[ZBook Server]
  WSLUbuntu[WSL Ubuntu]
  HomeAssistan[Home Assistant]
  MinecraftPap[Minecraft Paper]
  PhantomProxy[Phantom Proxy]
  MacBookProTh[MacBook Pro (This Mac)]
  HomeBaseMacB[HomeBase MacBook Pro]
  W09NSmartFra[W09N Smart Frame]
  KitchenSpeak[Kitchen Speaker]
  TuyaSmartPlu[Tuya Smart Plugs]
  ESPIoTplug[ESP IoT · plug]
  Unknown10001[Unknown · 10.0.0.145]
  ESPIoTLEDstr[ESP IoT · LED strip]
  Unknown10001[Unknown · 10.0.0.17]
  Unknown10001[Unknown · 10.0.0.176]
  Unknown10002[Unknown · 10.0.0.200]
  Unknown10003[Unknown · 10.0.0.32]
  Unknown10004[Unknown · 10.0.0.45]
  Unknown10007[Unknown · 10.0.0.78]
  Unknown10008[Unknown · 10.0.0.87]
  RouterGatewa <-->|Wi-Fi 5 GHz| ZBookServer
  RouterGatewa <-->|Wi-Fi| MacBookProTh
  RouterGatewa <-->|Wi-Fi| HomeBaseMacB
  RouterGatewa <-->|Wi-Fi 2.4 GHz| W09NSmartFra
  RouterGatewa <-->|Wi-Fi| KitchenSpeak
  RouterGatewa <-->|Wi-Fi 2.4 GHz| TuyaSmartPlu
  ZBookServer <-->|Docker bridge | WSLUbuntu
  ZBookServer <-->|Windows portpr| HomeAssistan
  WSLUbuntu <-->|Docker bridge | HomeAssistan
  WSLUbuntu <-->|Docker bridge | MinecraftPap
  WSLUbuntu <-->|Docker bridge | PhantomProxy
  MinecraftPap <-->|Logical / docu| PhantomProxy
  MacBookProTh <-->|Wi-Fi| ZBookServer
  MacBookProTh <-->|HTTP / Web UI| HomeAssistan
  HomeBaseMacB <-->|Wi-Fi| ZBookServer
```
