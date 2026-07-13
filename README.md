# Homelab Network Space Map

Live **3D network topology** and **Obsidian vault** for the S-PRATT Home Assistant homelab. One Python scanner on the Dev Mac discovers LAN clients, merges Home Assistant device trackers, pulls **multi-host Glances**, and renders an interactive space map anyone on Wi‑Fi can open in a browser.

**Last updated:** 2026-07-13  
**GitHub:** [marshalls-dev/homelab-network-map](https://github.com/marshalls-dev/homelab-network-map) · branch `main`  
**Control Center zone:** Trailhead **Z3 Network Atlas**

![Homelab Network Space Map](https://img.shields.io/badge/python-3.10+-blue) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Home%20Base%2010.0.0.8-41BDF5) ![WebSocket](https://img.shields.io/badge/live%20events-WebSocket-22c55e)

## What you get

| Output | Purpose |
|--------|---------|
| **`network-graph.html`** | Interactive 3D force graph — orbit, zoom, drag nodes, click for capability cards |
| **`network-data.json`** | Graph payload (nodes, edges, metrics, legend) |
| **Obsidian vault** | Device notes, wiki-links, static graph view |
| **`Network Map.md`** | Human-readable scan summary |

Each physical device is **one node**. Connections are **not** duplicated — a phone on Wi‑Fi and in Home Assistant shows **two edges**: router (yellow) and HA Companion (teal).

**Smart plugs** are discovered individually from Home Assistant (`switch.*` / `light.*` outlets) and render as separate nodes (`plug-1` … `plug-4`) with distinct labels — not a single aggregate “Tuya Plugs” orb.

## Architecture (current production)

```
Dev Mac (scanner) ── ARP scan ──► Videotron Helix LAN (10.0.0.x)
     │
     ├── Home Assistant REST ──► 10.0.0.8:8123  (Home Base Mac)
     ├── Home Assistant WebSocket ──► live state_changed
     ├── Glances ──► old-macbook :61208 (Home Base) + zbook-wifi :61209 (ZBook)
     ├── Live broadcast server (:8766) ──► instant UI updates
     └── generate_network_map.py ──► network-data.json + HTML

Browser (any device) ── HTTP :8765 ──► network-graph.html
                     └── WS   :8766 ──► node pulses + link telemetry
```

| Hub node ID | Host | Role | Glances |
|-------------|------|------|---------|
| `old-macbook` | 10.0.0.8 | **Home Base** — HA, go2rtc, Frigate, n8n, Agent Gateway | `:61208` |
| `zbook-wifi` | 10.0.0.169 | Basement — Jellyfin, Ollama, RTSP, Minecraft/WSL | `:61209` |

Entity naming aligns with Home Assistant’s Network Health package (`homeassistant/monitoring/network-registry.yaml`).

**Single source of truth for “who is online”:** the Mac’s ARP table (proxy for router-active clients). Optional `router-clients.json` / `router-online.json` enrich Helix exports. Stale ghosts are filtered out; cloud-only IoT (e.g. Tuya plugs without LAN IP) stay visible via HA tether fallbacks.

## Quick start

### Requirements

- **Python 3.10+**
- **`websockets`** package: `pip3 install websockets`
- **Mac on the same LAN** as the homelab (runs the scanner)
- **Home Assistant** long-lived token (phones/tablets, smart plugs, live events)
- **Obsidian** (optional — notes and wiki graph)

### Paths

| Location | Purpose |
|----------|---------|
| `~/MARSHALL_CURSOR_PROJECTS/homelab-network-map` | Git checkout (edit + push here) |
| `~/HomelabNetwork` | Optional live vault used by `scripts/start-dashboard.sh` |

If both exist, the launcher syncs newer template/code from the repo into the live vault before serving.

### One-time setup

```bash
cd ~/MARSHALL_CURSOR_PROJECTS/homelab-network-map

pip3 install websockets

# Home Assistant token (Home Base Mac — 10.0.0.8)
cp ha-token.local.example ha-token.local   # paste token inside
# or: export HOMELAB_HA_TOKEN="your-token"

# Label your LAN clients (IPs from router DHCP / ARP scan)
cp known-clients.example.json known-clients.json

# Optional: Helix router registry export
cp router-clients.example.json router-clients.json
```

Create a HA token: **Profile → Security → Long-Lived Access Tokens** on http://10.0.0.8:8123.

### Generate once

```bash
python3 generate_network_map.py
```

### Live dashboard (recommended)

```bash
python3 generate_network_map.py --serve
```

Or use the launcher (prefers `~/HomelabNetwork` when present):

```bash
./scripts/start-dashboard.sh
```

From **Trailhead Control Center** → **Z3 Network Atlas** → Start dashboard / Open graph.

| URL | Who |
|-----|-----|
| `http://127.0.0.1:8765/network-graph.html` | On the Dev Mac |
| `http://<mac-lan-ip>:8765/network-graph.html` | iPad, iPhone, other Macs on Wi‑Fi |
| `ws://<mac-lan-ip>:8766` | Live HA event stream (auto-reconnect) |

Topology rescans every **30 seconds**; **instant** plug/state changes arrive over the WebSocket.

Your device gets a **📍 You are here** pin (matched by LAN IP or hostname on the host).

### CLI options

```bash
python3 generate_network_map.py --help

  --ha-host IP        Home Assistant host (default: 10.0.0.8 Home Base)
  --zbook IP          ZBook LAN IP — Glances :61209, RTSP (default: 10.0.0.169)
  --open              Open HTML in browser after generate
  --serve             HTTP server on :8765 + live WebSocket on :8766
  --bind 0.0.0.0      Listen on all interfaces (LAN access)
  --interval 30       Topology rescan interval when serving
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
| **Multi-host Glances** | CPU/RAM/disk cards for Home Base (`:61208`) and ZBook (`:61209`) |

## Connection legend

| Medium | Color | Meaning |
|--------|-------|---------|
| `wifi` / `wifi_5g` | Orange | Helix / LAN Wi‑Fi |
| `wifi_2g` | Orange dashed | 2.4 GHz (frame, some IoT) |
| `ha_mobile` | Teal | Home Assistant Companion app |
| `http` | Purple | Web UI (HA dashboards, frame panel) |
| `docker_bridge` | Purple dashed | Docker / WSL2 internal |
| `portproxy` | Cyan dashed | Windows portproxy → WSL services |
| `tailscale` | Green dashed | Tailscale overlay |
| `cast` | Yellow | Google Cast control |
| `rtsp` | Red | Camera stream → go2rtc / HA |
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
| `scripts/sync-to-live-vault.sh` | Yes | Sync repo → `~/HomelabNetwork` |
| `scripts/restart-dashboard.sh` | Yes | Bounce the live server |
| `known-clients.json` | **No** (gitignored) | Your IP/MAC → friendly names |
| `known-clients.example.json` | Yes | Template |
| `router-clients.json` | **No** (gitignored) | Helix connected-devices export |
| `ha-token.local` | **No** (gitignored) | HA API token |
| `helix-router.json` | Yes | Videotron Helix ESP hostname hints |
| `extra-devices.json` | **No** (gitignored) | Manual devices |
| `node-positions.json` | **No** (gitignored) | Saved 3D layout from browser |

### Smart plug discovery

The generator scans all Home Assistant `switch.*` and `light.*` entities matching outlet/plug keywords. Each match becomes its own node with dynamic HA labels and constellation layout around the router.

### Labeling unknown LAN clients

Each scan prints unlabeled ARP entries. Add them to `known-clients.json` or `router-clients.json` and re-run.

### Router-only truth

Devices appear on the map only if they are:

1. In the **current ARP scan** (or router registry), or  
2. **Core infrastructure** (router, ZBook, WSL, Home Base, nested services), or  
3. **HA device_trackers** / **smart plugs** (HA link even without LAN IP)

Mark stale ghosts with `"stale": true` in client registries to hide them.

## Nested services (`runs_on`)

Services that run inside other hosts appear as smaller nested nodes:

| Service | Parent |
|---------|--------|
| Home Assistant, go2rtc / Frigate stack | **Home Base** (`old-macbook`) |
| Minecraft, Phantom, Jellyfin | **ZBook / WSL** (`zbook-wifi` / `wsl-ubuntu`) |
| Basement RTSP camera publish | **ZBook** |

## Home Assistant integration

With a token set, the generator:

- Talks to **Home Base** at `10.0.0.8:8123` (not the old ZBook HA URL)
- Adds **`device_tracker.*`** phones/tablets
- Adds **`ha_mobile`** edges from `homeassistant` → each tracked device
- Discovers **individual smart plugs** as `plug-1` … `plug-N`
- Subscribes to **`state_changed`** over HA WebSocket and broadcasts live JSON to browsers
- Fetches Glances for both hubs when ports are open

## Obsidian

1. Install [Obsidian](https://obsidian.md)
2. **Open folder as vault** → this directory (or `~/HomelabNetwork`)
3. Read **[[Connection Legend]]** and **[[Network Map]]**
4. Use **Graph view** for wiki-link topology (static; no live latency)

Obsidian graph ≠ live HTML dashboard. Use `--serve` for real-time path health and WebSocket pulses.

## Project layout

```
homelab-network-map/
├── generate_network_map.py      # Main generator + HTTP/WebSocket server
├── network-graph-template.html  # 3D dashboard shell
├── network-graph.html           # Generated (committed as demo snapshot)
├── network-data.json            # Generated graph payload
├── scripts/
│   ├── start-dashboard.sh
│   ├── restart-dashboard.sh
│   └── sync-to-live-vault.sh
├── Connection Legend.md
├── Network Map.md
├── Devices/                     # Per-device Obsidian notes (generated)
├── helix-router.json
├── *.example.json
└── .obsidian/
```

## License

Personal homelab project. Adapt freely for your own network; scrub IPs and tokens before publishing.

## Git & GitHub

```bash
cd ~/MARSHALL_CURSOR_PROJECTS/homelab-network-map
git pull
python3 generate_network_map.py
git add README.md generate_network_map.py network-graph-template.html \
  network-graph.html network-data.json scripts/ helix-router.json \
  known-clients.example.json "Connection Legend.md" "Network Map.md" Devices/
git commit -m "Describe your change"
git push origin main
```

Or use `./scripts/publish.sh` when present.

Secrets stay gitignored (`known-clients.json`, `router-clients.json`, `ha-token.local`, etc.).
