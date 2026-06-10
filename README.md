# Homelab Network Space Map

A live **3D network topology** and **Obsidian vault** for a Home Assistant homelab. One Python scanner on your Mac discovers LAN clients, merges Home Assistant device trackers, and renders an interactive space map anyone on Wi‑Fi can open in a browser.

![Homelab Network Space Map](https://img.shields.io/badge/python-3.10+-blue) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-integrated-41BDF5) ![WebSocket](https://img.shields.io/badge/live%20events-WebSocket-22c55e)

## What you get

| Output | Purpose |
|--------|---------|
| **`network-graph.html`** | Interactive 3D force graph — orbit, zoom, drag nodes, click for capability cards |
| **`network-data.json`** | Graph payload (nodes, edges, metrics, legend) |
| **Obsidian vault** | Device notes, wiki-links, static graph view |
| **`Network Map.md`** | Human-readable scan summary |

Each physical device is **one node**. Connections are **not** duplicated — a phone on Wi‑Fi and in Home Assistant shows **two edges**: router (yellow) and HA Companion (teal).

**Smart plugs** are discovered individually from Home Assistant (`switch.*` / `light.*` outlets) and render as separate nodes (`plug-1` … `plug-4`) with distinct labels — not a single aggregate “Tuya Plugs” orb.

## Architecture

```
Mac (scanner) ── ARP scan ──► Videotron Helix LAN (10.0.0.x)
     │
     ├── Home Assistant REST ──► initial states, Glances, probes
     ├── Home Assistant WebSocket ──► live state_changed stream
     ├── Live broadcast server (:8766) ──► instant UI updates
     └── generate_network_map.py ──► network-data.json + HTML

Browser (any device) ── HTTP :8765 ──► network-graph.html
                     └── WS   :8766 ──► node pulses + link telemetry
```

**Single source of truth for “who is online”:** the Mac’s ARP table (proxy for router-active clients). Optional `router-clients.json` / `router-online.json` enrich Helix exports. Stale ghosts are filtered out; cloud-only IoT (e.g. Tuya plugs without LAN IP) stay visible via HA tether fallbacks.

## Quick start

### Requirements

- **Python 3.10+**
- **`websockets`** package (live HA event stream): `pip3 install websockets`
- **Mac on the same LAN** as your homelab (runs the scanner)
- **Home Assistant** long-lived token (required for phones/tablets, smart plugs, and live events)
- **Obsidian** (optional — for notes and wiki graph)

### One-time setup

```bash
cd ~/HomelabNetwork

pip3 install websockets

# Home Assistant token (pick one)
cp ha-token.local.example ha-token.local   # paste token inside
# or: export HOMELAB_HA_TOKEN="your-token"

# Label your LAN clients (IPs from router DHCP / ARP scan)
cp known-clients.example.json known-clients.json
# edit names for phones, tablets, IoT

# Optional: Helix router registry export
cp router-clients.example.json router-clients.json

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

Or use the launcher:

```bash
./scripts/start-dashboard.sh
```

| URL | Who |
|-----|-----|
| `http://127.0.0.1:8765/network-graph.html` | On the Mac |
| `http://<mac-lan-ip>:8765/network-graph.html` | iPad, iPhone, other Macs on Wi‑Fi |
| `ws://<mac-lan-ip>:8766` | Live HA event stream (auto-reconnect) |

The HTTP server binds to **`0.0.0.0`** by default. Topology rescans every **30 seconds**; **instant** plug/state changes arrive over the WebSocket without waiting for the file poll.

Your device gets a **📍 You are here** pin (matched by LAN IP or hostname on the host).

After upgrading plug discovery, click **Reset layout** once to clear any stale `smart-plugs` pin from localStorage.

### CLI options

```bash
python3 generate_network_map.py --help

  --zbook IP          ZBook / HA host (default: 10.0.0.169)
  --open              Open HTML in browser after generate
  --serve             HTTP server on :8765 + live WebSocket on :8766
  --bind 0.0.0.0      Listen on all interfaces (LAN access)
  --interval 30       Topology rescan interval when serving (seconds)
  --ws-port 8766      Live event WebSocket broadcast port
  --ws-bind 0.0.0.0   Live WebSocket bind address
  --watch N           Regenerate every N seconds without server
```

## 3D visualization

| Feature | Description |
|---------|-------------|
| **Procedural starfield** | Three-tier infinite-depth star layers |
| **ACES filmic tone mapping** | High-contrast cores without color washout |
| **Directional sun + ambient** | `MeshStandardMaterial` volumetric node cores |
| **1.5× cyber-cages** | Emissive wireframe icosahedron halos per node |
| **Thick link conduits** | Structural Wi‑Fi / cloud / docker pathways |
| **Telemetry pulses** | Cubes (wired), spheres (wireless), pyramids (IoT) on links |
| **Live WebSocket** | Instant node flash/ping + link particle boost on HA events |

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
| `generate_network_map.py` | Yes | Scanner, merger, probe, HTTP + WebSocket server |
| `network-graph-template.html` | Yes | 3D UI (Three.js + 3d-force-graph) |
| `scripts/start-dashboard.sh` | Yes | macOS launcher for `--serve` |
| `known-clients.json` | **No** (gitignored) | Your IP/MAC → friendly names |
| `known-clients.example.json` | Yes | Template |
| `router-clients.json` | **No** (gitignored) | Helix connected-devices export |
| `router-clients.example.json` | Yes | Template |
| `ha-token.local` | **No** (gitignored) | HA API token |
| `ha-token.local.example` | Yes | Template |
| `helix-router.json` | Yes | Videotron Helix ESP hostname hints |
| `router-online.json` | **No** (gitignored) | Optional Helix “connected devices” export |
| `router-online.example.json` | Yes | Template |
| `extra-devices.json` | **No** (gitignored) | Manual devices (headphones, etc.) |
| `extra-devices.example.json` | Yes | Template |
| `node-positions.json` | **No** (gitignored) | Saved 3D layout from browser |

### Smart plug discovery

The generator scans all Home Assistant `switch.*` and `light.*` entities matching outlet/plug keywords (`device_class: outlet`, `plug_N`, `socket`, `tuya`, etc.). Each match becomes its own node with:

- Dynamic label from HA (`Plug 1 · Desk`, …)
- Router + HA cloud tether when no LAN IP is available
- Constellation layout fanned around the router gateway (no stacking)

Diagnostics print at scan time and are stored in `network-data.json` as `plug_diagnostics`.

### Labeling unknown LAN clients

Each scan prints unlabeled ARP entries:

```
[i] Unlabeled LAN clients (add to router-clients.json):
    10.0.0.45  aa:bb:cc:dd:ee:ff
```

Add an entry in `known-clients.json` or `router-clients.json`. Re-run the generator — duplicates merge into one canonical node.

### Router-only truth

Devices appear on the map only if they are:

1. In the **current ARP scan** (or router registry), or  
2. **Core infrastructure** (router, ZBook, WSL, HA, nested services), or  
3. **HA device_trackers** / **smart plugs** (HA link even without LAN IP)

Mark stale ghosts with `"stale": true` in client registries to hide them even if ARP still lists them.

## 3D map controls

| Action | Control |
|--------|---------|
| Orbit | Left-drag empty space |
| Zoom | Scroll |
| Pan | Right-drag |
| Pin a node | Drag the node |
| Unpin | Double-click node or right-click node |
| Save layout | **Save layout** button → `node-positions.json` |
| Reset layout | **Reset layout** button |

## Home Assistant integration

With a token set, the generator:

- Adds **`device_tracker.*`** phones/tablets (merged into registry entries)
- Maps canonical IDs (e.g. `marshall-iphone`, `wife-iphone`, `family-ipad`, `w09n-frame`)
- Adds **`ha_mobile`** edges from `homeassistant` → each tracked device
- Discovers **individual smart plugs** as `plug-1` … `plug-N` nodes
- Subscribes to **`state_changed`** over HA WebSocket and broadcasts live JSON to browsers
- Reads switch/media_player/sensor states for plugs, speakers, cameras
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

Obsidian graph ≠ live HTML dashboard. Use `--serve` for real-time path health and WebSocket pulses.

## Project layout

```
HomelabNetwork/
├── generate_network_map.py      # Main generator + HTTP/WebSocket server
├── network-graph-template.html  # 3D dashboard shell
├── network-graph.html           # Generated (committed as demo snapshot)
├── network-data.json            # Generated graph payload
├── scripts/start-dashboard.sh   # macOS dashboard launcher
├── Connection Legend.md         # Medium reference (generated)
├── Network Map.md               # Scan summary (generated)
├── Devices/                     # Per-device Obsidian notes (generated)
├── helix-router.json            # Helix ESP MAC hints
├── known-clients.example.json
├── router-clients.example.json
├── ha-token.local.example
├── router-online.example.json
├── extra-devices.example.json
└── .obsidian/                   # Vault settings
```

## Not the ZBook copy

`C:\Users\serveradmin\NetworkVault` on the Windows ZBook is a separate folder. **This Mac vault (`~/HomelabNetwork`) is the daily-driver source.**

## License

Personal homelab project. Adapt freely for your own network; scrub IPs and tokens before publishing.

## Backup

Timestamped archives (excluding secrets) are stored at:

```
~/HomelabNetwork-backups/homelab-network-YYYY-MM-DD-HHMM.tar.gz
```

Create a fresh backup anytime:

```bash
STAMP=$(date +%Y-%m-%d-%H%M)
tar -czf ~/HomelabNetwork-backups/homelab-network-$STAMP.tar.gz \
  -C ~/HomelabNetwork --exclude='ha-token.local' .
```

## Git & GitHub

The repo is on branch **`main`** at [github.com/marshalls-dev/homelab-network-map](https://github.com/marshalls-dev/homelab-network-map). Secrets and personal LAN files stay gitignored (`known-clients.json`, `router-clients.json`, `ha-token.local`, etc.).

```bash
cd ~/HomelabNetwork
git pull
python3 generate_network_map.py
git add README.md generate_network_map.py network-graph-template.html network-graph.html network-data.json scripts/
git commit -m "Describe your change"
git push origin main
```

Or use the publish helper:

```bash
./scripts/publish.sh
```
