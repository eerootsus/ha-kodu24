# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ha-kodu24` is the Home Assistant config repo for the house (renamed from `ha-climate` 2026-08-15 — it outgrew climate). Everything here deploys as HA packages copied into `config/` and `!include`d under `homeassistant: packages:`, or as pyscript modules. Alongside the climate work below it holds `battery-monitor/` (battery levels and safety-device alerts), `backup-monitor/` (push alerts for the off-site backups defined in the `unraid` repo, and since 2026-11-05 for HA's own backups: Yellow + Nabu Casa + Hetzner sub-account `u647127-sub3`, checked by `backup-monitor/ha_backup_copies.py`), `workshop-heating/` (on/off heating of the workshop via its split-unit HVAC, moved out of the UI 2026-10-17), and `heating-pressure/` (top-up and leak alerts for the heating system pressure, 2026-10-25). New general HA housekeeping belongs here rather than in a new repo.

**This repo is the source of truth for the Kodu 24 smart home.** Open work and plans live in `PLANS.md`; the Obsidian vault's `Projects/Smart home.md` only holds TODO-feeding next-action lines that point here. Record new findings and plans in the repo, not the vault, and move a `PLANS.md` item's outcome into the relevant doc once it is built.

The climate half is a PyScript helper for the Zigbee thermostatic radiator valves (TRVs): four Danfoss eTRV0103s and, on Ada's radiator since 2026-10-26, a Sonoff TRVZB (Lola's is next, `PLANS.md` §3). It publishes per-room virtual temperature/humidity sensors from external room sensors (since 2026-10-17 the door sensor; the outer-wall Alts are weight 0). Since 2026-11-10 **HA is the room thermostat** (`trv-climate/room_thermostat.yaml`): it opens or shuts each TRV from its room's door sensor, and the TRVs are plain valves (see "Control principle" below). Before that each TRV regulated on its own internal sensor plus a hand-set trim (`TRV_REGULATION.md` "Trims in force"), which is still the fallback when a room sensor goes silent or the thermostat is switched off. Better Thermostat was trialled and dropped as an obscuring layer. The boiler curve is set from HA by hand (`HEATING_CURVE_TEST.md` "Curve in force").

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
- **Two keys are authorized** (add-on `a0d7b954_ssh`): `iBook G7` (ED25519, this
  workstation's own 1Password) and, since 2026-11-05, `oroma-lent` (ECDSA, the
  agent lent by `ssh -A` from the device being sat at, see `~/.ssh/config`). Without
  the second, a session driven remotely got "Permission denied (publickey)":
  the iBook key's 1Password prompt appears on a screen nobody is at. The add-on's
  options can be read and changed without ssh over the websocket API
  (`supervisor/api`, `/addons/a0d7b954_ssh/info` and `/options`, then `/restart`).

## Heating check

`./heating-check.py` compares how each room holds its setpoint over a window
(default: last 7 days) against the fixed pre-trim baseline week, with weather and
gas-per-degree-day for context. Same ssh transport; see `TRV_REGULATION.md`
"Trims in force".

`./heating-check.py --duty --from "YYYY-MM-DD HH:MM" [--step 3]` (2026-11-11) is for the
room-thermostat era, when every room sits at target: per time step, the share of time
HA had each valve open, room mean, outside, flow and the wind onto each wall. Rising
duty with wind at a steady temperature is the wind's cost per room.

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
  `TRV_REGULATION.md`.
- **New ZHA entities are slugged in HA's instance language** (`language: et` here), so
  a reconfigure creates `number.<area>_<device>_kohalik_temperatuuri_nihe` next to
  older English-slugged siblings. Display names are unaffected — `friendly_name` is
  translated at runtime, so every device already shows Estonian — but mismatched ids
  break templating across devices. Rename them back over the websocket API
  (`config/entity_registry/update`; no REST equivalent), and expect to redo it after
  the next reconfigure.

This is not a standalone Python project - it runs within Home Assistant's PyScript integration.

**Installation:** none of it is manual any more. `room_climate.py` and `trv-climate/` are
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
> If climate goes quiet again, read `ha core logs | grep room_climate` first.
>
> **Same class of failure, 2026-10-26 → 11-05:** the module only published areas
> holding an `eTRV0103`, so when Ada's TRV became a Sonoff TRVZB her room sensor
> froze at its last value - stale, not absent, so even the no-data alert stayed
> quiet. `TRV_MODELS` now lists both; add any new TRV model there.

**room_climate.py** (named `danfoss.py` until 2026-11-05) - Main PyScript module containing:

room_climate.py is **sensor-aggregation only** — it performs **no writes to the TRVs**
and does not control heating. It was trimmed that way to make room for Better
Thermostat; **BT was then trialled and removed** (2026-09-13, it offered nothing
meaningful — see `TRV_REGULATION.md`). Its sensors are the **input of the room
thermostat** (`room_thermostat.yaml`, since 2026-11-10), plus the dashboard and the
heating-curve test. The TRVs' own external feed stays disabled (eTRVs) / off (TRVZB).

- **Weighted Calculation**: `calculate_weighted_climate()` computes a per-area
  weighted average from external sensors labelled `sensor_weight_X` (TRV
  temperatures are excluded so heating doesn't skew it).
- **`update_room_climate_sensors()`** (PyScript, at startup + every 5 min):
  publishes `sensor.climate_{area_id}_temperature` / `_humidity`. These are the
  single per-room sensors. Since 2026-11-10 the room thermostat controls on them;
  they feed the dashboard and `HEATING_CURVE_TEST.md`.

That's the whole module. The previous Zigbee control logic — time sync,
radiator-covered, load-balancing, external-sensor feed/disable, and the
retry queue — was removed so the script can never interfere with BT. (See git
history and `DANFOSS.md` if that logic is ever needed again.)

**trv-climate/climate.yaml** - Template sensor definitions wrapping pyscript-created sensors for proper HA UI management.

**trv-climate/offset.yaml** - Per-room TRV sensor error (TRV reading − room), raw and `_settled`; the settled value is what a trim should match. Ada's TRVZB reports its reading with its offset already applied, so hers adds it back. The stairwell's (added 2026-11-05) reads negative: its head sits in a draught.

**trv-climate/heating_alerts.yaml** - Push alert when a TRV room stays under its own target, with the likely cause (curve / trim / valve). Alert only.

**trv-climate/condensation.yaml** - Mould/condensation risk at the outer walls (2026-11-05), from each room's Alt sensor and its door reference: `wall_rh_<room>` (worse of the Alt's own RH and the room's vapour at the wall temperature; a stuck Alt RH is ignored), `wall_dew_margin_<room>`, and a 72 h mean. Pushes at a 72 h mean >= 75 % or a dew margin < 2 K for an hour; thresholds and this year's history are in its header. Advise only. The risk season here is summer into October, not winter.

**trv-climate/balancing_test.yaml** - `script.balancing_test`: the repeatable before/after measurement for radiator balancing (all valves shut, then all fully open, each TRV's reading sampled every 5 min, targets restored; a watchdog restores them if it is interrupted). Results in `sensor.balancing_test_result` (this run + the previous one). The one place that writes TRV setpoints, and only while it runs.

**trv-climate/clock_sync.yaml** - Writes the time to any eTRV reporting `Invalid_clock_information` (on the flag, and nightly at 03:30), pushes only if that does not clear it. The stairwell went 2026-10-01..25 without a clock unnoticed after `set_time()` was dropped. Clock only, never a heating setting.

**trv-climate/trim_adjust.yaml** (2026-11-10) - The trims as helpers, `input_number.trv_trim_<room>`, in "+ heats more" units for every room (Ada's TRVZB offset is minus hers): **set a trim there, never on the device** - `trv_trim_apply` writes it, reads it back and retries. `trv_trim_adjust` (off unless `input_boolean.trv_trim_adjust`) steps a room's trim ±0.5 when its 2-h mean is > 0.3 K off its own target, at most once per 2 h, but never raises a room whose valve is already flat out (that is the boiler's). Every step is pushed. The first piece of the "logic lives in HA" principle below.

**trv-climate/room_thermostat.yaml** (2026-11-10, **on**) - HA is the thermostat: every 5 min each TRV's setpoint goes to **28 (open)** when its room (door sensor) is under `input_number.room_target_<room>` − 0.2, to **5 (shut)** at or above target (was target + 0.1 until 2026-11-11), unchanged in between. The TRV's head, trim and firmware logic no longer decide anything. A room whose sensor is silent for 20 min falls back to its TRV (setpoint = target), with a push. **Room targets are the helpers now - a TRV's dial is overwritten within 5 min.** Switching `input_boolean.room_thermostat` off writes every TRV back to its room target. While on, the trim adjuster stands down and the heating alerts judge against the room targets; switch it off before the balancing test.

**trv-climate/trim_check.yaml** - Reads every TRV trim back from the device (`homeassistant.update_entity` is a fresh ZHA read) at 03:45 and on remount signals, pushes if one differs from its `input_number.trv_trim_<room>` helper. Never writes. A failed read keeps the cached value, so it can miss a reset, never invent one.

**curve-test/heating_curve_test.yaml** - Deployed but **off** (2026-11-05). Once `script.curve_test_start` runs it holds the boiler curve, raises it on a 90-min room shortfall against each room's own TRV target (shift in mild weather, slope in real cold, capped), and records how cold each curve survived. The one automation here that writes a heating setting; bounded, logged, one switch. Start after Lola's TRVZB and settled trims. `HEATING_CURVE_TEST.md`.

**trv-climate/room_feed.yaml** - **Parked, not loaded** (2026-10-19). Fed Lola's room
temperature to her TRV (Danfoss automatic offset mode) for two nights; the valve
barely responded, so she is back on a fixed trim. Kept as the record and for reuse
(covered mode would need a 10-min cadence). Every TRV now runs on its own sensor + trim.

## Control principle: the logic lives in HA, devices are plain

Eero, 2026-11-10: when every device is "smart", logic competes and the tuning never
ends, because nobody can tell which layer is at fault. So all the logic lives in
**one place we control - HA, in this repo** - and the devices are plain:

- **A TRV is just a valve that holds the temperature it is given**, against the room
  value HA feeds it. Its own "smart" features stay off: eTRV window detection and load
  balancing, TRVZB adaptive mode and open-window (all off as of 2026-11-10). The
  eTRVs' anticipatory control loop cannot be switched off - the reason for replacing
  them with TRVZBs (`PLANS.md` §3 "Direction").
- **The boiler is plain too**: it follows its curve, and HA sets the curve
  (`number.vitodens_100_heating_curve_shift` / `_slope`).
- **HA's job is that whatever a room is set to is what the room gets** - including
  on windy days, by adjusting the TRV feed/trims and the curve. Each piece of logic is
  in this repo, slow, bounded, logged, pushes on every change, and has one switch.
- **Order of knobs (Eero, 2026-11-10): TRV trims first, the boiler only when a trim
  cannot help.** A room short with its valve throttled is a trim (or, on a TRVZB, its
  feed/offset) matter. Only a room short with its valve fully open (≥ 80 %, TRVZB
  calling) means the boiler is not delivering: then the shift, and the slope only for
  shortfalls that grow with cold. Curve changes are logged in `HEATING_CURVE_TEST.md`
  "Curve in force".
- **The kitchen may fall short in high wind (Eero, 2026-11-11).** It is the SW corner,
  two outer walls onto open gardens, on one radiator. Do not raise the curve so far for
  it that the other rooms become hard to control (overshoot, valves cycling); a kitchen
  under target on a stormy day is accepted.
- **One decision per quantity, in one file.** Two automations must never adjust the
  same thing; split the work by condition (e.g. rooms with throttled valves → room
  level; rooms with a fully open valve → the curve), so they cannot fight.
- Which sensor feeds a TRVZB (door → corrected Alt → its own, `PLANS.md` §3) must be
  visible on the dashboard, like every other decision HA takes.

**Built 2026-11-10:** `trv-climate/room_thermostat.yaml` - HA opens/shuts each
valve from its room's door sensor; the TRV's own reading no longer matters (Eero:
"the TRV temperature can be whatever, if controlling in HA solves the flakiness").
The trims (`trim_adjust.yaml`) only matter again if it is switched off.

## Why the TRVs' own external-sensor features are not used

> Since 2026-11-10 HA controls the valves (`room_thermostat.yaml`) by setpoint
> 28 / 5, so this is the background to that choice and to the fallback, not the
> current state.

The Danfoss eTRV's native external-sensor feature holds an anticipatory ~1% valve
opening and never fully closes when fed an external sensor (confirmed across all
externally-fed TRVs; only an unfed one idles — see `DANFOSS.md` §2.6, and note
"off" is only 5°C anti-freeze, not a real off). Control was therefore handed to
Better Thermostat — which was then **trialled and removed** as not worth it.

What that leaves, and it matters with heating season coming: the external feed is
still disabled on the four eTRVs (`0x4015 = -8000`; Ada has a Sonoff TRVZB since
2026-10-26, see `PLANS.md` §7), so each one regulates on its
**internal** sensor, which sits on the radiator and reads warm. That is corrected
with a static per-room trim (`regulation_setpoint_offset`; on the TRVZB,
`local_temperature_offset` with the opposite sign; set 2026-10-17 —
values and rationale in `TRV_REGULATION.md` "Trims in force").
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
  went to weight 0), so every TRV room now has a room reference. Lola's two are named right
  (checked 2026-10-26: the door one warmed by hand jumped as `TH01 Sonoff Lola`).

## Adding New Areas

Areas are auto-detected from HA device assignments: an area gets a sensor when it holds a TRV whose model is in `room_climate.py`'s `TRV_MODELS`. Add corresponding template sensors to `trv-climate/climate.yaml` following existing pattern.
