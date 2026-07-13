# Homelab Network Map

Updated: **2026-07-12 12:00:00** from **MF-MAC-905** · Set `HOMELAB_HA_TOKEN` for plug/speaker modes

> **Not a live feed by default.** Obsidian Graph shows wiki-links (topology). Status refreshes when you run `python3 generate_network_map.py`. For auto-refresh, use `network-graph.html` with `--serve`.

## Quick views
- **Graph view** — Obsidian topology (static until refresh)
- **[[network-graph.html]]** — interactive map with medium colors, latency, path health
- **[[Connection Legend]]** — Wi-Fi vs Docker vs Cast explained

## Device status
| Device | Reachable | Mode | Ping |
|--------|-----------|------|------|
| [[Devices/Router Gateway|Router Gateway]] | online | active | 4.8 ms |
| [[Devices/ZBook Server|ZBook Server]] | online | active | 9.0 ms |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | online | active | — |
| [[Devices/Home Assistant|Home Assistant]] | online | active | 5.2 ms |
| [[Devices/Minecraft Paper|Minecraft Paper]] | online | active | 5.8 ms |
| [[Devices/Phantom Proxy|Phantom Proxy]] | online | standby | 28.9 ms |
| [[Devices/Jellyfin|Jellyfin]] | online | active | 41.0 ms |
| [[Devices/LG Basement Projector|LG Basement Projector]] | offline | offline | — |
| [[Devices/Xbox One|Xbox One]] | online | active | — |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | online | active | 0.5 ms |
| [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | online | active | 57.7 ms |
| [[Devices/W09N Smart Frame|W09N Smart Frame]] | online | active | 88.7 ms |
| [[Devices/Kitchen Speaker|Kitchen Speaker]] | online | active | 27.4 ms |
| [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | unknown | unknown | — |
| [[Devices/Wife's iPhone|Wife's iPhone]] | online | active | 108.7 ms |
| [[Devices/Family iPad|Family iPad]] | online | active | 692.9 ms |
| [[Devices/Fire Tablet|Fire Tablet]] | offline | offline | — |
| [[Devices/Plug 1 · Desk|Plug 1 · Desk]] | unknown | unknown | — |
| [[Devices/Plug 2 · Shed|Plug 2 · Shed]] | unknown | unknown | — |
| [[Devices/Plug 3 · Command Central|Plug 3 · Command Central]] | unknown | unknown | — |
| [[Devices/Plug 4|Plug 4]] | unknown | unknown | — |
| [[Devices/Primary MacBook Air|Primary MacBook Air]] | unknown | unknown | — |
| [[Devices/Smart Refrigerator|Smart Refrigerator]] | unknown | unknown | — |
| [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | online | standby | 68.9 ms |
| [[Devices/ESP IoT · plug|ESP IoT · plug]] | online | standby | 109.8 ms |
| [[Devices/Tuya Smart Bulb|Tuya Smart Bulb]] | unknown | unknown | — |
| [[Devices/Tuya LED Strip|Tuya LED Strip]] | unknown | unknown | — |
| [[Devices/LG Washer|LG Washer]] | unknown | unknown | — |
| [[Devices/LG Dryer|LG Dryer]] | unknown | unknown | — |
| [[Devices/WLAN Device|WLAN Device]] | unknown | unknown | — |
| [[Devices/Family Frame Tablet|Family Frame Tablet]] | unknown | unknown | — |
| [[Devices/Unknown · 10.0.0.32|Unknown · 10.0.0.32]] | online | active | — |
| [[Devices/Unknown · 10.0.0.87|Unknown · 10.0.0.87]] | online | active | 7.4 ms |

## Connection map
| From | To | Medium | Traffic | Path | Notes |
|------|----|--------|---------|------|-------|
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 5 GHz | routing | up | ZBook wireless uplink |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | Wi-Fi | routing | up | Daily driver Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | routing | up | Home Base Mac · primary HA host |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/W09N Smart Frame|W09N Smart Frame]] | Wi-Fi 2.4 GHz | routing | up | Frame on 2.4 GHz SSID |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Kitchen Speaker|Kitchen Speaker]] | Wi-Fi | routing | up | Google Home Mini |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya Wi-Fi plugs |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | management | up | Hyper-V virtual switch |
| [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | [[Devices/Home Assistant|Home Assistant]] | Docker bridge (WSL2) | data | up | Docker Compose on Home Base Mac |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Docker bridge (WSL2) | data | up | Paper server container |
| [[Devices/Phantom Proxy|Phantom Proxy]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Windows portproxy | data | up | Windows Phantom → WSL Geyser :19133 |
| [[Devices/Xbox One|Xbox One]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Minecraft Bedrock (UDP) | data | available | LAN discovery UDP :19132 · Friends tab |
| [[Devices/Xbox One|Xbox One]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Minecraft Bedrock (UDP) | data | available | Bedrock gameplay · Geyser/Floodgate |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Xbox One|Xbox One]] | Wi-Fi | routing | up | Basement Xbox · LAN |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LG Basement Projector|LG Basement Projector]] | Wi-Fi | routing | degraded | LG PF1500W · webOS management |
| [[Devices/Xbox One|Xbox One]] | [[Devices/LG Basement Projector|LG Basement Projector]] | HDMI video | data | degraded | HDMI video → projector screen |
| [[Devices/Xbox One|Xbox One]] | [[Devices/Jellyfin|Jellyfin]] | HTTP / Web UI | data | available | Jellyfin app · streams from ZBook |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Jellyfin|Jellyfin]] | Logical / documented link | management | up | Native Windows service · reads D:\ |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | SSH · SMB · basement services |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | management | up | HA UI · dashboards |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Wi-Fi | management | up | Home Base Mac · deploy |
| [[Devices/MacBook Pro (This Mac)|MacBook Pro (This Mac)]] | [[Devices/ZBook Server|ZBook Server]] | Tailscale overlay | routing | up | Remote access overlay |
| [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | LAN · basement camera ingest |
| [[Devices/W09N Smart Frame|W09N Smart Frame]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | data | up | Loads /frame-panel from Home Base HA |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Kitchen Speaker|Kitchen Speaker]] | Google Cast protocol | control | up | TTS · media control |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | control | degraded | Tuya integration |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | upstream | up | Basement RTSP → go2rtc on Home Base Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Wife's iPhone|Wife's iPhone]] | Wi-Fi | routing | up | Known client · catalog |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Family iPad|Family iPad]] | Wi-Fi | routing | up | Known client · catalog |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Fire Tablet|Fire Tablet]] | Wi-Fi | routing | degraded | Known client · catalog |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Plug 1 · Desk|Plug 1 · Desk]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya plug · catalog |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Plug 1 · Desk|Plug 1 · Desk]] | Cloud API (Tuya) | control | degraded | Tuya via Home Assistant |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Plug 2 · Shed|Plug 2 · Shed]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya plug · catalog |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Plug 2 · Shed|Plug 2 · Shed]] | Cloud API (Tuya) | control | degraded | Tuya via Home Assistant |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Plug 3 · Command Central|Plug 3 · Command Central]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya plug · catalog |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Plug 3 · Command Central|Plug 3 · Command Central]] | Cloud API (Tuya) | control | degraded | Tuya via Home Assistant |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Plug 4|Plug 4]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya plug · catalog |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Plug 4|Plug 4]] | Cloud API (Tuya) | control | degraded | Tuya via Home Assistant |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Primary MacBook Air|Primary MacBook Air]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Smart Refrigerator|Smart Refrigerator]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | Wi-Fi | routing | up | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · plug|ESP IoT · plug]] | Wi-Fi | routing | up | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya Smart Bulb|Tuya Smart Bulb]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya LED Strip|Tuya LED Strip]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LG Washer|LG Washer]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LG Dryer|LG Dryer]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/WLAN Device|WLAN Device]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Family Frame Tablet|Family Frame Tablet]] | Wi-Fi | routing | degraded | Helix catalog · offline OK |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.32|Unknown · 10.0.0.32]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Unknown · 10.0.0.87|Unknown · 10.0.0.87]] | Wi-Fi | routing | up | LAN ARP discovery |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Assistant|Home Assistant]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Jellyfin|Jellyfin]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/HomeBase MacBook Pro|HomeBase MacBook Pro]] | Home Assistant app | control | up | HA Companion · unknown |

```mermaid
flowchart LR
  RouterGatewa[Router Gateway]
  ZBookServer[ZBook Server]
  WSLUbuntu[WSL Ubuntu]
  HomeAssistan[Home Assistant]
  MinecraftPap[Minecraft Paper]
  PhantomProxy[Phantom Proxy]
  Jellyfin[Jellyfin]
  LGBasementPr[LG Basement Projector]
  XboxOne[Xbox One]
  MacBookProTh[MacBook Pro (This Mac)]
  HomeBaseMacB[HomeBase MacBook Pro]
  W09NSmartFra[W09N Smart Frame]
  KitchenSpeak[Kitchen Speaker]
  TuyaSmartPlu[Tuya Smart Plugs]
  WifesiPhone[Wife's iPhone]
  FamilyiPad[Family iPad]
  FireTablet[Fire Tablet]
  Plug1Desk[Plug 1 · Desk]
  Plug2Shed[Plug 2 · Shed]
  Plug3Command[Plug 3 · Command Central]
  Plug4[Plug 4]
  PrimaryMacBo[Primary MacBook Air]
  SmartRefrige[Smart Refrigerator]
  ESPIoTLEDstr[ESP IoT · LED strip]
  ESPIoTplug[ESP IoT · plug]
  TuyaSmartBul[Tuya Smart Bulb]
  TuyaLEDStrip[Tuya LED Strip]
  LGWasher[LG Washer]
  LGDryer[LG Dryer]
  WLANDevice[WLAN Device]
  FamilyFrameT[Family Frame Tablet]
  Unknown10003[Unknown · 10.0.0.32]
  Unknown10008[Unknown · 10.0.0.87]
  RouterGatewa <-->|Wi-Fi 5 GHz| ZBookServer
  RouterGatewa <-->|Wi-Fi| MacBookProTh
  RouterGatewa <-->|Wi-Fi| HomeBaseMacB
  RouterGatewa <-->|Wi-Fi 2.4 GHz| W09NSmartFra
  RouterGatewa <-->|Wi-Fi| KitchenSpeak
  RouterGatewa <-->|Wi-Fi 2.4 GHz| TuyaSmartPlu
  ZBookServer <-->|Docker bridge | WSLUbuntu
  HomeBaseMacB <-->|Docker bridge | HomeAssistan
  WSLUbuntu <-->|Docker bridge | MinecraftPap
  PhantomProxy <-->|Windows portpr| MinecraftPap
  XboxOne <-->|Minecraft Bedr| PhantomProxy
  XboxOne <-->|Minecraft Bedr| MinecraftPap
  RouterGatewa <-->|Wi-Fi| XboxOne
  RouterGatewa <-->|Wi-Fi| LGBasementPr
  XboxOne <-->|HDMI video| LGBasementPr
  XboxOne <-->|HTTP / Web UI| Jellyfin
```
