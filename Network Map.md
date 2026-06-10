# Homelab Network Map

Updated: **2026-06-09 23:10:49** from **MF-MAC-905** · HA entity modes live

> **Not a live feed by default.** Obsidian Graph shows wiki-links (topology). Status refreshes when you run `python3 generate_network_map.py`. For auto-refresh, use `network-graph.html` with `--serve`.

## Quick views
- **Graph view** — Obsidian topology (static until refresh)
- **[[network-graph.html]]** — interactive map with medium colors, latency, path health
- **[[Connection Legend]]** — Wi-Fi vs Docker vs Cast explained

## Device status
| Device | Reachable | Mode | Ping |
|--------|-----------|------|------|
| [[Devices/Router Gateway|Router Gateway]] | online | active | 4.6 ms |
| [[Devices/ZBook Server|ZBook Server]] | online | active | 15.4 ms |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | online | active | — |
| [[Devices/Home Assistant|Home Assistant]] | online | active | 44.7 ms |
| [[Devices/Minecraft Paper|Minecraft Paper]] | online | standby | 42.1 ms |
| [[Devices/Phantom Proxy|Phantom Proxy]] | online | standby | 38.8 ms |
| [[Devices/This Mac (Primary Scanner)|This Mac (Primary Scanner)]] | online | active | 0.3 ms |
| [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | online | home | 161.0 ms |
| [[Devices/Home Panel Droid|Home Panel Droid]] | online | active | 86.9 ms |
| [[Devices/Kitchen speaker|Kitchen speaker]] | online | idle | 6.6 ms |
| [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | unknown | unknown | — |
| [[Devices/LG Dryer|LG Dryer]] | offline | offline | — |
| [[Devices/Primary MacBook Air|Primary MacBook Air]] | online | active | 29.6 ms |
| [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | online | home | 42.8 ms |
| [[Devices/Xbox One|Xbox One]] | offline | offline | — |
| [[Devices/LG Washer|LG Washer]] | online | standby | 47.1 ms |
| [[Devices/Smart Refrigerator|Smart Refrigerator]] | online | standby | 98.9 ms |
| [[Devices/WLAN Device|WLAN Device]] | online | standby | 109.0 ms |
| [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | offline | offline | — |
| [[Devices/iPad|iPad]] | offline | offline | — |
| [[Devices/Tuya Smart Bulb|Tuya Smart Bulb]] | offline | offline | — |
| [[Devices/Tuya LED Strip|Tuya LED Strip]] | offline | offline | — |
| [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | online | standby | 32.7 ms |
| [[Devices/ESP IoT · plug|ESP IoT · plug]] | online | standby | 54.9 ms |
| [[Devices/Family iPad|Family iPad]] | offline | offline | — |
| [[Devices/iPhone-61|iPhone-61]] | offline | offline | — |
| [[Devices/70-70-aa-1c-90-48|70:70:aa:1c:90:48]] | offline | offline | — |
| [[Devices/d0-c9-07-ef-aa-d0|d0:c9:07:ef:aa:d0]] | offline | offline | — |
| [[Devices/d0-c9-07-d6-52-78|d0:c9:07:d6:52:78]] | offline | offline | — |
| [[Devices/espressif|espressif]] | online | active | 67.1 ms |
| [[Devices/d0-c9-07-e2-f9-c4|d0:c9:07:e2:f9:c4]] | offline | offline | — |
| [[Devices/ESP DA324B|ESP DA324B]] | online | standby | 78.8 ms |
| [[Devices/ESP 2C6B52|ESP 2C6B52]] | offline | offline | — |
| [[Devices/Family Frame Tablet|Family Frame Tablet]] | offline | offline | — |
| [[Devices/iPhone-60|iPhone-60]] | offline | offline | — |
| [[Devices/iPhone-54|iPhone-54]] | offline | offline | — |

## Connection map
| From | To | Medium | Traffic | Path | Notes |
|------|----|--------|---------|------|-------|
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 5 GHz | routing | up | ZBook wireless uplink |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/This Mac (Primary Scanner)|This Mac (Primary Scanner)]] | Wi-Fi | routing | up | Daily driver Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | Wi-Fi | routing | up | Family Mac |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Panel Droid|Home Panel Droid]] | Wi-Fi 2.4 GHz | routing | up | Frame on 2.4 GHz SSID |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Kitchen speaker|Kitchen speaker]] | Wi-Fi | routing | up | Google Home Mini |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Wi-Fi 2.4 GHz | routing | degraded | Tuya Wi-Fi plugs |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/WSL Ubuntu|WSL Ubuntu]] | Docker bridge (WSL2) | management | up | Hyper-V virtual switch |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Home Assistant|Home Assistant]] | Windows portproxy | data | up | :8123 LAN bridge |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Home Assistant|Home Assistant]] | Docker bridge (WSL2) | data | up | HA container bind mount |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Docker bridge (WSL2) | data | up | Paper server container |
| [[Devices/WSL Ubuntu|WSL Ubuntu]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Docker bridge (WSL2) | data | up | Host-network phantom |
| [[Devices/Minecraft Paper|Minecraft Paper]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Logical / documented link | data | up | Geyser backend :19133 |
| [[Devices/This Mac (Primary Scanner)|This Mac (Primary Scanner)]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | SSH · SMB · HA UI |
| [[Devices/This Mac (Primary Scanner)|This Mac (Primary Scanner)]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | management | up | Dashboard · Obsidian refresh |
| [[Devices/This Mac (Primary Scanner)|This Mac (Primary Scanner)]] | [[Devices/ZBook Server|ZBook Server]] | Tailscale overlay | routing | up | Remote access overlay |
| [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi | management | up | LAN file share |
| [[Devices/Home Panel Droid|Home Panel Droid]] | [[Devices/Home Assistant|Home Assistant]] | HTTP / Web UI | data | up | Loads /frame-panel tiles |
| [[Devices/Home Panel Droid|Home Panel Droid]] | [[Devices/ZBook Server|ZBook Server]] | Wi-Fi 2.4 GHz | data | up | HTTP to HA portproxy |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Kitchen speaker|Kitchen speaker]] | Google Cast protocol | control | up | TTS · media control |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Tuya Smart Plugs|Tuya Smart Plugs]] | Cloud API (Tuya) | control | degraded | Tuya integration |
| [[Devices/ZBook Server|ZBook Server]] | [[Devices/Home Assistant|Home Assistant]] | RTSP video stream | upstream | up | Basement webcam via go2rtc |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LG Dryer|LG Dryer]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Primary MacBook Air|Primary MacBook Air]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Xbox One|Xbox One]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/LG Washer|LG Washer]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Smart Refrigerator|Smart Refrigerator]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/WLAN Device|WLAN Device]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | Wi-Fi 5 GHz | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/iPad|iPad]] | Wi-Fi 5 GHz | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya Smart Bulb|Tuya Smart Bulb]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Tuya LED Strip|Tuya LED Strip]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · LED strip|ESP IoT · LED strip]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP IoT · plug|ESP IoT · plug]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Family iPad|Family iPad]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/iPhone-61|iPhone-61]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/70-70-aa-1c-90-48|70:70:aa:1c:90:48]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/d0-c9-07-ef-aa-d0|d0:c9:07:ef:aa:d0]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/d0-c9-07-d6-52-78|d0:c9:07:d6:52:78]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/espressif|espressif]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/d0-c9-07-e2-f9-c4|d0:c9:07:e2:f9:c4]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP DA324B|ESP DA324B]] | Wi-Fi | routing | up | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/ESP 2C6B52|ESP 2C6B52]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Family Frame Tablet|Family Frame Tablet]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/iPhone-60|iPhone-60]] | Wi-Fi | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/iPhone-54|iPhone-54]] | Wi-Fi 5 GHz | routing | degraded | Helix router registry |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Home Assistant|Home Assistant]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Minecraft Paper|Minecraft Paper]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Router Gateway|Router Gateway]] | [[Devices/Phantom Proxy|Phantom Proxy]] | Wi-Fi | routing | up | Helix / LAN Wi‑Fi |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/HomeBase_Macbook|HomeBase_Macbook]] | Home Assistant app | control | up | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Home Panel Droid|Home Panel Droid]] | Home Assistant app | control | up | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Mashall Spratt’s iPhone|Mashall Spratt’s iPhone]] | Home Assistant app | control | up | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/Stephanie Cléroux’s iPhone|Stephanie Cléroux’s iPhone]] | Home Assistant app | control | degraded | HA Companion · home |
| [[Devices/Home Assistant|Home Assistant]] | [[Devices/iPad|iPad]] | Home Assistant app | control | degraded | HA Companion · home |

```mermaid
flowchart LR
  RouterGatewa[Router Gateway]
  ZBookServer[ZBook Server]
  WSLUbuntu[WSL Ubuntu]
  HomeAssistan[Home Assistant]
  MinecraftPap[Minecraft Paper]
  PhantomProxy[Phantom Proxy]
  ThisMacPrima[This Mac (Primary Scanner)]
  HomeBaseMacb[HomeBase_Macbook]
  HomePanelDro[Home Panel Droid]
  Kitchenspeak[Kitchen speaker]
  TuyaSmartPlu[Tuya Smart Plugs]
  LGDryer[LG Dryer]
  PrimaryMacBo[Primary MacBook Air]
  MashallSprat[Mashall Spratt’s iPhone]
  XboxOne[Xbox One]
  LGWasher[LG Washer]
  SmartRefrige[Smart Refrigerator]
  WLANDevice[WLAN Device]
  StephanieClr[Stephanie Cléroux’s iPhone]
  iPad[iPad]
  TuyaSmartBul[Tuya Smart Bulb]
  TuyaLEDStrip[Tuya LED Strip]
  ESPIoTLEDstr[ESP IoT · LED strip]
  ESPIoTplug[ESP IoT · plug]
  FamilyiPad[Family iPad]
  iPhone61[iPhone-61]
  7070aa1c9048[70:70:aa:1c:90:48]
  d0c907efaad0[d0:c9:07:ef:aa:d0]
  d0c907d65278[d0:c9:07:d6:52:78]
  espressif[espressif]
  d0c907e2f9c4[d0:c9:07:e2:f9:c4]
  ESPDA324B[ESP DA324B]
  ESP2C6B52[ESP 2C6B52]
  FamilyFrameT[Family Frame Tablet]
  iPhone60[iPhone-60]
  iPhone54[iPhone-54]
  RouterGatewa <-->|Wi-Fi 5 GHz| ZBookServer
  RouterGatewa <-->|Wi-Fi| ThisMacPrima
  RouterGatewa <-->|Wi-Fi| HomeBaseMacb
  RouterGatewa <-->|Wi-Fi 2.4 GHz| HomePanelDro
  RouterGatewa <-->|Wi-Fi| Kitchenspeak
  RouterGatewa <-->|Wi-Fi 2.4 GHz| TuyaSmartPlu
  ZBookServer <-->|Docker bridge | WSLUbuntu
  ZBookServer <-->|Windows portpr| HomeAssistan
  WSLUbuntu <-->|Docker bridge | HomeAssistan
  WSLUbuntu <-->|Docker bridge | MinecraftPap
  WSLUbuntu <-->|Docker bridge | PhantomProxy
  MinecraftPap <-->|Logical / docu| PhantomProxy
  ThisMacPrima <-->|Wi-Fi| ZBookServer
  ThisMacPrima <-->|HTTP / Web UI| HomeAssistan
  HomeBaseMacb <-->|Wi-Fi| ZBookServer
```
