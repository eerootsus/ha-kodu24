# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ha-kodu24` is the Home Assistant config repo for the house (renamed from `ha-climate` 2026-08-15 — it outgrew climate). Everything here deploys as HA packages copied into `config/` and `!include`d under `homeassistant: packages:`, or as pyscript modules. Alongside the climate work below it holds `battery-monitor/` (battery levels and safety-device alerts), `backup-monitor/` (push alerts for the off-site backups defined in the `unraid` repo), `workshop-heating/` (on/off heating of the workshop via its split-unit HVAC, moved out of the UI 2026-10-17), and `heating-pressure/` (top-up and leak alerts for the heating system pressure, 2026-10-25). New general HA housekeeping belongs here rather than in a new repo.

**This repo is the source of truth for the Kodu 24 smart home.** Open work and plans live in `PLANS.md`; the Obsidian vault's `Projects/Smart home.md` only holds TODO-feeding next-action lines that point here. Record new findings and plans in the repo, not the vault, and move a `PLANS.md` item's outcome into the relevant doc once it is built.

The climate half is a PyScript helper for Danfoss eTRV0103 Zigbee thermostatic radiator valves (TRVs). It publishes per-room virtual temperature/humidity sensors from external room sensors (since 2026-10-17 the door sensor; the outer-wall Alts are weight 0). It does **not** control heating: each eTRV regulates on its own internal sensor, corrected by a per-room trim set by hand (`BETTER_THERMOSTAT.md` "Trims in force"; Better Thermostat was trialled and dropped as an obscuring layer). Automation here advises — `trv-climate/heating_alerts.yaml` names the knob, a human turns it.

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
   with no restart, but needs a long-lived access token. **`./dashboard.py`**
   wraps it per view: `check` (diff live vs record), `apply` (record → live, asks
   first, verifies), `pull` (live → record after UI edits). Views it knows are in
   its `VIEWS` map; add one there to manage another. Used for the Küte view
   (`trv-climate/dashboard/heating_view.yaml`).
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

## Heating check

`./heating-check.py` compares how each room holds its setpoint over a window
(default: last 7 days) against the fixed pre-trim baseline week, with weather and
gas-per-degree-day for context. Same ssh transport; see `BETTER_THERMOSTAT.md`
"Trims in force".

## Zigbee mesh topology

`./zigbee-topology.sh` prints who parents whom and at what **first-hop LQI**,
read from ZHA's neighbour table in `/config/zigbee.db` over the same ssh
transport as `deploy.sh` (no HA token needed). `--save` stores a snapshot under
`topology/` (tracked, so before/after evidence outlives one workstation),
`--diff` compares the two most recent.

**Do not use `sensor.*_lqi` to judge a device's link.** LQI is a MAC-layer
measurement taken by the receiving radio, so the coordinator's number describes
only the *last hop into the coordinator*. For anything behind a router that is
a different radio link: on 2026-09-13 the Ada TRV's sensor read a comfortable
178 while its actual hop to its parent was 45, and Lola's sensor *fell* from
~155 to ~118 when she re-parented onto the new ZBMINIR2 — her own link had in
fact improved to 217. Only the neighbour table carries the real number, and
nothing historises it, which is why this script exists.

Two facts that govern any mesh work here:

- **End devices never migrate on their own.** A sleepy device keeps its parent
  until polling fails; there is no periodic "is there a better parent?" check.
  Adding a router changes nothing for already-joined devices. To move one,
  power-cycle its *current* parent — the eTRVs poll every 7 s
  (`long_poll_interval` = 28 quarter-seconds, which is also the firmware floor),
  so they orphan and rejoin within roughly a minute. This is also why a core
  update re-parents things: the coordinator restarts and its direct children
  scatter onto routers.
- **The neighbour table only refreshes on a topology scan**, so a snapshot taken
  right after a re-parent can still show the old parent. A device listed as a
  child by two routers at once (the script's "RECENTLY MOVED" section) is one
  that moved and whose old parent has not been rescanned.
- **ZHA's `unsupported_attributes_v12` cache lies after a bad interview.** A device
  interviewed over a weak link gets attributes recorded as unsupported that the
  same firmware supports elsewhere, and the entity behind them is never created.
  zigpy then refuses to read or write those attributes at all, so it can only be
  cleared in `zigbee.db`. Diffing the table across identical devices is how you
  spot it. Clearing it is necessary but **not sufficient**: ZHA only creates these
  config entities at device *interview*, so the device also needs a Reconfigure
  (Settings → Devices & Services → ZHA → device → Reconfigure). Cache first, then
  reconfigure — the other order re-reads the attribute, finds it still cached as
  unsupported, and skips it. Done for the TRVs on 2026-09-13; see
  `BETTER_THERMOSTAT.md`.
- **New ZHA entities are slugged in HA's instance language** (`language: et` here), so
  a reconfigure creates `number.<area>_<device>_kohalik_temperatuuri_nihe` next to
  older English-slugged siblings. Display names are unaffected — `friendly_name` is
  translated at runtime, so every device already shows Estonian — but mismatched ids
  break templating across devices. Rename them back over the websocket API
  (`config/entity_registry/update`; no REST equivalent), and expect to redo it after
  the next reconfigure.

This is not a standalone Python project - it runs within Home Assistant's PyScript integration.

**Installation:** none of it is manual any more. `danfoss.py` and `trv-climate/` are
both in `deploy.sh`'s manifest and `climate_sensors:` is declared in the tracked
`configuration.yaml`, so `./deploy.sh` is the whole procedure. A changed module is
picked up by `pyscript.reload`; the template sensors need `template.reload`.

No build step required. Dependencies in `requirements.txt` are Home Assistant's own packages.

## Architecture

> **Fixed 2026-09-13, worth knowing about.** `get_all_climate_devices()` iterated
> `dr.devices` expecting device *ids*, but HA now returns a
> `_DeprecatedDeviceRegistryItemsView` that yields `DeviceEntry` objects, so
> `dr.async_get(device_id)` raised `TypeError: cannot use 'DeviceEntry' as a dict
> key` on every run. No `sensor.climate_*` was published and all ten `trv-climate`
> template sensors sat `unavailable` — for an unknown length of time, because
> **the failure is invisible from the UI**: an absent sensor and an `unavailable`
> one look identical from a template, and this install writes no
> `home-assistant.log`, so the traceback only ever appeared in `ha core logs`.
> If climate goes quiet again, read `ha core logs | grep danfoss` first.

**danfoss.py** - Main PyScript module containing:

danfoss.py is **sensor-aggregation only** — it performs **no writes to the TRVs**
and does not control heating. It was trimmed that way to make room for Better
Thermostat; **BT was then trialled and removed** (2026-09-13, it offered nothing
meaningful — see `BETTER_THERMOSTAT.md`), so nothing applies room-based control
now. Each eTRV regulates on its own internal sensor with the external feed still
disabled, and these sensors are observability plus the heating-curve test's input.

- **Weighted Calculation**: `calculate_weighted_climate()` computes a per-area
  weighted average from external sensors labelled `sensor_weight_X` (TRV
  temperatures are excluded so heating doesn't skew it).
- **`update_room_climate_sensors()`** (PyScript, at startup + every 5 min):
  publishes `sensor.climate_{area_id}_temperature` / `_humidity`. These are the
  single per-room sensors. Nothing consumes them for control since BT was dropped;
  they feed the dashboard and `HEATING_CURVE_TEST.md`.

That's the whole module. The previous Zigbee control logic — time sync,
radiator-covered, load-balancing, external-sensor feed/disable, and the
retry queue — was removed so the script can never interfere with BT. (See git
history and `DANFOSS.md` if that logic is ever needed again.)

**trv-climate/climate.yaml** - Template sensor definitions wrapping pyscript-created sensors for proper HA UI management.

**trv-climate/heating_alerts.yaml** - Push alert when a TRV room stays under its own target, with the likely cause (curve / trim / valve). Alert only.

**trv-climate/balancing_test.yaml** - `script.balancing_test`: the repeatable before/after measurement for radiator balancing (all valves shut, then all fully open, each TRV's reading sampled every 5 min, targets restored; a watchdog restores them if it is interrupted). Results in `sensor.balancing_test_result` (this run + the previous one). The one place that writes TRV setpoints, and only while it runs.

**trv-climate/clock_sync.yaml** - Writes the time to any eTRV reporting `Invalid_clock_information` (on the flag, and nightly at 03:30), pushes only if that does not clear it. The stairwell went 2026-10-01..25 without a clock unnoticed after `set_time()` was dropped. Clock only, never a heating setting.

**trv-climate/room_feed.yaml** - **Parked, not loaded** (2026-10-19). Fed Lola's room
temperature to her TRV (Danfoss automatic offset mode) for two nights; the valve
barely responded, so she is back on a fixed trim. Kept as the record and for reuse
(covered mode would need a 10-min cadence). Every TRV now runs on its own sensor + trim.

## Why nothing controls the TRVs right now

The Danfoss eTRV's native external-sensor feature holds an anticipatory ~1% valve
opening and never fully closes when fed an external sensor (confirmed across all
externally-fed TRVs; only an unfed one idles — see `DANFOSS.md` §2.6, and note
"off" is only 5°C anti-freeze, not a real off). Control was therefore handed to
Better Thermostat — which was then **trialled and removed** as not worth it.

What that leaves, and it matters with heating season coming: the external feed is
still disabled on the four eTRVs (`0x4015 = -8000`; Ada has a Sonoff TRVZB since
2026-10-26, see `PLANS.md` §7), so each one regulates on its
**internal** sensor, which sits on the radiator and reads warm. That is corrected
with a static per-room trim (`regulation_setpoint_offset`, set 2026-10-17 —
values and rationale in `BETTER_THERMOSTAT.md` "Trims in force").
`DANFOSS.md` is the curated eTRV Zigbee/feature reference.

## Device Labels

Configure in Home Assistant UI on devices:
- `sensor_weight_X` - External sensors with weight X for the room average.
  **`sensor_weight_0` = shown, not counted.** Since 2026-10-17 the room reference is
  the sensor at the door; the "Alt" sensors sit on the outer wall (the coldest
  spot, on purpose) and carry weight 0, so they still appear in the dashboard's
  Diagnostika table but do not drag the room value down. The table puts any
  sensor whose name contains "Alt" in its Alt column. The kitchen and the
  stairwell got door sensors on 2026-10-25 (SNZB-02P, weight 2; the kitchen Alt
  went to weight 0), so every TRV room now has a room reference. Lola's two may have been
  swapped at the 2026-09-12 battery change - unverified (hold one, watch which
  column jumps).

## Adding New Areas

Areas are auto-detected from HA device assignments. Add corresponding template sensors to `trv-climate/climate.yaml` following existing pattern.
