# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ha-kodu24` is the Home Assistant config repo for the house (renamed from `ha-climate` 2026-08-15 — it outgrew climate). Everything here deploys as HA packages copied into `config/` and `!include`d under `homeassistant: packages:`, or as pyscript modules. Alongside the climate work below it holds `battery-monitor/` (battery levels and safety-device alerts) and `backup-monitor/` (push alerts for the off-site backups defined in the `unraid` repo). New general HA housekeeping belongs here rather than in a new repo.

The climate half is a PyScript helper for Danfoss eTRV0103 Zigbee thermostatic radiator valves (TRVs). It publishes per-room weighted virtual temperature/humidity sensors from external sensors. Heating control itself is handled by **Better Thermostat** (see `BETTER_THERMOSTAT.md`), which consumes these sensors; this script no longer writes to the TRVs.

## Setup & Deployment

**Deploy with `./deploy.sh`** (added 2026-09-05). It rsyncs every package in
its manifest into HA's `/config` and runs `ha core check`; `--restart` also
restarts HA, `-n` is a dry run.

Prerequisites, one-time:

1. An SSH add-on installed and started, with this workstation's public key in
   its `authorized_keys` option. Ours listens on **port 22** (the script's
   default) and has `rsync`, `tar` and the `ha` CLI available. Note a newly
   added key needs the add-on *restarted*, not just the config saved.
   (This is HA OS/Supervised — the Observer on :4357 confirms it — so add-ons
   are available.)
2. Nothing to change in the Tailscale policy: `tag:workstation → tag:home` is
   not port-restricted (both :8123 and :4357 answer over the tailnet).

Two things about the transport that are not obvious:

- **It must go over the tailnet.** HA sits on a segment the workstation cannot
  reach directly — HA's LAN address does not even ping from the wifi, though
  the Unraid host and the VM reach it fine. Hence `HA_HOST` defaults to the
  tailnet name.
- **Nabu Casa remote UI cannot carry ssh.** It proxies the frontend only, so
  it is not an alternative transport for deploys.

The script uses ssh `ControlMaster` — not for speed, but because the key lives
in the 1Password agent, which prompts per signature. Without one shared
connection each manifest entry would raise its own prompt and the later ones
would time out.

`--delete` is applied **per manifest entry**, not globally: package dirs this
repo owns are mirrored, but `themes/` and `pyscript/` are not, because HACS
also writes into `config/themes/` and mirroring would delete themes this repo
never knew about. `dashboard/` directories are excluded entirely — they are
records of storage-mode dashboards and paste-in card templates, not files HA
loads.

`configuration.yaml` is tracked here as of 2026-09-05 and is deployed like
everything else, so **edit it in the repo, not in `/config`** — the next deploy
overwrites the live copy. It matters more than the package files: its
`packages:` block is what decides which packages HA actually loads, and while
it was unversioned `battery-monitor` sat in the repo, documented as live,
without ever being declared — so it never loaded and never alerted. Adding a
package directory does nothing until it is listed there.

### Dashboards (storage mode)

Both dashboards — `lovelace` (Ülevaade) and `home-server` (Server) — are
**storage mode**: HA owns the live copy as JSON in `/config/.storage/`, which
is why the YAML under `*/dashboard/` is a hand-maintained *record* rather than
the thing HA loads. The record can therefore drift; check before assuming.

They can still be edited from the shell. Three routes, in the order worth
reaching for:

1. **Patch `/config/.storage/lovelace.<id>` and restart** — what was used on
   2026-09-05 to add the pool strip. Load the JSON, insert precisely, write it
   back, `ha core restart`. Prefer a *surgical* insert over regenerating the
   file from the YAML record: a wholesale overwrite silently applies any drift
   the record has accumulated. Back the file up first, keep the wrapper
   (`version`, `minor_version`, `key`) intact, and re-render the YAML record to
   match so the two do not diverge.
   **The restart is required** — HA holds the config in memory and would
   otherwise rewrite your edit on the next UI change.
2. **Websocket API `lovelace/config/save`** — the supported route, applies live
   with no restart, but needs a long-lived access token.
3. **Convert the dashboard to YAML mode** (declare it under `lovelace:` in
   `configuration.yaml`). This makes it a plain file that `deploy.sh` can own,
   and removes the record/live duplication entirely — at the cost of losing UI
   editing for that dashboard. Not done; worth considering if the record keeps
   drifting.

Card *definitions* also exist as paste-in templates under `*/dashboard/`, for
adding by hand in the UI editor.

### Verifying a deploy

`ha core check` only validates syntax. To confirm entities actually exist and
carry values, query the recorder DB over ssh (`sqlite3` is present):

```sh
sqlite3 /config/home-assistant_v2.db "SELECT sm.entity_id, s.state
  FROM states s JOIN states_meta sm ON s.metadata_id=sm.metadata_id
  WHERE sm.entity_id LIKE '%backup_pool%'
  GROUP BY sm.entity_id HAVING MAX(s.last_updated_ts);"
```

New `input_*` helpers only appear after a restart (or Developer Tools → YAML →
Reload all), so a package can deploy cleanly and still show nothing until then.

### Transport gotchas

- **No sftp subsystem** on the add-on: `scp` fails with "subsystem request
  failed". `rsync` works (it tunnels over the ssh channel), as does
  `ssh host 'cat file'` for pulling one file.
- A newly added `authorized_keys` entry needs the **add-on restarted**, not
  just the config saved.

This is not a standalone Python project - it runs within Home Assistant's PyScript integration.

**Installation:**
1. Copy `danfoss.py` to `config/pyscript/`
2. Copy `trv-climate/climate.yaml` to `config/trv-climate/`
3. Include in `configuration.yaml`:
   ```yaml
   homeassistant:
     packages:
       climate_sensors: !include trv-climate/climate.yaml
   ```
4. Restart Home Assistant

No build step required. Dependencies in `requirements.txt` are Home Assistant's own packages.

## Architecture

**danfoss.py** - Main PyScript module containing:

danfoss.py is now **sensor-aggregation only** — it performs **no writes to the
TRVs** and does not control heating. Heating control (setpoint, on/off,
calibration) is owned entirely by **Better Thermostat** (see `BETTER_THERMOSTAT.md`).

- **Weighted Calculation**: `calculate_weighted_climate()` computes a per-area
  weighted average from external sensors labelled `sensor_weight_X` (TRV
  temperatures are excluded so heating doesn't skew it).
- **`update_room_climate_sensors()`** (PyScript, at startup + every 5 min):
  publishes `sensor.climate_{area_id}_temperature` / `_humidity`. These are the
  single per-room sensors Better Thermostat consumes (BT does not do weighted
  averaging itself).

That's the whole module. The previous Zigbee control logic — time sync,
radiator-covered, load-balancing, external-sensor feed/disable, and the
retry queue — was removed so the script can never interfere with BT. (See git
history and `DANFOSS.md` if that logic is ever needed again.)

**trv-climate/climate.yaml** - Template sensor definitions wrapping pyscript-created sensors for proper HA UI management.

## Why control moved to Better Thermostat

The Danfoss eTRV's native external-sensor feature holds an anticipatory ~1% valve
opening and never fully closes when fed an external sensor (confirmed across all
externally-fed TRVs; only an unfed one idles — see `DANFOSS.md` §2.6, and note
"off" is only 5°C anti-freeze, not a real off). Control was therefore handed to
Better Thermostat, which drives the setpoint with the native external sensor
disabled. `DANFOSS.md` is the curated eTRV Zigbee/feature reference.

## Device Labels

Configure in Home Assistant UI on devices:
- `sensor_weight_X` - External sensors with weight X for the room average

## Adding New Areas

Areas are auto-detected from HA device assignments. Add corresponding template sensors to `trv-climate/climate.yaml` following existing pattern.
