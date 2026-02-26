# Generic Router Monitor (Home Assistant)  
![hassfest](https://github.com/REPLACE_WITH_GH_OWNER/generic-router-monitor/actions/workflows/hassfest.yml/badge.svg)
![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)
![License](https://img.shields.io/github/license/REPLACE_WITH_GH_OWNER/generic-router-monitor)

A production-safe Home Assistant custom integration that monitors **routers via SSH** (plus ping).  
Built for Linux-based router firmware like **DD-WRT** and **OpenWRT**, and supports **mixed “modern” and “legacy” SSH crypto** on a per-router basis.

## Features

- ✅ Online/Offline (ping)
- ✅ Uptime
- ✅ CPU Load (1 minute)
- ✅ Memory Used (%)
- ✅ Auto-detect WAN interface (best-guess based on traffic deltas)
- ✅ WAN RX/TX throughput (Mbps)
- ✅ Per-router SSH mode:
  - **modern** (default, recommended)
  - **legacy** (for older DD-WRT builds that require group1/ssh-rsa)
- ✅ Diagnostics export with **password redaction**

## Screenshots

Add screenshots to `docs/screenshots/` and link them here.

Example:
- `docs/screenshots/device.png`
- `docs/screenshots/entities.png`

## Requirements

- Home Assistant Core (modern versions)
- Routers must provide SSH shell access and common Linux utilities:
  - `/proc/uptime`
  - `/proc/loadavg`
  - `free`
  - `/proc/net/dev`
- ICMP ping to the router must be permitted from Home Assistant

## Installation

### Option A: HACS (recommended)

1. Install HACS
2. In HACS → Integrations → “⋮” → Custom repositories
3. Add this repository URL, category **Integration**
4. Install **Generic Router Monitor**
5. Restart Home Assistant
6. Add the integration: Settings → Devices & Services → Add Integration → **Generic Router Monitor**

### Option B: Manual

1. Copy `custom_components/generic_router` into:
   ```
   /config/custom_components/generic_router
   ```
2. Restart Home Assistant
3. Add the integration

## Configuration

When adding the integration you will be prompted for:

- **Host/IP**
- **SSH Port** (default 22)
- **SSH Username**
- **SSH Password**
- **SSH Mode**
  - `modern` (default)
  - `legacy` (older DD-WRT crypto)

### WAN RX/TX Notes

WAN RX/TX requires two samples to compute throughput, so RX/TX may show `unknown` for the first 30–60 seconds.

## Entities

### Binary Sensor
- `Online`

### Sensors
- `Uptime` (seconds)
- `CPU Load (1m)`
- `Memory Used` (%)
- `WAN Interface`
- `WAN RX` (Mbps)
- `WAN TX` (Mbps)

## Troubleshooting

### “SSH error: Permission denied”
- Confirm you can SSH from another machine using the same host/port/user/pass.
- Many DD-WRT builds use `root` as the SSH user even if the web UI shows `admin`.

### “Connection refused”
- SSH is not enabled or not listening on the configured port.
- Confirm SSH is listening:
  - DD-WRT: `ps | grep dropbear`
  - `netstat -an | grep :22`

### Legacy router requires old crypto
- Set **SSH Mode** to `legacy` for that router.
- This enables older key exchange and host key algorithms required by some older DD-WRT builds.

### Deprecation warnings from cryptography/asyncssh
You may see warnings about deprecated ciphers (ARC4/TripleDES) from upstream dependencies.  
These are warnings from **asyncssh/cryptography**, not this integration, and do not affect operation.

## Security Notes

- Use LAN-only SSH whenever possible.
- Avoid exposing SSH to the internet.
- Use strong passwords or keys where supported.
- Diagnostics data redacts stored passwords.

## Development

- Run `hassfest` and `hacs` validation via GitHub Actions
- See `.github/workflows/`

## Release Process

1. Update version in `custom_components/generic_router/manifest.json`
2. Tag and create a release:
   - `git tag vX.Y.Z`
   - `git push --tags`
3. Create a GitHub Release named `vX.Y.Z` with notes
4. (Optional) Attach a zip asset of the repo

## License

MIT — see [LICENSE](LICENSE).
