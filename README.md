# Homelab Network Space Map

A live **3D network topology** and **Obsidian vault** for a Home Assistant homelab. One Python scanner on your Mac discovers LAN clients, merges Home Assistant device trackers, and renders an interactive space map anyone on Wi‑Fi can open in a browser.

![Homelab Network Space Map](https://img.shields.io/badge/python-3.10+-blue) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-integrated-41BDF5)

## What you get

| Output | Purpose |
|--------|---------|
| **`network-graph.html`** | Interactive 3D force graph — orbit, zoom, drag nodes, click for capability cards |
| **`network-data.json`** | Graph payload (nodes, edges, metrics, legend) |
| **Obsidian vault** | Device notes, wiki-links, static graph view |
| **`Network Map.md`** | Human-readable scan summary |

Each physical device is **one node**. Connections are **not** duplicated — a phone on Wi‑Fi and in Home Assistant shows **two edges**: router (yellow) and HA Companion (teal).

## Architecture

```
Mac (scanner) ── ARP scan ──► Videotron Helix LAN (10.0.0.x)
     │
     ├── Home Assistant API ──► device_tracker.*, media_player.*, switch.*
     ├── Glances API ──► ZBook live CPU/RAM/disk
     └── generate_network_map.py ──► network-data.json + HTML

Browser (any device) ── HTTP :8765 ──► network-graph.html  (with --serve)
```

**Single source of truth for “who is online”:** the Mac’s ARP table (proxy for router-active clients). Optional `router-online.json` merges IPs exported from the Helix admin page. Stale ghosts (e.g. old ARP entries) are filtered out.

## Quick start

### Requirements

- **Python 3.10+** (stdlib only — no pip packages)
- **Mac on the same LAN** as your homelab (runs the scanner)
- **Home Assistant** long-lived token (optional but recommended)
- **Obsidian** (optional — for notes and wiki graph)

### One-time setup

```bash
cd ~/HomelabNetwork

# Home Assistant token (pick one)
cp ha-token.local.example ha-token.local   # paste token inside
# or: export HOMELAB_HA_TOKEN="your-token"

# Label your LAN clients (IPs from router DHCP / ARP scan)
cp known-clients.example.json known-clients.json
# edit names for phones, tablets, IoT

# Optional: Helix hostname hints for ESP devices
# helix-router.json is included as a starting point

# Optional: extra static devices
cp extra-devices.example.json extra-devices.json
```

Create a HA token: **Profile → Security → Long-Lived Access Tokens**.

### Generate once

```bash
python3 generate_network_map.py
```

Opens nothing by default. Outputs update in this folder.

### Live dashboard (recommended)

```bash
python3 generate_network_map.py --serve
```

| URL | Who |
|-----|-----|
| `http://127.0.0.1:8765/network-graph.html` | On the Mac |
| `http://<mac-lan-ip>:8765/network-graph.html` | iPad, iPhone, other Macs on Wi‑Fi |
| `http://<tailscale-ip>:8765/network-graph.html` | Remote via Tailscale |

The server binds to **`0.0.0.0`** by default and **auto-regenerates every 30 seconds**. Only the Mac runs Python; every other device just opens the link.

Your device gets a **📍 You are here** pin (matched by LAN IP or hostname on the host).

### CLI options

```bash
python3 generate_network_map.py --help

  --zbook IP          ZBook / HA host (default: 10.0.0.169)
  --open              Open HTML in browser after generate
  --serve             HTTP server on port 8765 + auto-refresh
  --bind 0.0.0.0      Listen on all interfaces (LAN access)
  --interval 30       Regenerate interval when serving (seconds)
  --watch N           Regenerate every N seconds without server
```

## Connection legend

| Medium | Color | Meaning |
|--------|-------|---------|
| `wifi` / `wifi_5g` | Orange | Helix / LAN Wi‑Fi |
| `wifi_2g` | Orange dashed | 2.4 GHz (frame, some IoT) |
| `ha_mobile` | Teal | Home Assistant Companion app |
| `http` | Purple | Web UI (HA dashboards, frame panel) |
| `docker_bridge` | Purple dashed | WSL2 Docker internal |
| `portproxy` | Cyan dashed | Windows portproxy → HA |
| `tailscale` | Green dashed | Tailscale overlay |
| `cast` | Yellow | Google Cast control |
| `rtsp` | Red | Camera stream → HA |
| `cloud_api` | Gray | Tuya cloud |
| `bluetooth` | Light blue | Personal audio peripherals |
| `logical` | Gray dashed | Documented, not probed |

Hover a link for latency and health. Click a node for the **capability card** (RAM, storage, compute score, live Glances metrics, HA entity state).

## Configuration files

| File | Committed? | Purpose |
|------|------------|---------|
| `generate_network_map.py` | Yes | Scanner, merger, probe, server |
| `network-graph-template.html` | Yes | 3D UI (Three.js + 3d-force-graph) |
| `known-clients.json` | **No** (gitignored) | Your IP/MAC → friendly names |
| `known-clients.example.json` | Yes | Template |
| `ha-token.local` | **No** (gitignored) | HA API token |
| `ha-token.local.example` | Yes | Template |
| `helix-router.json` | Yes | Videotron Helix ESP hostname hints |
| `router-online.json` | **No** (gitignored) | Optional Helix “connected devices” export |
| `router-online.example.json` | Yes | Template |
| `extra-devices.json` | **No** (gitignored) | Manual devices (headphones, etc.) |
| `extra-devices.example.json` | Yes | Template |
| `node-positions.json` | **No** (gitignored) | Saved 3D layout from browser |

### Labeling unknown LAN clients

Each scan prints unlabeled ARP entries:

```
[i] Unlabeled LAN clients (match in router DHCP, then add to known-clients.json):
    10.0.0.45  aa:bb:cc:dd:ee:ff
```

Add an entry under `by_ip` or `by_mac` in `known-clients.json`. Re-run the generator — duplicates merge into one canonical node.

### Router-only truth

Devices appear on the map only if they are:

1. In the **current ARP scan** (or `router-online.json`), or  
2. **Core infrastructure** (router, ZBook, WSL, HA, nested services), or  
3. **HA device_trackers** without LAN IP yet (HA link only until IP is seen)

Mark stale ghosts with `"stale": true` in `known-clients.json` to hide them even if ARP still lists them.

## 3D map controls

| Action | Control |
|--------|---------|
| Orbit | Left-drag empty space |
| Zoom | Scroll / middle-drag |
| Pan | Right-drag |
| Pin a node | Drag the node |
| Unpin | Double-click node |
| Save layout | **Save layout** button → `node-positions.json` |
| Reset layout | **Reset layout** button |

## Home Assistant integration

With a token set, the generator:

- Adds **`device_tracker.*`** phones/tablets (merged into `known-clients` entries)
- Maps canonical IDs (e.g. `marshall-iphone`, `wife-iphone`, `family-ipad`, `w09n-frame`)
- Adds **`ha_mobile`** edges from `homeassistant` → each tracked device
- Reads switch/media_player states for plugs, speakers, cameras
- Shows HA-off warning in the UI when the token is missing

## Nested services (runs_on)

Services that run inside other hosts appear as smaller nested nodes tethered to their parent:

- **Home Assistant**, **Minecraft**, **Phantom**, **Webcam** → run on **ZBook / WSL**
- Purple nest tethers and `↳` label prefix in the 3D view

## Obsidian

1. Install [Obsidian](https://obsidian.md)
2. **Open folder as vault** → this directory
3. Read **[[Connection Legend]]** and **[[Network Map]]**
4. Use **Graph view** for wiki-link topology (static; no live latency)

Obsidian graph ≠ live HTML dashboard. Use `--serve` for real-time path health.

## Project layout

```
HomelabNetwork/
├── generate_network_map.py      # Main generator + HTTP server
├── network-graph-template.html  # 3D dashboard shell
├── network-graph.html           # Generated (committed as demo snapshot)
├── network-data.json            # Generated graph payload
├── Connection Legend.md         # Medium reference (generated)
├── Network Map.md               # Scan summary (generated)
├── Devices/                     # Per-device Obsidian notes (generated)
├── helix-router.json            # Helix ESP MAC hints
├── known-clients.example.json
├── ha-token.local.example
├── router-online.example.json
├── extra-devices.example.json
└── .obsidian/                   # Vault settings
```

## Not the ZBook copy

`C:\Users\serveradmin\NetworkVault` on the Windows ZBook is a separate folder. **This Mac vault (`~/HomelabNetwork`) is the daily-driver source.**

## License

Personal homelab project. Adapt freely for your own network; scrub IPs and tokens before publishing.
