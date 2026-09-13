# ha-kodu24

Home Assistant configuration for the house. It began as climate control alone,
which is why most of it is still TRVs, and now also carries the general
housekeeping packages that have nowhere better to live:

- **`trv-climate/` + `danfoss.py`** — pyscript climate sensors for Danfoss
  TRVs (documented below). They are observability, not control: Better Thermostat
  was trialled for control and removed, so the TRVs regulate themselves.
- **`battery-monitor/`** — weekly battery nudge, plus immediate alerts for
  safety devices.
- **`backup-monitor/`** — push alerts for the off-site backups running on
  `alpine-docker`. The backup jobs themselves live in the `unraid` repo.
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
and needs the SSH add-on holding this workstation's key. **Edit here, not in
`/config`** — deploys overwrite the live copies.

`curve-test/` is deliberately not deployed: it steps the heating curve down to
find the house's tolerance floor, so it goes live only on a conscious decision.

Dashboards are storage mode, so the YAML under `*/dashboard/` is a record, not
what HA loads — see the dashboard section in `CLAUDE.md` for how to change them
from the shell and keep the record in step.

## Climate

Pyscript-based climate control for Danfoss TRVs in Home Assistant.

`danfoss.py` is **sensor aggregation only** — it performs no writes to the TRVs.
It was trimmed that way for Better Thermostat, which was then trialled and removed
(`BETTER_THERMOSTAT.md`). So nothing applies room-based control today: each eTRV
runs its own PID on its own internal sensor, and these sensors feed the dashboard
and the heating-curve test.

### Features

- Publishes one weighted virtual temperature/humidity sensor per area
  (`sensor.climate_{area_id}_temperature` / `_humidity`). An area with no usable
  external sensor is published as `unavailable` rather than omitted — that is
  Stairwell's normal state, not a fault
- Weights come from device labels (`sensor_weight_X`); TRVs find the areas but
  their own temperatures are **excluded**, so heating does not skew the average

Removed in the Better Thermostat cutover: the external-sensor feed, weekly time
sync, radiator-covered writes, load-balancing disable, and the Zigbee retry queue.
BT is gone now too, so **git history is the only copy** — that is where to look if
room-based control is ever wanted back.

## Home Assistant Setup

`./deploy.sh` does all of this — `danfoss.py` and `trv-climate/` are both in its
manifest and `climate_sensors:` is already declared in the tracked
`configuration.yaml`. What lands where:

```
config/
├── pyscript/
│   └── danfoss.py                    <- main pyscript
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
1. Finding all TRVs assigned to each area — this decides *which* areas get a sensor
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
the reason it is there: the TRV load estimate sensors carry no `state_class`, so HA
records no history for them without it.

```yaml
homeassistant:
  customize:
    sensor.trv_danfoss_ada_load_estimate:
      state_class: measurement
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

1. The pyscript will automatically create `sensor.climate_{area_id}_temperature`
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
alert). Copy to `config/battery-monitor/` and include as a package.

Threshold `input_number.battery_warn_level` defaults to **40 %**, higher than the usual
20–25 %, because of the feedback loop below.

**Why batteries and the mesh are one problem:** a thin mesh makes sleepy devices retry
transmissions, retries burn battery, dead devices remove what little routing exists, and
the mesh gets thinner still. **Fresh batteries in a bad mesh drain again** — the routers
are the fix, batteries are symptom relief. Do the ZBMINIR2s first, or at least in the
same visit.

Battery levels are numeric, so HA long-term statistics keep them indefinitely: the
decline slope before vs after the routers go in is directly plottable, which makes this
the instrument for confirming the mesh work actually helped.
