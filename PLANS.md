# Kodu 24 — open work and plans

The repo is the source of truth for the Kodu 24 smart home. This file holds what
is *not built yet*: installs waiting for a visit, HA work waiting for an evening,
and the background those need. What is built is documented where it lives
(`README.md` for the map, `CLAUDE.md` for how things work, `TRV_REGULATION.md`
for TRV control, `HEATING_CURVE_TEST.md` for the boiler curve).

The Obsidian vault (`Projects/Smart home.md`) only carries next-action lines for
the personal TODO and points here. Do not grow a second copy there.

When something here gets done, move its outcome into the doc of the thing it
built and delete it from this file.

---

## Next visit to Kodu 24

### 1. Hydraulic balance — radiator valve presets

**Presets set 2026-10-26** - radiators, runs, the before/after runs and the presets
chosen are in `TRV_REGULATION.md` "Radiator presets". Still open:

1. **Fine-tune by temperature drop:** TRV fully open, IR thermometer on supply
   and return pipe. Aim for ~5–8 °C drop at 35–40 °C supply, about the same on
   each. Small drop (2–3 °C) = water rushing through → throttle; large drop =
   starved → open. This decides; the presets only got close.
2. **After:** switch the room thermostat off, run `script.balancing_test` again
   (label "after", `cool_minutes: 240`, `open_minutes: 90`, a similar outside
   temperature; the result sensor keeps the previous run beside it), switch it back
   on. Then compare valve duty before and after (`./heating-check.py --duty`). One
   lever at a time.

Under the room thermostat (since 2026-11-10) every room is held at target whatever
its share of flow, so this is about efficiency and even valve duty, not comfort: a room
whose valve runs much longer than its neighbours at the same weather is the one short
of water.

**Every summer:** to stop the 1 % summer heat (`DANFOSS.md` §2.6), close the
**radiator master valves** between the boiler and the radiator manifold. That shuts
all five radiators in one place while the bathroom underfloor loops keep running
(switching heating off at the boiler would stop those too). Never touch the presets
for summer - the balance survives, and autumn is just reopening the master valves.

**Debris - check it before turning a knob.** Half the system is old and has had
debris before (flushed, inhibitor added). Turning the kitchen H-valve on 2026-10-26
gave a hiss, like something giving way or a valve that had not really been open. Lower
presets make the insert's gap narrower, so particles lodge more easily: a room that
drifts after being stable, or a preset that seems to stop working, may be dirt, not
balance. Run its ring fully closed and open a couple of times before changing the
setting. Lola's jump in the "after" run (6 → 4 yet faster than "before") may have been
a pin freed by the visit rather than a flow change.

**Filtration** - two separate jobs:
- **Heating circuit:** a magnetic dirt separator on the return before the boiler
  (check first whether one is under the Vitodens). Catches magnetite all the time,
  protecting the boiler's heat exchanger and the insert gaps.
- **Incoming mains water:** a filter on the cold supply, suggested by the boiler
  company to protect the hot-water side. Top-ups of the heating also come from the
  mains, so it helps there too.

### 2. Curve shift - decide on the kitchen in the cold

**2026-11-13: decided - curve 1.4/−2, kitchen target 21.0, night setback 23:00-05:00
(room setting 21).** Reasoning, model and tables in `HEATING_CURVE_TEST.md` "Reference
curve"; the setback is `trv-climate/boiler_setback.yaml`. Still open:
- **First −5..−10 °C days:** kitchen should hold ≥ 20 (Eero's floor) by day; if
  Ada / Lola / Master run warm while it does, step down to 1.3/0. If the kitchen
  falls under 20, raise the shift by 1 (`./curve-model.py`, re-calibrated, says how far).
- **First mornings after the setback:** how long the kitchen takes to recover; end it
  at 04:00 instead of 05:00 if breakfast is cold. Bedrooms must not alert at night.
  First night (13/14, ~3.5 °C out): writes 23:01 / 05:01 took, mean supply ~46 vs
  47.7 the night before (the ~2.3 K the curve predicts); kitchen sagged to 20.7-20.9
  and was back at 21.0 by 09:00, bedrooms fine. The floors cannot see it as long as
  the boiler stays above the Uponor head's ~38 °C: living room 21.3 → 21.4, bathrooms
  unchanged (but those sensors report coarsely). Kept as is (Eero, 2026-11-14) -
  adjust only if the people living there report cold floors or mornings.
- **Weekday away-mode, parked:** lower room targets while everyone is out (presence,
  not a fixed schedule) - maybe 2-4 % more gas; revisit after a couple of weeks of the
  night setback.
- The gas/radiator heat gap is the living-room floor (runs all winter) plus pipe heat
  (`HEATING_CURVE_TEST.md` "Unexplained") - the floor side is the next project ("Floor
  heating" under HA work). The radiator runs go from the manifold through the floor
  void, in the downstairs ceiling (Eero, 2026-11-13), so their heat stays inside the
  house - nothing to lag; it is part of the "pipe heat" in the gap.
  Last winter's 82 °C plateau goes with §8's flow/return sensors.

How the curve got here (+2 → +6, then 1.4/−2) is in `HEATING_CURVE_TEST.md` "Curve in
force"; the kitchen's valve pin was worked on site 2026-11-12 and moves freely, so a
short kitchen is the curve and the wind.

### 3. TRVZBs for the other radiators; Lola's room

- **Order three Sonoff TRVZBs - kitchen first, then Master and stairwell** (decided
  2026-11-17: Lola's TRVZB passed, result in `TRV_REGULATION.md`, Lola row). Fit each
  with `CLAUDE.md` "Swapping an eTRV for a TRVZB"; the stairwell (28 %) and Master
  (34 %) eTRV batteries (§5) go with them. Under the room thermostat the eTRVs already
  act as plain valves, so the case is that TRVZBs close fully in summer and carry no
  hidden logic - the first still unproven until spring (§7).
- **Parked: feeding the room temperature to the TRVZBs** (their external input), only
  needed if the room thermostat is ever dropped.
  **Feed design - never regulate on a frozen number** (Eero, 2026-11-10). The feed
  depends on a sensor battery and the mesh, so it picks its source by freshness, per
  room, in this order:
  1. **Door sensor** (the room reference) - fresh = reported within ~30 min
     (`last_reported`, not `last_changed`: a steady room does not change).
  2. **The room's Alt sensor**, corrected by that room's typical door − Alt
     difference (the outer-wall Alt reads ~0.4-0.8 K colder - `heating-check`'s
     wall-door figures; learn it as a rolling median while both are fresh). Lola,
     Ada, Master and the kitchen have one; the stairwell does not.
  3. **The TRV's own sensor** - switch the external input off, so it regulates as
     it does today, with its local offset as the trim.
  Every switch of source pushes once (which room, from what to what, why), and
  `battery-monitor/` should flag the room sensors early, since a dead one now
  costs control, not just a chart. Switching back up the chain is automatic once
  the better source is fresh again. Build and test it on Lola first (pull a door
  sensor's battery on purpose), then copy it to each room as its TRVZB goes in.
- **Humidity** (7-day mean 67 %, >70 % most nights) is the **plants** — thin them
  first. A 2026-10-17 analysis of 74 heating-season nights found no wind effect on
  her overnight moisture gain (r −0.02), a modest stack-effect one (r −0.30) and a
  small gain (~+0.25 g/m³ per night): ventilation copes, the baseline is high. A CO₂
  sensor is the definitive ventilation test if still needed.
- **Lola's room by day (found 2026-11-17).** From ~11:00 her valve stays "open" all
  afternoon and the room sits at 21.3-21.4, never reaching 21.5; nights cycle normally.
  Ada's room, the hall (stairwell sensor, next to Lola's door) and the wind show no such
  pattern, so it is her room only. Two parts:
  1. **Her TRVZB idling at the open setpoint 28** - head in a warm pocket (headboard +
     curtains; even shut it cools only to 22-24 vs Ada's 20-21), so by day it heated ~half
     the time HA held it open. Fixed 2026-11-17: open = 32. **Check 11-18 from 11:00
     (`heating-check.py --duty`, `sensor.trv_sonoff_lola_hvac_action`):** does the
     daytime run now reach 21.5 and shut? If yes, part 2 is minor.
  2. **More outside air by day, before the TRVZB too.** Her window side cools against her
     door sensor by day (door - wall gap 0.37 K vs 0.19 at night; eTRV era 0.28 vs 0.16),
     and her room dries by day (absolute humidity −0.59 g/m³ day vs night; Ada +0.05,
     hall −0.01). Both doors stand open by day. Lead: her **fresh-air inlet** is not
     fully closed, and with her door open by day outside air flows in through it to the
     hall and extract; at night the shut door blocks the path. **Next visit: check
     Lola's and Ada's inlets.** If hers is open, close it only partly and watch her
     humidity a week - her room is the humid one (plants, above), and the inlet may be
     what keeps that in check. Also: how close the headboard and curtains are to her TRV.
     **Or an air leak** in her exposed SE corner (corner joint, window frames, floor
     edge, sockets in the outer walls) - from the sensors it looks the same as an open
     inlet: it needs the open door as the way out, so it shows only by day. A gap in the
     *insulation* alone does not fit: conduction is steady (worse at night, when it is
     colder) and cannot dry the air, and her wall-side sensor stays 8-9.5 K above the
     dew point, so nothing condenses there. **To tell them apart:** inlet first; then,
     door open in some wind, an incense stick along the corner, window frames, skirting
     and sockets; a thermal camera on a cold morning shows both (missing insulation =
     a steady cold patch, a leak = cold streaks from a gap). **Free test, no visit:** one
     day with her door shut - if the daytime drying and window-side cooling vanish, it
     is an air path through her room (inlet or leak); if not, it is inside the room.
     **Checked 2026-11-17 (Eero): her inlet (PAX valve) is set closed but does not seal**
     - air movement is felt, and the damper disc shows a gap at its seat. So the air path
     is confirmed; an extra corner leak is not ruled out. It is in her **south wall** - the
     face the wind has been on (5-6 m/s onto S since 11-13) - which is why the same small
     leak moves more air than Ada's would on her sheltered east wall. Not yet known:
     whether Ada's leaks too. The foam filter is yellowed - cheap to replace.
     **Done 2026-11-17 ~22:30: Lola's inlet plugged** (Eero), the same evening as open =
     32 (21:36) - two changes at once, so 11-18 onward cannot say which one fixed the
     daytime run; the plug's own signature is her daytime drying (absolute humidity
     −0.59 g/m³ day vs night) and window-side cooling (door − wall 0.37 K) going away.
     **Watch her humidity** - her room is the humid one (plants) and this was its only
     fresh air with the door shut: `wall_rh_lola_72h` pushes at 75 %; if it climbs, open
     the inlet partly again rather than leave the plug in.
- **Master's inlet was open; closed 2026-11-17 ~22:30** (Eero). Expect lower valve duty
  (it was already the least-worked room, 4-37 %) and a warmer room, so watch for night
  overshoot, and higher humidity in a bedroom two people sleep in: `wall_rh_master`
  / `_72h`. If it climbs, set the inlet part-open rather than fully open.
- **Ada's inlet is on A (automatic)** - left as is (Eero, 2026-11-17). Her room shows
  no daytime drying or cooling and holds target evenly, so it is the reference: if Lola's
  or Master's humidity climbs with theirs shut, A is the setting to try first (Lola's
  needs its damper reseated for that to mean anything).

### 4. Zigbee routers — ZBMINIR2 (on the shelf since 2026-08-23)

In-wall relays behind a switch; real routers (~64 children). ⚠️ Need a
**neutral** in the box; **R2, not L2** — the no-neutral L2 does not route.

- **Sauna light switch** — the sauna light is already Zigbee, the switch is dumb.
  The relay must sit **outside the hot room** (rated ~40 °C vs 80–100 °C in the
  sauna; sauna wiring zones per EVS-HD 60364-7-703), away from shower spray.
- **Kitchen counter lights switch** — **drill the wall box deeper first**, or the
  relay won't fit.
- **Bathroom fan relay** — needed for humidity control anyway (see HA work), and
  a downstairs router.
- **Plug-in router in the master bedroom corner** (not a ZBMINIR2).
- **Paulmann light (living room) - keep it powered, control it over Zigbee.** It is a
  router, and it drops off the mesh whenever it is switched off at the wall (offline
  since 2026-11-04 18:28). Fix: power it permanently and add a Zigbee switch that sends
  commands instead of cutting power, like the kitchen lamps in §6.
- **Dead corner** (rssi −100).

**Why downstairs matters:** the laundry leak sensor hangs off the living-room
floor lamp (an IKEA bulb) at LQI 47 — a safety device on a weak link that dies when
the lamp is switched off at the wall. After installing: `./zigbee-topology.sh
--save`, a day later `--diff`. If the leak sensor has not moved, power-cycle the
floor lamp once (end devices never pick a new parent on their own).

**Avoid as routers:** Tuya (flaky), Aqara (poor router), bulbs (poor, and can be
switched off).

### 5. Batteries

Bathroom leak sensor replaced (100 %, 2026-11-13). Left: stairwell TRV 28 %, master TRV
34 % (2026-11-13) - both eTRVs, so they go with the TRVZB swap (§3) unless that slips.

### 6. Kitchen lamps as routers

Add the kitchen Zigbee switch **wired so the TRÅDFRI bulbs stay always powered**
(decoupled smart-bulb mode — the switch sends Zigbee commands, never cuts power),
or dumb bulbs + an always-live ZBMINIR2. Switched-off bulbs are dead routers.

### 7. Sonoff TRVZB - still to see

On Ada since 2026-10-26 and Lola since 2026-11-12 (settings in `TRV_REGULATION.md`, quirks in
`CLAUDE.md` "Swapping an eTRV for a TRVZB"). Still to see: calibration drift, and whether
they close fully in summer - the main reason for them. Alternative if they disappoint:
Eurotronic Spirit Zigbee. Avoid Tuya/Aqara TRVs.

### 8. Boiler flow/return ΔT - why the burner short-cycles

With every valve open (2026-11-10 evening) the burner still cycled in 3-10 min bursts
at ~44 °C supply (modulation 11-19 %), 55-78 starts a day the week before: the water
comes back nearly as hot as it left. The radiator loop has no bypass, and the
underfloor mixing unit was **ruled out on site 2026-11-12** ("Background", House:
it can only return water cooler than its ~33 °C floor flow). Two causes are left:

- **The radiators cannot take the boiler's minimum output** at this water temperature.
  Fix: hotter water (the curve, 1.4/−2 since 2026-11-13) or more emitter.
- **The Vitodens pump runs faster than needed.** Turning it down means fewer starts, a
  cooler return and better condensing.

**To do: buy two SNZB-02P** (Eero, 2026-11-11; borrowing the outer-wall Alts was
dropped - they stay for the condensation alerts) and strap them to the **flow and
return pipes at the boiler** under a bit of pipe insulation. No `sensor_weight_`
label, so they are not counted as room sensors. Log a normal day and a cold,
all-valves-open evening:

- ΔT **< ~5 K with all valves open** → the pump: lower the Vitodens pump speed.
- ΔT **10-15 K** → the radiators take what they can; only hotter water helps.

**Open question (Eero to decide):** the floor-heating plan below reads its pipe
temperatures with wired probes on an ESP32 (ESPHome). The boiler flow/return could go on
the same kind of board (or the same one, if the boiler and the Uponor mixer are close
enough to wire) instead of two SNZB-02P - wired probes report as often as asked and
need no batteries. Not decided.

Then add flow/return/ΔT to `./heating-check.py` and the Küte view.

---

## HA work (no visit needed)

- **Wind compensation - the open parts.** Since 2026-11-10 the room thermostat handles
  wind on the room side by feedback (a room the wind cools gets its valve opened; what
  that costs shows as valve duty, `./heating-check.py --duty`), so the wind trims and
  room-feed ideas are gone. Left: (1) an **automatic curve step** for a room whose valve
  is flat out and still short - by hand today, and Eero accepts the kitchen short in
  high wind (`CLAUDE.md` "Control principle"); (2) a **forecast step** (e.g. a
  curve-shift bump on a strong S/SW forecast) only if feedback proves too slow. Evidence
  to collect first: a cold S/SW day against a cold NW or calm one, by duty per room.
- **Bathroom fan on humidity** (after its relay is in): trigger on a fast rise
  (e.g. +8 points in 10 min = shower) or on being ~15 points above a reference room,
  off when back within a few points; minimum and maximum run time. Not a fixed %:
  the downstairs bathroom averages ~58 % in October and peaks at 92 %. **Before
  sizing a mechanical extract:** check no open-flue appliance shares the old
  chimney (backdraught). The Vitodens is room-sealed.
- **Better light automations.**
- **Matter lights + extra downstairs lighting, Matter smoke detectors** — on a
  separate Thread mesh (see below).

## Floor heating - the next project (Eero, 2026-11-13)

The floors are the other half of the heating and nothing in HA sees them: the living-room
rings alone give roughly as much winter heat as the five radiators, on a fixed mixer
setting (head 5 = 38 °C), with no control and no measurement. Same principle as the
radiators (CLAUDE.md "Control principle"): measure first, then put the logic in HA.

**Measure first:**
- **Floor circuit flow/return** after the Uponor PUSH-23: external probes on the pipes
  under insulation, read by an **ESP32 (ESPHome)** - Eero has the probes already
  (2026-11-14; check whether they are I2C or 1-wire DS18B20 before wiring). Wired probes
  report as often as asked, no batteries. The same board can later carry the zone-valve
  relays below. Gives the floor ΔT and, with §8, the floor's share of the boiler's heat.
- **Room temperatures exist already:** living room `sensor.th_living_room_temperature`
  (rings 1-2; "lounge" in the flow sheet is the same room), downstairs bathroom
  `sensor.tz2000_a476raq2_ts0201_temperature` ("TH downstairs bathroom", ring 3),
  upstairs bathroom `sensor.th_upstairs_bathroom_temperature_2` (ring 4).
  **All three are Tuya TS0201 (`_TZ2000_a476raq2`, the ones with a screen) and report
  far too rarely to control a floor on:** on 2026-11-14 the living room had changed once
  in 33 h and the downstairs bathroom not at all in a day, though all three were alive
  on the mesh. Replace them with SNZB-02P like the kitchen and stairwell door sensors,
  before any floor logic (three to buy).
- Then a heating-check-style view: living-room temperature against outside and the
  floor flow, to see whether it is overheated (= gas to save) or held.

**Then control** (the existing plan):
- **Zone valves**, not eTRVs: solenoid valves on an **ESP32 relay
  board** (WiFi, likely ESPHome), **normally open** (no power = heat, so every
  failure fails warm). Relay ON = zone CLOSED: expose a "zone open" switch with the
  relay inverted so the UI never shows on for closed; boot with all relays off;
  check the valves' continuous-duty rating (powered while held closed); the logic
  must never close every zone (pump). Floors are slow: wide band, long minimum
  on/off times (30–60 min). Bathroom loops must stay on year-round. Logic in HA,
  in this repo. **Physical install first, then the logic** — record which relay
  drives which zone and room while wiring.


---

## Background

### House

- Naturally ventilated: inlets in rooms, under-door gaps, extract via the old
  chimney (stack effect, little wind effect measured). Hallway extracts are an
  option; they would work by stack effect — high, into a warm flue — and one grille
  per flue.
- **Construction (Eero, 2026-11-13):** a wooden building (1931 project); only the
  central common stairwell is masonry. Basement foundation and walls are limestone.
  **The kitchen is a later addition in ash/cinder block** (tuhkplokk-type), so the room
  that sets the curve is built differently from the rest: more mass (it cools and
  recovers slower than the wooden rooms), likely a worse wall U-value than the log
  walls, and the joint to the old house was a suspected draught path. **Checked
  2026-11-13** on 696 h of Alt-vs-door-sensor offsets (regressed on room−outside and the
  wind onto the S and W walls): the Master Alt, next to the joint, does **not** react to
  southerly wind (+0.003 K per m/s), but cools 0.045 K per K of room−outside - 5× Lola's
  south-wall Alt (0.009) and as steep as the kitchen's (0.043). So a cold bridge / poorly
  insulated junction, not a draught (caveat: Alt placement differs; Master's room
  sensor gets en-suite floor heat). The kitchen's Alt is the one that takes wind:
  −0.04 K per m/s onto S, −0.08 onto W. Worth a look when insulation comes up.
  So the flat has little thermal mass: rooms cool and recover within hours, which
  makes a setback show in the rooms (and save) more than in a masonry house - and
  makes the kitchen's slow recovery after one matter more.
- **Layout and orientation** (from the 2019 renovation drawings in `~/Documents/Kodu
  24/2019 Remont/Plaanid-joonised`, `Kodu - 20190404.pdf` p.6 = radiators, and the
  1997 floor plans in `Maja/Kodu_tn_24_projekt`; confirmed by Eero 2026-11-10). Flat 1
  is the **south half of the ground floor**; the building holds two mirrored flats per
  floor with a common stairwell entered from the middle of the street facade. Kodu tn
  is to the **east**; the building is turned only ~10-15° clockwise, so the faces are
  close to the compass points:
  - **West end (garden, terrace; workshop below):** kitchen + dining, open through a
    large opening into the **gallery** (a wide hallway section, with double doors to
    Master) along the north side; the hallway continues past the WC, Ada and Lola to
    the stairwell. No floor heating in this open space (on this floor only the en-suite
    floor is heated). One radiator, under the west window. The
    kitchen is the **south-west corner**: two outer walls, south and west, and both
    face open gardens (Eero, 2026-11-11), so it is the most wind-exposed room.
  - **South long wall (outer):** Master (next to the kitchen; manifold at its inner
    corner), the stair-room radiator, and **Lola's** room in the south-east corner (two
    outer walls, south and east).
  - **East end (street):** mostly sheltered - Kodu tn is lined with houses, so wind
    onto the east face counts for less than the same wind onto the open south and west.
    **Except Lola's south-east corner**, which looks down the open end of the street
    (Eero, 2026-11-11) and may catch wind from the south-east through that gap. The two children's rooms, radiators under the east windows:
    Lola's (corner) and **Ada's** in the north-east, which borders the common stairwell
    and has only the one outer wall. **Lola's room has two windows**; Ada's, Master and
    the stair room have one each (Eero, 2026-11-17) - with two outer walls, the most
    glass per radiator of the TRV rooms after the kitchen.
  - **North long side:** no outer wall - the party wall with the other ground-floor
    flat, and the common stairwell at its east end.
  - **Middle:** bathroom + WC on one shared floor-heating loop (the en-suite), next to
    the manifold.
  - **Downstairs:** the **living room** and a bathroom, both floor-heated, and the
    boiler, under Master, ~3 m from the manifold. Not connected to the kitchen. See
    "Floor heating" below.
  - **Above:** heated flats over all of it. **Below:** the workshop under the kitchen.
    Heated neighbours are therefore above and along the north (kitchen/hallway) side;
    the outer walls are south, west and east only.
  So a **SW wind** hits both open faces (south and west) - the kitchen on both its
  walls - and a **NW wind** only the west end; the kitchen borders Master but none of
  the other TRV rooms.
- The workshop is directly under the kitchen; its split HVAC and the (not yet
  commissioned) Panasonic heat-pump outdoor unit sit together under a large,
  skirted-but-gappy wooden terrace, a couple of metres apart. Watch for one unit's
  cold exhaust reaching the other's intake once both run: a Zigbee temperature
  sensor at the heat pump's intake vs met.no, split on vs off, answers it.
- Ada does not sleep in her room every night and her door is usually more open,
  so her room is a poor night-time baseline.
- **Heating system pressure leaks down slowly** (known small leaks, not yet found;
  Eero tops it up to ~2.0 bar on the boiler's manometer), ~0.07–0.09 bar a month all year
  (`sensor.vitodens_100_supply_pressure`, weekly means): ~2.0 in Dec 2025 → 1.5 by
  May, topped up to ~1.9 in mid-May, → 1.5 by Oct; topped up again 2026-10-25 from
  ~1.75 to 2.0 on the gauge (sensor 2.2 - sensor and gauge differ by ~±0.2). Nov 2025
  peaked at 3.4–3.6 on the sensor - worth knowing, as that is near the safety
  valve's usual 3 bar and a valve that has lifted can keep weeping.
  Suspects: safety valve weeping (check its drain), manifold or H-valve fittings,
  auto air vents, expansion vessel precharge. A top-up lasts ~6–8 months at this
  rate; bleed the radiators a day or two after one.
  Every top-up also brings in fresh, oxygen-rich water, which with steel radiators
  makes magnetite sludge - so the leak feeds the debris problem too (§1 "Debris"),
  and finding it is part of keeping the system clean.

**Floor heating** (Eero's "Floor flow Kodu 24" sheet, 2026-11-13), four rings, numbered
from the left at the manifold: **1 and 2 the living room** ("lounge" in the sheet;
2 × 13.7 m², ~91 m of 20 mm pipe each, 150 mm spacing; they **run all winter**), **3 the
downstairs bathroom** (6.9 m², ~46 m), **4 the upstairs bathroom** (2.9 m², ~19 m by
geometry; the flush measurement says ~35). The floor pipes downstairs are **old plastic** - most likely without an oxygen barrier, so oxygen diffuses
into the system water all the time and rusts the steel radiators: another source of the
magnetite in the valve inserts (§1 "Debris"), and one more reason for the magnetic
dirt separator. The sheet's flushed volumes are rough (the radiator rows include the
shared boiler stretch). Together the floors give roughly as much heat in winter as all
five radiators (`HEATING_CURVE_TEST.md` "Unexplained").

**Underfloor mixing unit** (read on site 2026-11-12): an Uponor Fluvia T
**PUSH-23-B-W** with its own Wilo pump. It serves **all the floor heating, rings 1-4**
(Eero, 2026-11-13; the 11-12 note "bathroom + WC only" was wrong): one mixed supply
temperature for every floor, so per-room floor control can only be the ring valves (manuals in
`~/Documents/Kodu 24/Juhendid-manuaalid/`, the operation pages are 18-20 of
`uponor-push-23b-shunt-med-wilo-pumpe_MAN.pdf`). Thermostatic head **5 = 38 °C** (scale
1-9 = 20-55 °C); floor flow read ~33 °C at 47 °C boiler flow. The valve beside the head
set **fully left = open** ("standard" mark; turning right closes, the 1-5 scale covers
only the last ~75° before closed). Wilo pump on **constant pressure (flat line), step
2**. It returns floor-return water only, so it lowers the boiler return - it is not a
hot bypass. Turn the valve down to 2-3 only if the floor runs too warm.

### Zigbee vs Matter / Thread

- **Matter is not a radio.** It runs over **Thread** (same 2.4 GHz 802.15.4 family
  as Zigbee, but a separate, incompatible stack) or Wi-Fi/Ethernet. Devices that do
  both natively are rare and not worth buying for.
- **One dedicated radio per protocol.** HA's Zigbee+Thread multiprotocol on one
  dongle is deprecated and unstable. One Zigbee dongle, one Thread dongle.
- **Interop happens at the hub:** HA can bridge Zigbee devices into Matter for
  Apple/Google Home — free, software only.
- **Meshes don't cross:** a Thread router does not route Zigbee. Matter/Thread
  won't help the Zigbee mesh; the router fix stays ZBMINIR2.
- **Here:** heating and sensors stay Zigbee (ZHA). Matter smoke detectors and
  lights → Matter-over-Thread, which needs a **Thread Border Router** (a second
  dongle, e.g. HA Connect ZBT in Thread mode, or an Apple/Google/Nest hub), on a
  2.4 GHz channel clear of Zigbee and Wi-Fi.
