# Better Thermostat: evaluated, and dropped

**Outcome (2026-09-13): Better Thermostat was installed, trialled and removed.** It
offered nothing meaningful over the eTRVs' own control, so the integration is gone
and there is no `climate.*_better_thermostat` entity. This file is kept as the
record of why it was tried, what was changed on the TRVs for it, and — below — what
that leaves us with, because several of those device changes are **still in force**.

Read `DANFOSS.md` for the device reference. What follows is history plus the
current baseline.

## What we were trying to fix

The Danfoss eTRV's **native external room sensor** feature gives accurate
room-based control but holds an anticipatory ~1 % valve opening that never fully
closes (see `DANFOSS.md` — the PID floor, observed year-round on every
externally-fed TRV; only the one TRV *without* an external sensor idles at 0 %).
With this firmware you cannot have both accurate external-sensor control **and** a
fully-closing valve. The plan was to hand control to **Better Thermostat (BT)** and
use each eTRV as a calibrated actuator instead.

## Where control actually sits now

```
labelled room sensors  ──►  danfoss.py  ──►  sensor.climate_<area>_*
                                                   (observability + curve test)

eTRV internal sensor   ──►  eTRV's own PID  ──►  valve
                            setpoint set by hand / schedule
```

**Nothing applies room-based control.** Each eTRV regulates on its own internal
sensor, because the external feed is disabled (`0x4015 = -8000`, left over from the
BT preparation and **not** reverted). `danfoss.py` still publishes the weighted room
sensors, but nothing consumes them for control — they are for the dashboard and for
`HEATING_CURVE_TEST.md`.

Worth knowing before the heating season: an eTRV's internal sensor sits on the
radiator, so it reads warm and the valve throttles early. That is the inaccuracy the
external-sensor feature exists to correct, and it is currently off on all five. The
options, none of them taken yet:

- **Leave it.** Simplest; accept whatever per-room offset the valves settle at, and
  trim it with the setpoint. The room sensors make the error measurable.
- **Turn the external feed back on** (re-add something like the old
  `update_external_temperatures`). Accurate, but brings back the 1 % floor that
  started this whole thread — fine in winter, the summer problem again in June.
- **Use `0x404B` Regulation SetPoint Offset** (±2.5 K) as a static per-room trim
  from the room sensors. Small range, but it needs no continuous feed.

## Target architecture that was planned (not built)

```
weighted room sensors (danfoss.py)  ──►  Better Thermostat (per room)  ──►  eTRV
sensor.climate_<area>_temperature        target temp + calibration            (actuator)
                                          outdoor threshold (summer off)
```

- **danfoss.py is now sensor-aggregation only:** `update_room_climate_sensors`
  publishes the weighted `sensor.climate_<area>_temperature` (BT's per-room input)
  plus its helpers. **All TRV writes were removed** (time sync, radiator-covered,
  load-balancing, external-sensor feed, retry queue) so it cannot fight BT.
- **eTRV native external sensor is turned OFF** so it doesn't fight BT:
  `prioritize external temperature sensor = off` and external sensor = `-8000`
  (done on all TRVs).

## Per-room mapping

| Room | eTRV climate entity | BT external sensor input |
|------|---------------------|--------------------------|
| Ada | `climate.trv_danfoss_ada` | `sensor.climate_ada_s_room_temperature` |
| Master/Bedroom | `climate.trv_danfoss_master_thermostat_4` | `sensor.climate_bedroom_temperature` |
| Kitchen | `climate.trv_danfoss_kitchen_thermostat_5` | `sensor.climate_kitchen_temperature` |
| Lola | `climate.trv_danfoss_lola` | `sensor.climate_lola_s_room_temperature` |
| Stairwell | `climate.trv_danfoss_stairwell_thermostat_3` | (no external sensor — TRV internal only) |

## Setup steps (not to be followed — kept for what they changed on the devices)

Steps 2's device changes were applied and are still live. The rest was abandoned.

1. **Install Better Thermostat** via HACS (Integrations → Better Thermostat), then
   restart HA.
2. **Disable the eTRV native external sensor** on every TRV so BT has sole control:
   `switch.*prioritize_external_temperature_sensor` → off and external = `-8000`.
   (Already done on all five; danfoss.py no longer pushes `0x4015`.)
3. **Add a Better Thermostat** per room (Settings → Devices & Services → Add →
   Better Thermostat) with:
   - **Thermostat:** the eTRV climate entity (table above)
   - **Temperature sensor:** the room's `sensor.climate_<area>_temperature`
   - **Outdoor sensor:** `sensor.vicare_outside_temperature` + outdoor threshold
     (e.g. 18 °C) → this is the summer-off mechanism, replacing `update_heating_season`
   - **Calibration type:** **Target Temperature Based** (Danfoss's offset is capped
     at ±2.5 K — too small; let BT drive the setpoint instead)
   - **Algorithm:** start **Normal**; revisit AI Time Based / PID later
   - **Window sensors:** optional; if used, disable the eTRV's own open-window
     detection to avoid double-handling
   - **Tolerance:** small (e.g. 0.3 °C) to limit valve cycling
4. **Verify:** with a room above target, BT should drive the eTRV to its off/5 °C
   state and `pi_heating_demand` should reach **0** (the thing native mode never did).

`danfoss.py` was trimmed to sensor-aggregation only for this plan. That trimming
stands — it writes nothing to the TRVs — even though BT is gone, so **if room-based
control is ever wanted again the control logic has to come back from git history or
be rewritten**. See "Where control actually sits now" above.

## Firmware & config baseline (verified)

- **Firmware is already uniform and current:** all five report
  `sw_version = 0x00000020`, and every `update.*_firmware` entity is `off`
  (installed == latest). **No OTA update is needed or available** — don't chase one.
- The differing entity names (EN "prioritise" / EN "prioritize" / Estonian for
  Stairwell, plus extra `heat_available`/pre-heat entities on Lola & Ada) are **ZHA
  quirk/locale variants at pairing time, not firmware** — cosmetic, no behavioural
  effect. Re-interviewing a device *may* normalize names but is unnecessary.
- **Behavioural config is unified across all five:** `prioritize external = off`,
  external sensor = `-8000`, load balancing off, min/max 5/35, valve orientation
  Horizontal, setpoint response "quick 5min", valve exercise Thu 11:00, adaptation
  enabled.
- **Watch item (resolved 2026-09-13):** Lola's Zigbee link was weak (`lqi`/`rssi`
  unknown; writes needed several retries). The ZBMINIR2 routers went in and Lola
  re-parented onto one — LQI 217 to her parent. Use `./zigbee-topology.sh`, not
  `sensor.*_lqi`, to check this: the sensor reads the wrong hop and went *down* to
  ~118 as her actual link improved.
- **Note:** the eTRV clock is no longer synced by this project (set_time was
  removed). It only affects valve-exercise/adaptation timing, not BT control; sync
  once manually via ZHA if desired.

## Status — 2026-09-13

- **Better Thermostat: installed, trialled, removed.** It offered nothing meaningful
  over the eTRVs' own control. `/config/custom_components/` holds only `hacs` and
  `pyscript`; no BT entity exists. Not a regression — a decision.
- **Room sensors: working again.** They had been dead for some time — `danfoss.py`
  threw on every run after an HA change to the device registry (fixed 2026-09-13).
  Four rooms report; Stairwell is `unavailable` because it has no labelled external
  sensor, which is correct rather than broken.
- **TRVs: running on their own internal sensors**, setpoints set by hand. Four still
  sit at `pi_heating_demand = 1` and Stairwell at 0.

## Open issue: radiator TRVs stuck at 1 % (summer warmth)

Four radiator TRVs (ada, master, kitchen, lola) hold `pi_heating_demand = 1 %` and
the radiators stay warm in summer; only **stairwell** idles at 0 %. Because the
boiler must keep circulating (~25 °C) to feed the **bathroom underfloor loops**,
the loop stays hot and a 1 % valve still passes heat — so turning heating off at
the boiler isn't an option; the radiator valves themselves must close.

**Tried remotely — none worked** (verified via API): `prioritize external` off,
external sensor `−8000`, `heat_available` off, and the community `radiator_covered`
cycle + setpoint nudge (z2m #19495). Even on Ada (best link) nothing moved. A raw
attribute dump showed the four configured identically to Stairwell
(`radiator_covered = False`, external `−8000`, offsets 0, adaptation done).

**Suspected confounder at the time: a thin Zigbee mesh.** 29 sleepy end-devices,
Lola at `rssi −93`, a corner at −100, and router-capable TRADFRI bulbs `unavailable`
(lost hops). Writes routinely fail/retry and can't be verified as landed (fresh
reads time out), so "fix didn't work" may = "write never arrived."

**That theory is now weak.** ZBMINIR2 routers went in, Lola re-parented onto one and
her link improved (LQI 217 to her parent; `rssi −81`, and see `CLAUDE.md` on why the
`sensor.*_lqi` number misleads). The mesh is materially better and **the four are
still at 1 %** — while Stairwell, the healthy one, is a coordinator child on the same
kind of link as the stuck ones. Whatever holds the valve open is not the radio. The
external-sensor control path (§2.6) remains the best explanation, which is consistent
with Stairwell being the one TRV never fed an external sensor.

**Chosen resolution:** physically **close the manual lockshield valve** on the
radiators where possible for summer — bulletproof, independent of TRV/mesh. Accepted
trade-off: those radiators can't be turned on for a cold summer night until reopened.

**If the mesh is improved later:** re-deploy `trv_debug.py` (attribute dump) and
`trv_unstick.py` (cycle covered + setpoint nudge), re-run on the reliable network,
and confirm writes land via fresh read-back before trusting any result.

## Sources
- Danfoss Ally PID quirks / unstick (cycle radiator_covered + setpoint) — https://github.com/Koenkk/zigbee2mqtt/discussions/19495
- Better Thermostat docs — https://better-thermostat.org/configuration
- Danfoss Ally external-sensor calibration writeup — https://ha-praksis.dk/en/case-calibrating-danfoss-ally-with-external-temperature-sensors/
- Danfoss Ally firmware archive (v1.28/v1.20/v1.18/v1.08), ZHA/deCONZ/Z2M —
  https://community.home-assistant.io/t/danfoss-ally-thermostat-firmware-archive-v1-28-v1-20-v1-18-v1-08-specifications-zha-deconz-zigbee2mqtt/261951
