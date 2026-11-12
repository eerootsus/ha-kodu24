# ha-kodu24

Home Assistant configuration for the house. It began as climate control alone,
which is why most of it is still TRVs, and now also carries the general
housekeeping packages that have nowhere better to live:

- **`trv-climate/` + `room_climate.py`** — pyscript climate sensors for the
  TRVs - Danfoss eTRVs, one Sonoff TRVZB (documented below). They are
  observability, not control: Better Thermostat was trialled for control and
  removed, so the TRVs regulate themselves.
- **`trv-climate/offset.yaml`** — measures how far each TRV's own sensor sits
  from the real room, so the per-room trim is a number rather than a guess.
  Read the `_settled` sensors; see `TRV_REGULATION.md`.
- **`trv-climate/heating_alerts.yaml`** — push alert when a TRV room stays under
  its own target, naming the likely knob (curve shift / trim / valve fault), plus
  an alert when a room's sensors go silent. Alert only; nothing is adjusted.
- **`trv-climate/condensation.yaml`** — mould and condensation risk at the outer
  walls, from each room's outer-wall "Alt" sensor and its door reference: wall
  humidity, dew-point margin, and a push when the wall stays damp (72 h mean
  ≥ 75 %) or nears the dew point. Advise only. Here the risk is summer into
  October, not winter.
- **`heating-check.py`** — per-room "how well does each room hold its target"
  over a week, against a fixed pre-trim baseline, with degree-days and gas per
  degree-day so different weeks compare.
- **`trv-climate/dashboard/heating_view.yaml`** — record of the Küte dashboard
  view (storage mode; the live copy is in `/config/.storage`): room cards, boiler
  tiles, and the live Diagnostika table (room vs TRV vs target, sensors, trim,
  valve).
- **`PLANS.md`** — everything not built yet: installs waiting for a visit
  (radiator balancing, routers, sensors), HA work, and the house background they
  need. The repo is the source of truth for the Kodu 24 smart home; the Obsidian
  note only points here.
- **`dashboard.py`** — keeps a storage-mode dashboard view and its YAML record in
  step: `check`, `apply`, `pull` (see `CLAUDE.md` "Dashboards").
- **`workshop-heating/`** — on/off heating of the workshop with its split unit,
  17–19 °C, October–April, with a fail-safe that switches it off if its sensor
  goes silent.
- **`heating-pressure/`** — push alerts for the heating system pressure: top-up
  due (≤ 1.5 bar on the sensor for 12 h), critically low (< 1.2), and the slow
  leak getting faster (daily mean down > 0.2 bar in a week).
- **`battery-monitor/`** — weekly battery nudge, plus immediate alerts for
  safety devices.
- **`backup-monitor/`** — push alerts for the off-site backups running on
  `alpine-docker` (the jobs themselves live in the `unraid` repo), and for HA's
  own backups: `ha_backup_copies.py` checks that the newest automatic backup is
  on the Yellow, in Nabu Casa and on the Hetzner Storage Box - two off-site
  copies, not one. Job `immich` (2026-11-10) watches phone photo uploads per
  person: `fail` when someone's Immich count has not grown in 14 days. HA's own
  Immich integration was not used: its counts are server totals, so it cannot
  see one phone stop while another keeps uploading.
- **`chores/`** — household chore rotation, notifications and dashboard cards
  (see `chores/README.md`). Merged in from the former `ha-chores` repo with
  its history intact.
- **`themes/`** — HA themes; currently the e-ink serif theme the chores
  dashboard is built around.
- **`zigbee-topology.sh` + `topology/`** — reads ZHA's neighbour table to print
  who parents whom and at what first-hop LQI, and stores tracked snapshots.
  `sensor.*_lqi` measures a different hop and will mislead you; see `CLAUDE.md`.
- **`configuration.yaml`** — HA's root config, tracked here since 2026-09-05.
  Its `packages:` block decides what HA actually loads, so a package directory
  in this repo does nothing until it is listed there.

## Deploying

```sh
./deploy.sh -n         # dry run, shows exactly what would change
./deploy.sh            # rsync + `ha core check`
./deploy.sh --restart  # ...and restart HA
```

Runs over the tailnet (HA is not reachable from the workstation's LAN segment)
and needs the SSH add-on to accept your key (two are authorized; see
`CLAUDE.md` "Transport gotchas"). **Edit here, not in
`/config`** — deploys overwrite the live copies.

`curve-test/` is deployed but switched off: once started (`script.curve_test_start`)
it raises the heating curve on a sustained room shortfall and records how cold each
curve survived (`HEATING_CURVE_TEST.md`). Starting it is a deliberate decision, not
a deploy.

Dashboards are storage mode, so the YAML under `*/dashboard/` is a record, not
what HA loads — see the dashboard section in `CLAUDE.md` for how to change them
from the shell and keep the record in step.

## Climate

Pyscript room-climate sensors for the radiator TRVs: three Danfoss eTRV0103s (kitchen,
Master, stairwell) and Sonoff TRVZBs on Ada's radiator since 2026-10-26 and Lola's since 2026-11-12.

`room_climate.py` is **sensor aggregation only** — it performs no writes to the TRVs.
It was trimmed that way for Better Thermostat, which was then trialled and removed
(`TRV_REGULATION.md`). Since 2026-11-10 these sensors drive HA's room thermostat
(`trv-climate/room_thermostat.yaml`), which opens or shuts each TRV from its room's
door sensor; each TRV's own PID on its internal sensor plus trim is the fallback.

### Features

- Publishes one weighted virtual temperature/humidity sensor per area
  (`sensor.climate_{area_id}_temperature` / `_humidity`). An area with no usable
  external sensor is published as `unavailable` rather than omitted, so a dead
  sensor shows (every TRV room has one since 2026-10-25)
- Weights come from device labels (`sensor_weight_X`); TRVs find the areas but
  their own temperatures are **excluded**, so heating does not skew the average
- Only TRVs whose model is in `TRV_MODELS` (`eTRV0103`, `TRVZB`) count. A TRV of
  any other model leaves its room unpublished - and an already-published sensor
  then freezes at its last value rather than going `unavailable`, which is how
  Ada's room went blind 2026-10-26 → 11-05

Removed in the Better Thermostat cutover: the external-sensor feed, weekly time
sync, radiator-covered writes, load-balancing disable, and the Zigbee retry queue.
BT is gone now too, so **git history is the only copy** — that is where to look if
room-based control is ever wanted back.

## Home Assistant Setup

`./deploy.sh` does all of this — `room_climate.py` and `trv-climate/` are both in its
manifest and `climate_sensors:` is already declared in the tracked
`configuration.yaml`. What lands where:

```
config/
├── pyscript/
│   └── room_climate.py               <- main pyscript
├── trv-climate/
│   └── climate.yaml                  <- template sensors with unique_ids
└── configuration.yaml
```

Pyscript picks up a changed module on `pyscript.reload`; the template sensors need
`template.reload` or a restart.

---

## How It Works

### Virtual Temperature Sensors

The pyscript creates virtual sensors (`sensor.climate_{area_id}_temperature`) by:
1. Finding all TRVs (of a model in `TRV_MODELS`) assigned to each area — this decides *which* areas get a sensor
2. Reading the labelled external sensors in those areas
3. Calculating the weighted average from those sensors alone. **TRV temperatures
   are not in it at all** (an earlier version gave them weight 0.5); a valve's own
   reading tracks the radiator, not the room
4. Creating virtual sensor entities

An area whose external sensors are all missing gets no usable value, and the
wrapping template sensor goes `unavailable`.

The template sensors in `trv-climate/climate.yaml` wrap these with proper
`unique_id` for UI management (area assignment, customization).

### External Temperature Sensors

To add external temperature sensors (e.g., a separate Zigbee sensor):
1. Assign the device to the same area as the TRVs
2. Add a label `sensor_weight_X` where X is the weight (e.g., `sensor_weight_2` for double weight)

### Device Labels

- `sensor_weight_X` - Includes device's temperature sensor in room average with weight X

`radiator_covered` used to be read from a label and written to the TRV; that write
went with the rest of the control logic. The label is inert now.

### Enable History Graphs for Load Estimates

**Already done** — this block is in the tracked `configuration.yaml`. Kept here as
the reason it is there: the eTRV load estimate sensors carry no `state_class`, so HA
records no history for them without it. (Ada's and Lola's lines went with their eTRVs;
the TRVZB has no load estimate.)

```yaml
homeassistant:
  customize:
    sensor.trv_danfoss_kitchen_load_estimate:
      state_class: measurement
    sensor.trv_danfoss_lola_load_estimate:
      state_class: measurement
    sensor.trv_danfoss_master_load_estimate:
      state_class: measurement
    sensor.trv_danfoss_stairwell_load_estimate:
      state_class: measurement
```

---

## Scheduled Tasks

| Schedule | Function | Description |
|----------|----------|-------------|
| Startup + every 5 min | `update_room_climate_sensors` | Publish the virtual room sensors |

That is the whole schedule. `set_time`, `radiator_covered`,
`disable_load_balancing`, `update_external_temperatures`, `update_heating_season`
and `process_pending_writes` were all removed in the Better Thermostat cutover,
and with them the Zigbee retry queue and its `pyscript.get_pending_writes` debug
service. Nothing in this repo writes to a TRV any more.

The queue existed because eTRVs are sleepy end-devices that miss one-shot writes
(`DANFOSS.md` §1.1). That constraint still holds for anything that *does* write to
them — `trv_debug.py` and `trv_unstick.py` included — so re-read a value back
before trusting that a write landed.

---

## Adding New Areas

When you add TRVs to a new area:

1. The pyscript will automatically create `sensor.climate_{area_id}_temperature`,
   provided the TRV's model is in `TRV_MODELS` in `room_climate.py` (add it there if not)
2. Add a new entry to `trv-climate/climate.yaml`:

```yaml
      - name: "New Room Temperature"
        unique_id: climate_new_room_temperature
        device_class: temperature
        state_class: measurement
        unit_of_measurement: "°C"
        state: "{{ states('sensor.climate_new_room_temperature') }}"
        availability: "{{ states('sensor.climate_new_room_temperature') not in ['unknown', 'unavailable'] }}"
```

3. Reload YAML or restart Home Assistant

## Battery monitor

`battery-monitor/battery_monitor.yaml` — a weekly Sunday-morning digest of dead and
low batteries, plus an immediate alert when a **leak/smoke sensor** goes offline
(a flat battery on those fails silently: no alert, and no warning that there is no
alert). Deployed by `deploy.sh` and declared under `packages:` in
`configuration.yaml`.

Threshold `sensor.battery_warning_level` is **20 %** (40 % until 2026-10-25, for lead
time while the mesh was thin; see the feedback loop below). It is fixed in the YAML,
not a slider: change it there and deploy.

**Why batteries and the mesh are one problem:** a thin mesh makes sleepy devices retry
transmissions, retries burn battery, dead devices remove what little routing exists, and
the mesh gets thinner still. **Fresh batteries in a bad mesh drain again** — the routers
are the fix, batteries are symptom relief. Do the ZBMINIR2s first, or at least in the
same visit.

Battery levels are numeric, so HA long-term statistics keep them indefinitely: the
decline slope before vs after the routers go in is directly plottable, which makes this
the instrument for confirming the mesh work actually helped.
