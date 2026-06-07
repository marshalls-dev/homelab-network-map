# Homelab Network Map

Updated: **2026-06-07 12:06:57** from **MF-MAC-905** · HA entity modes live

> **Not a live feed by default.** Obsidian Graph shows wiki-links (topology). Status refreshes when you run `python3 generate_network_map.py`. For auto-refresh, use `network-graph.html` with `--serve`.

## Quick views
- **Graph view** — Obsidian topology (static until refresh)
- **[[network-graph.html]]** — interactive map with medium colors, latency, path health
- **[[Connection Legend]]** — Wi-Fi vs Docker vs Cast explained

## Device status
| Device | Reachable | Mode | Ping |
|--------|-----------|------|------|
| [[Devices/Router Gateway|Router Gateway]] | online | active | 5.0 ms |
| [[Devices/ZBook Server|ZBook Server]] | online | active | 5.0 ms |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | online | active | — |
| [[Devices/Home Assistant|Home Assistant]] | online | active | 24.6 ms |
| [[Devices/Minecraft Paper|Minecraft Paper]] | online | standby | 40.0 ms |
| [[Devices/Phantom Proxy|Phantom Proxy]] | online | standby | 39.9 ms |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | online | active | 0.3 ms |
| [[Devices/Old MacBook Pro|Old MacBook Pro]] | online | active | 176.2 ms |
| [[Devices/Home Panel Droid|Home Panel Droid]] | online | active | 66.7 ms |
| [[Devices/Chromecast|Chromecast]] | online | active | 32.1 ms |
| [[Devices/Kitchen speaker|Kitchen speaker]] | unknown | unknown | — |
| [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | unknown | unknown | — |
| [[Devices/ZBook Basement|ZBook Basement]] | online | active | — |
| [[Devices/ESP IoT · plug|ESP IoT · plug]] | online | active | 69.9 ms |
| [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | offline | offline | — |
| [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | online | active | 10.3 ms |
| [[Devices/Fire Tablet|Fire Tablet]] | online | active | 117.9 ms |
| [[Devices/iPad|iPad]] | online | unknown | 680.0 ms |
| [[Devices/LAN device · 45|LAN device · 45]] | online | active | 16.2 ms |
| [[Devices/Smart Refrigerator|Smart Refrigerator]] | online | active | 46.3 ms |
| [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | unknown | unknown | — |
| [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | unknown | unknown | — |

## Connection map
| From | To | Medium | Traffic | Path | Notes |
|------|----|--------|---------|------|-------|
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 5 GHz | routing | up | ZBook wireless uplink |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | routing | up | Daily driver Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Old MacBook Pro|Old MacBook Pro]] | Wi-Fi | routing | up | Family Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Panel Droid|Home Panel Droid]] | Wi-Fi 2.4 GHz | routing | up | Frame on 2.4 GHz SSID |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Chromecast|Chromecast]] | Wi-Fi | routing | up | Cast discovery |
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
| [[Devices/Old MacBook Pro|Old MacBook Pro]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | LAN file share |
| [[Devices/Home Panel Droid|Home Panel Droid]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | data | up | Loads /frame-panel tiles |
| [[Devices/Home Panel Droid|Home Panel Droid]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 2.4 GHz | data | up | HTTP to HA portproxy |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Kitchen speaker|Kitchen speaker]] | Google Cast protocol | control | degraded | TTS · media control |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | control | degraded | Tuya integration |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Chromecast|Chromecast]] | Google Cast protocol | control | up | Cast discovery |
| [[Devices/Chromecast|Chromecast]] | [[Devices/Kitchen speaker|Kitchen speaker]] | Google Cast protocol | data | degraded | Speaker group / Cast route |
| [[Devices/ZBook Basement|ZBook Basement]] | [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | upstream | up | Camera stream to HA |
| [[Devices/ZBook Basement|ZBook Basement]] | [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | upstream | up | go2rtc in WSL |
| [[Devices/ZBook Basement|ZBook Basement]] | [[Devices/ZBook Server|ZBook Server]] | Logical / documented link | upstream | up | Host camera passthrough |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · plug|ESP IoT · plug]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | Wi-Fi | routing | degraded | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Fire Tablet|Fire Tablet]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/iPad|iPad]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LAN device · 45|LAN device · 45]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Smart Refrigerator|Smart Refrigerator]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Assistant|Home Assistant]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Home Panel Droid|Home Panel Droid]] | Home Assistant app | control | up | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | Home Assistant app | control | degraded | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/iPad|iPad]] | Home Assistant app | control | up | HA Companion · unknown |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | Home Assistant app | control | degraded | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | Home Assistant app | control | degraded | HA Companion · home |

```mermaid
flowchart LR
  RouterGatewa[Router Gateway]
  ZBookServer[ZBook Server]
  WSLUbuntu[WSL Ubuntu]
  HomeAssistan[Home Assistant]
  MinecraftPap[Minecraft Paper]
  PhantomProxy[Phantom Proxy]
  MacBookProTh[MacBook Pro (This Mac)]
  OldMacBookPr[Old MacBook Pro]
  HomePanelDro[Home Panel Droid]
  Chromecast[Chromecast]
  Kitchenspeak[Kitchen speaker]
  TuyaSmartPlu[Tuya Smart Plugs]
  ZBookBasemen[ZBook Basement]
  ESPIoTplug[ESP IoT · plug]
  StephanieClr[Stephanie Cléroux’s iPhone]
  ESPIoTLEDstr[ESP IoT · LED strip]
  FireTablet[Fire Tablet]
  iPad[iPad]
  LANdevice45[LAN device · 45]
  SmartRefrige[Smart Refrigerator]
  MashallSprat[Mashall Spratt’s iPhone]
  HomeBaseMacb[HomeBase_Macbook]
  RouterGatewa <-->|Wi-Fi 5 GHz| ZBookServer
  RouterGatewa <-->|Wi-Fi| MacBookProTh
  RouterGatewa <-->|Wi-Fi| OldMacBookPr
  RouterGatewa <-->|Wi-Fi 2.4 GHz| HomePanelDro
  RouterGatewa <-->|Wi-Fi| Chromecast
  RouterGatewa <-->|Wi-Fi 2.4 GHz| TuyaSmartPlu
  ZBookServer <-->|Docker bridge | WSLUbuntu
  ZBookServer <-->|Windows portpr| HomeAssistan
  WSLUbuntu <-->|Docker bridge | HomeAssistan
  WSLUbuntu <-->|Docker bridge | MinecraftPap
  WSLUbuntu <-->|Docker bridge | PhantomProxy
  MinecraftPap <-->|Logical / docu| PhantomProxy
  MacBookProTh <-->|Wi-Fi| ZBookServer
  MacBookProTh <-->|HTTP / Web UI| HomeAssistan
  OldMacBookPr <-->|Wi-Fi| ZBookServer
```
