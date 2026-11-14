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

**Presets set 2026-10-26** (below), which ended the settings freeze
(`TRV_REGULATION.md`). Still open here: step 4 (fine-tune by temperature drop)
and the kitchen decision under "Watching".

**Why (2026-10-17/18):** all radiators share one pump and nothing has ever been
balanced. Water takes the easiest path: short runs and small radiators get more
than they need, long runs to big radiators get less. The master bedroom (shortest
run, plus heat from the en-suite floor) overshoots with its valve nearly shut.
Without balance, the trims just hide the imbalance.

**The radiators** (installer's spec; runs are Eero's one-way estimate, 2026-10-25):

| Room | Area | Radiator (Atol C3, H500) | Sections | Run from manifold |
|---|---|---|---|---|
| Kitchen | 20 m² | L1058 | 23 | 9 m |
| Master | 16 m² | L874 | 19 | 3 m |
| Lola | 10 m² | L552 | 12 | 9 m |
| Ada | 9.5 m² | L506 | 11 | 11 m |
| Stairwell | 8 m² | L460 | 10 | 4 m |

Each needs flow roughly in proportion to its sections (same model and height).
With everything open, flow falls with run length. Put together, **the kitchen gets
the least water for its size** - the biggest radiator on a long run, about half
what Ada and Lola get per section and a third of the stairwell's (crude: counts
pipe resistance only, which overstates the spread). Ada is the farthest run but
has a small radiator, so she is not the starved one.

The kitchen's *apparent* shortfall was still mostly its cold outer-wall sensor:
on the door sensor (from 2026-10-25) it sits about on target, and its valve at
~95 % for days was the +2.5 trim making the TRV chase target + 2.5, not a measure
of flow. But it is the room most likely to fall short in real cold, and the
reason is its size, not distance.

**The master bedroom has heat its radiator does not control:** it is the
shortest run (most flow), the en-suite floor loops warm it through the wall, and
it is **surrounded by heated rooms on three sides**, so it loses little heat to
begin with. The manifold also sits inside its wall, but Eero judges that effect
negligible (2026-11-06). So the master needs throttling beyond what its size
suggests and the smallest trim of any room, and will never fully close its own
heat off.

Seen on the night of 11-05/06 (target 21.5, trim +1.0): the room held 22.0–22.2 all night as
outside fell 8.9 → 6.1 °C, with the valve at 5–6 % and the head only +0.3…+0.7 K
over the room (Lola's, actually heating, reads +3…+4). The radiator was all but shut,
so the ~0.6 K over is the heat it does not control, as on 10-19 (+0.5…+0.8 at 6–7 %)
and after 10-21 (+0.2…+0.5): about the same overshoot at every target. The trim
plays a small part: +1.0 aims the head at 22.5, which it read, so the TRV kept a
little flow; +0.4 would match its real error and let it close fully, worth a couple
of tenths at most.
**Test:** a night on trim 0 (set 11-06 08:27) - if the room still holds ~22, the radiator is irrelevant
and the only lever left is the curve (supply ~40 °C that night vs ~35 in the
baseline week), which every room shares. Turning the en-suite loop down is **not an
option for now** (Eero, 2026-11-06), and the neighbours are structural, so expect
~0.5 K over in Master until then. In effect the Master radiator is the **reserve**:
for when the en-suite door is closed (no floor-loop heat in) or in real cold; at
~6 °C outside the room does not need it. Unverified below ~3.5 °C (11-04, still
over at 2–8 %), and the door's state is not tracked, so a cold night with the door
shut is the case to watch.
**Result (read 11-09): trim 0 kept.** It ran four nights rather than one, and the room held
the target without its radiator: night mean +0.6 / +0.2 / +0.3 / 0.0 K on 21.5 (outside
5.8–7.5 °C), valve 3–6 % throughout. On 11-09 the whole house ran 0.5–0.9 K cool with
every valve throttled (Master −0.7 by day); every room shared the dip, so it is not
Master's trim. Raise it again only on a cold night or with the en-suite door shut.

**Where to balance:** bottom-connected radiators ("altühendusega") with a
**built-in valve insert** - the eTRV sits on it - and a **Honeywell 1/2" straight
H-valve** underneath, fed by 16 mm pipe (Kermi eurocones) on its own run from the
manifold.

The H-valve is a **quarter-turn ball shut-off with no presetting** (confirmed
2026-10-25 against Danfoss's similar RLV-KB instruction, filed as
`~/Documents/Kodu 24/Juhendid-manuaalid/Danfoss RLV-KB H-valve (similar to installed Honeywell).pdf`): screwdriver
slot *along* the pipe = open, *across* = closed. It has no end stops - hence
"it just rotates" - and is not meant to sit part-open. **All five set fully open
2026-10-25.** Older docs here say "lockshield"; there is no separate lockshield -
the summer shut-off is the radiator master valves (below).

So the balancing knob is the **presetting on the insert** (under the eTRV). Seen
2026-10-25 on one radiator: brass insert stamped **"OV"** (Oventrop's mark) plus a
type code (~"0637AT", "1181"), with a **black preset ring numbered around the pin**,
read against a nubbin on the brass body. Oventrop's inserts normally run **1–6,
6 = fully open** (also the factory setting). **It sits at 6** (confirmed
2026-10-25) - unbalanced, as expected. Assume the other four are at 6 too until
seen. Still open: the exact insert's flow (kv) table, if the type code can be read. The
ring turns by hand or with Oventrop's plastic key, eTRV off. The manifold is no
alternative: **plain ball valves only, all fully open** (2026-10-25).

1. **Before:** run `script.balancing_test` with label "before" (~2 h, unattended:
   every valve shut for an hour so all start cold, then fully open for an hour
   while each TRV's reading is sampled; targets restored after, push with the
   result). See `trv-climate/balancing_test.yaml`.
   **Done 2026-10-25, but use `cool_minutes: 240`, `open_minutes: 90`.** A 60-min
   cool left the radiators at 22-23 °C (barely below where they started), so that
   run rose only 0.0-0.7 °C and compares nothing. The 4 h cool brought all five
   to 20.3-20.7 °C. Baseline "before (4h cool)", outside 10.6 °C, supply
   51.3 → 39.7 °C:

   | Room      | +15 min | +30 min | +90 min | valve |
   |-----------|---------|---------|---------|-------|
   | Master    | 1.7     | 2.5     | 3.0     | 97 %  |
   | Ada       | 1.2     | 2.1     | 2.7     | 99 %  |
   | Lola      | 1.3     | 2.1     | 3.3     | 100 % |
   | Stairwell | 1.2     | 1.7     | 2.5     | 45 %  |
   | Kitchen   | 0.9     | 1.5     | 2.3     | 100 % |

   The +30 column is the one to compare; after it the curves flatten. Master
   fastest and kitchen slowest, as the table above predicts. The stairwell eTRV
   never opened past 45 % even at a 28 °C target (its slow ramp, see the 1 %
   investigation), yet kept pace with the fully open kitchen - so its share of
   flow is generous, consistent with throttling it most.
2. **Write down each insert's current preset** before touching it - that is the
   way back.
3. **Starting point, from the table above** (flow: kitchen fully open · Ada and
   Lola about half · master a bit below half, for its extra heat · stairwell about
   a third). On a 1–6 Oventrop scale, roughly: **kitchen 6 · Lola 5 · Ada 5 ·
   master 4 · stairwell 3**. Approximate - the scale is not linear and the exact
   kv table is unknown.
   **Adjusted by the "before" run** (2026-10-25 21:24, 4 h cool / 90 min open; rise
   on each TRV's own sensor): kitchen 2.4 · stairwell 2.5 · Ada 2.7 · master 3.0
   (fastest start) · Lola 3.3 °C. The stairwell heated as slowly as the kitchen, so
   it is not the over-fed room the table suggested (its never-fed valve may also
   ramp slowly); Lola climbed most. Chosen: **kitchen 6 · Ada 5 · Lola 4 · master 4
   · stairwell 4**.
4. **Fine-tune by temperature drop:** TRV fully open, IR thermometer on supply
   and return pipe. Aim for ~5–8 °C drop at 35–40 °C supply, about the same on
   each. Small drop (2–3 °C) = water rushing through → throttle; large drop =
   starved → open. This decides; step 3 only gets close.
5. **After:** run `script.balancing_test` again (label "after", same 240/90 and a
   similar outside temperature); the result sensor
   keeps the previous run beside it. Then ~2 days on the Küte dashboard's
   Diagnostika table, then the trims (master most likely down). One lever at a time.

**"After presets" run** (2026-10-26 18:43 open, 4 h cool / 90 min open, outside
10.2 °C, supply mean 39.5 °C but cycling 33–64.5; Ada left out - her TRV was being
swapped). Rise on each TRV's own sensor, after vs before:

| Room      | +15        | +30        | +60        | start |
|-----------|------------|------------|------------|-------|
| Master    | 0.0 (1.7)  | 1.2 (2.5)  | 2.9 (2.8)  | 20.6  |
| Lola      | 1.6 (1.3)  | 2.5 (2.1)  | 2.9 (2.9)  | 21.2  |
| Stairwell | 1.0 (1.2)  | 1.8 (1.7)  | 2.8 (2.2)  | 20.4  |
| Kitchen   | 1.3 (0.9)  | 1.6 (1.5)  | 2.1 (2.3)  | 20.1  |

Read: master's early slope collapsed (fastest → slowest at +30) but it caught up by
+60, so it still gets plenty once warm - part of the delay may be its valve opening
late, not flow. Lola went *faster* despite 6 → 4 (freed pin? see "Debris"). Kitchen
is still the slowest by +60 and cannot open further, so any next step is throttling
the others (Lola, stairwell → 3), not the kitchen. Not acted on: first ~2 days of
daily behaviour on the Küte table, one lever at a time.

**Watching until ~2026-11-02**, then decide - **overdue as of 2026-11-05.** Evidence
so far: in the 11-04 cold (~3.5–4.5 °C outside) the kitchen fell 0.1–0.4 short of
21.5 at 93–98 % valve - still the room the flow limits - while master and the
stairwell ran over with valves at 2–8 % (both trimmed down 2026-11-05). Idea first: the **kitchen may be
partly blocked** like Lola seemed to be - its ring was never turned (left at 6),
only its H-valve, which hissed. Exercise it: eTRV off, ring 6 → 1 → 6 a few times
(the full stroke flushes the gap), then back on (clock re-sync is automatic). It
ends at the same preset, so it is a cleaning step rather than a balance change. If
the kitchen then keeps up, the presets may already be close; if not, throttle the
stairwell to 3 (Lola waits for her TRVZB - throttling her now would starve a room
already short on a maxed trim).

**Presets before → after** (set 2026-10-26): kitchen 6 → 6 · master 6 → 4 ·
Lola 6 → 4 · Ada 6 → 5 · stairwell 5 → 4. Ada's ring was found a little past 6,
towards 1; the stairwell's at 5, not the factory 6.

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
setting. Lola's jump in the "after" run (6 → 4 yet faster than "before") may be a pin
freed by the visit rather than a flow change - judge her on the next days, not that run.

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

The rest of this section is the history that led there.

**2026-11-10 22:42: shift +4 → +5** (all valves open under the HA room thermostat,
rooms flat 45 min, burner short-cycling at ~44 °C). **Done 2026-11-10 20:18: shift +3 → +4** (Eero; set from HA, `HEATING_CURVE_TEST.md`
"Curve in force"). The kitchen ran 95-96 % open with the radiator hot all over and
still slid to 20.1 (its valve pin was worked on 2026-11-12 and moves freely). Check it the evening of 11-11 against the wind (S wind
forecast through 11-12). The rest of this section is the reasoning that led here.

**Checked 2026-11-11 21:00 (`heating-check --duty`):** the other four rooms hold
21.3-21.4 against 21.5 with valves cycling (Master 12-19 % open, the rest 33-57 %).
The kitchen ran 100 % open from 21:00 to 18:00 in only 3-3.5 m/s onto the S wall
(out 1.6-2.7 °C), crept 20.5 → 21.2, was 21.0 at 21:00 (66 % open after 18:00) -
short in mild wind, so not the accepted storm case. Gas 0.42 m³/degree-day for the
day (0.37 over 3 days; baseline 0.38, rooms ~0.8 K warmer now). **Decision (Eero):
hold +5 overnight; if the kitchen is still short on 11-12 morning at moderate wind,
shift +5 → +6**, and watch Master's night overshoot (21.66 with its valve shut,
03:00-06:00 on 11-11).

**Checked 2026-11-12 16:36 → shift +6 at 16:43:** the kitchen ran 100 % open from
22:00 on and sat 21.05-21.20, flat from 2.4 to 6.3 °C outside in S wind 3.8-6 m/s, so
the condition above held. Slope 1.1 (Viessmann's figure) was considered and rejected:
that figure assumes shift 0, and the shortfall does not grow with cold
(`HEATING_CURVE_TEST.md` "Curve in force"). Master again reached 21.69-21.72 at
04:00-08:00 with its valve shut - **check it and the kitchen on the morning of 11-13.**
Lola's 22:21-22:45 dip on 11-11 (21.76 → 20.45) was an airing: RH fell ~10 points on
both her sensors at once and recovered after the window closed.

The kitchen trim is settled against its door sensor: +2.5 → +2.0 (2026-10-25) →
+1.5 (2026-11-05, `TRV_REGULATION.md` "Trims in force"). What is left is flow,
not trim: in the 11-04 cold it ran 0.1–0.4 short at 93–98 % valve. After §1's
kitchen step, decide whether the curve (0.9 / +3 since 2026-10-19) needs shift +4 -
the shift, not the slope (`HEATING_CURVE_TEST.md`). (The automatic curve test was removed
2026-11-12; the curve is set by hand from valve duty.)

### 3. Lola's room

- **TRVZB fitted 2026-11-12** (outcome and settings: `TRV_REGULATION.md` "Trims in
  force", Lola row; procedure: `CLAUDE.md` "Swapping an eTRV for a TRVZB"). HA's room
  thermostat drives it 28 / 5 from the door sensor.
- **Pass mark - Lola is the test for the other eTRVs** (Eero, 2026-11-10): nights within
  ±0.3 K of target over the next ~3 nights (`heating-check --duty`), against −1.0…−1.8 on
  her eTRV. If she passes, kitchen, Master and stairwell get TRVZBs too - the kitchen
  first. Under the room thermostat the eTRVs already behave as plain valves, so the case
  for the TRVZBs is now that they close fully in summer and carry no hidden logic.
  Watch whether preset 4 costs her: valve flat out and room below ~21 at night = back
  to 5-6.
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

### 4. Zigbee routers — ZBMINIR2 (on the shelf since 2026-08-23)

In-wall relays behind a switch; real routers (~64 children). ⚠️ Need a
**neutral** in the box; **R2, not L2** — the no-neutral L2 does not route.

- **Lola's room — done 2026-09-13**, carries 5 (Lola + Ada TRVs and sensors,
  links 175–255). See `topology/2026-10-17_1701.txt`.
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
  Fix: hotter water (the curve, +6 since 2026-11-12) or more emitter.
- **The Vitodens pump runs faster than needed.** Turning it down means fewer starts, a
  cooler return and better condensing.

**To do: buy two SNZB-02P** (Eero, 2026-11-11; borrowing the outer-wall Alts was
dropped - they stay for the condensation alerts) and strap them to the **flow and
return pipes at the boiler** under a bit of pipe insulation. No `sensor_weight_`
label, so they are not counted as room sensors. Log a normal day and a cold,
all-valves-open evening:

- ΔT **< ~5 K with all valves open** → the pump: lower the Vitodens pump speed.
- ΔT **10-15 K** → the radiators take what they can; only hotter water helps.

Then add flow/return/ΔT to `./heating-check.py` and the Küte view.

---

## HA work (no visit needed)

- **Wind compensation.** *Update 2026-11-11:* the room layer is now HA's room
  thermostat (`room_thermostat.yaml`, on since 2026-11-10 21:53), which supersedes the
  trim adjuster (removed 2026-11-12): it opens a valve whenever its
  room is short, so the wind on the room side is handled by feedback, no wind model.
  What wind now costs shows as **valve duty**, `./heating-check.py --duty`. The test
  is the S/SSE spell 11-11 → 11-12 (2-5 °C, overcast, wind ~3 → 6-7 m/s): expected
  duty rising most in Lola (SE corner onto the open end of the street) and least in
  Master/Ada; the kitchen, open throughout, shows the boiler's limit. First morning
  (11-11 07-11, ~3 m/s onto S): Master 0-25 %, Ada/Lola/stair 40-60 %, kitchen 100 %
  rising to 21.0 after slope 0.9 → 1.0. Still open: an automatic curve step for rooms
  whose valve is flat out (by hand today; Eero accepts the kitchen short in high wind,
  CLAUDE.md), and a forecast step if the feedback proves too slow. Original note follows.
  **Originally: after the valves respond as expected (§3; the kitchen pin, checked free 2026-11-12), not before.**
  Eero's working theory (2026-11-10): wind on the **south wall** - the longest outer
  wall (Master, stair room, Lola) - cools the whole flat, and more so now the leaves
  are down. Seen so far: 11-09 (SW, 3.8 m/s onto S) and 11-10 (S, 4.8 m/s onto S,
  5.8 °C) every room ran 0.8-1.1 K short with the valves mostly shut, Master furthest;
  11-05 (NW, 7.6 m/s but all of it onto W) the flat held. Not yet separable from the
  kitchen valve fault (from 11-09 03:10) and the heads reading warm - Ada was short on
  11-10 too with no wind on her wall. `./heating-check.py` reports wind onto each wall.
  Options, to weigh once the TRVs behave:
  - **Trims by wind** (Eero's idea): raise each south-wall room's trim with the wind
    onto that wall. Limits: the eTRV trim caps at ±2.5 K, and every write costs a
    sleepy device a wake-up - step it (e.g. 0 / +0.5 / +1.0), with hysteresis, at most
    a few writes a day.
  - **Let the room sensor see it - Eero's choice (2026-11-10), together with a
    TRVZB on every radiator:** more control, every room the same, no opaque "smart"
    logic in the TRV. A TRVZB on its external-temperature input
    (`trv-climate/lola_feed.yaml` on branch `lola-trvzb`) regulates on the door sensor,
    which feels the wind's cooling directly - no wind model needed. If Lola's TRVZB
    passes and the eTRVs are replaced, this may make wind trims unnecessary.
  - **House-wide:** a curve-shift bump on a strong S/SW forecast. Coarser; it heats
    every room, including the ones the wind does not reach.
  First, collect the evidence: a cold S/SW day against a cold NW or calm one, with
  working valves.
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
- **Floor circuit flow/return** after the Uponor PUSH-23: two SNZB-02P strapped to the
  pipes under insulation, like §8's at the boiler (buy four at once). Gives the floor
  ΔT and, with §8, the floor's share of the boiler's heat.
- **Room temperatures exist already:** living room `sensor.th_living_room_temperature`
  (rings 1-2; "lounge" in the flow sheet is the same room), downstairs bathroom
  `sensor.tz2000_a476raq2_ts0201_temperature` ("TH downstairs bathroom", ring 3),
  upstairs bathroom `sensor.th_upstairs_bathroom_temperature_2` (ring 4).
  **All three are Tuya TS0201 (`_TZ2000_a476raq2`, the ones with a screen) and report
  far too rarely to control a floor on:** on 2026-11-14 the living room had changed once
  in 33 h and the downstairs bathroom not at all in a day, though all three were alive
  on the mesh. Replace them with SNZB-02P like the kitchen and stairwell door sensors,
  bought together with the pipe sensors above (seven in all), before any floor logic.
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
    and has only the one outer wall.
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
