# Kodu 24 — open work and plans

The repo is the source of truth for the Kodu 24 smart home. This file holds what
is *not built yet*: installs waiting for a visit, HA work waiting for an evening,
and the background those need. What is built is documented where it lives
(`README.md` for the map, `CLAUDE.md` for how things work, `BETTER_THERMOSTAT.md`
for TRV control, `HEATING_CURVE_TEST.md` for the boiler curve).

The Obsidian vault (`Projects/Smart home.md`) only carries next-action lines for
the personal TODO and points here. Do not grow a second copy there.

When something here gets done, move its outcome into the doc of the thing it
built and delete it from this file.

---

## Next visit to Kodu 24

### 1. Hydraulic balance — radiator valve presets

**Heating settings are frozen until this is done** (see `BETTER_THERMOSTAT.md`). The
week of data until then is the "before" picture.

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

**The master bedroom has three heat sources besides its radiator:** it is the
shortest run (most flow), the en-suite floor loops warm it through the wall, and
**the manifold itself sits inside the master bedroom wall** — distribution pipes
give off heat whenever the system circulates, valve open or not. So the master
needs throttling beyond what its size suggests and the smallest trim of any room,
and will never fully close its own heat off. If it still runs warm after
balancing, insulating the manifold cavity/pipes is the remaining lever (it also
keeps that heat for the rooms that need it).

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

**Watching until ~2026-11-02**, then decide. Idea first: the **kitchen may be
partly blocked** like Lola seemed to be - its ring was never turned (left at 6),
only its H-valve, which hissed. Exercise it: eTRV off, ring 6 → 1 → 6 a few times
(the full stroke flushes the gap), then back on (clock re-sync is automatic). It
ends at the same preset, so it is a cleaning step rather than a balance change - do
it early so the week's data includes it. If the kitchen then keeps up, the presets
may already be close; if not, throttle Lola and the stairwell to 3.

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

### 2. Kitchen trim against the door sensor

The door sensor is in (2026-10-25, weight 2; the Alt is weight 0) and reads ~1.4 K
above the outer-wall Alt the +2.5 trim was sized against. First correction taken
2026-10-25: +2.5 → +2.0 (`BETTER_THERMOSTAT.md` "Trims in force"). After §1:
confirm the trim against the door sensor, and only then decide whether the curve
needs another shift step.

### 3. Lola's room

- **Curtains and headboard away from the TRV.** It is boxed in: on the fixed +2.5
  trim it overshoots in morning sun, and the Danfoss automatic-offset room feed
  (`trv-climate/room_feed.yaml`, parked 2026-10-19) did not help - the valve sat at
  ~30 % whatever the room did. Free the TRV first; if the trim then holds in sun
  and on cold nights, done.
- **If not: the Sonoff TRVZB on her radiator** (doubles as §7's test). Regulating
  on her door sensor as an external temperature, it sidesteps the pocket; it also
  closes fully (no summer 1 % hold). Check before relying on it: which TRVZB
  external-sensor settings ZHA exposes (Zigbee2MQTT supports them fully), and which
  adapter her valve body needs (look at the one under the Danfoss). Do it **after**
  the balancing, one lever at a time. Danfoss covered mode (`0x4016` = TRUE) is the
  software-only alternative.
- **Sensor swap check:** hold one of her TH01s in a hand for a minute and watch
  which Diagnostika column (Andur / Alt) jumps. If the door one shows as Alt, swap
  the two device names in HA. Suspected since the 2026-09-12 battery change.
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
- **Dead corner** (rssi −100).

**Why downstairs matters:** the laundry leak sensor hangs off the living-room
floor lamp (an IKEA bulb) at LQI 47 — a safety device on a weak link that dies when
the lamp is switched off at the wall. After installing: `./zigbee-topology.sh
--save`, a day later `--diff`. If the leak sensor has not moved, power-cycle the
floor lamp once (end devices never pick a new parent on their own).

**Avoid as routers:** Tuya (flaky), Aqara (poor router), bulbs (poor, and can be
switched off).

### 5. Batteries

Last ones not yet replaced. As of 2026-10-17: bathroom leak sensor 23 %
(safety device — first), stairwell TRV 29 %, master TRV 35 %.

### 6. Kitchen lamps as routers

Add the kitchen Zigbee switch **wired so the TRÅDFRI bulbs stay always powered**
(decoupled smart-bulb mode — the switch sends Zigbee commands, never cuts power),
or dumb bulbs + an always-live ZBMINIR2. Switched-off bulbs are dead routers.

### 7. Sonoff TRVZB test - fitted on Ada, 2026-10-26

**Fitted on Ada's radiator 2026-10-26** (`climate.trv_sonoff_ada`, target 21, local
offset 0): her eTRV's adapter collar gave trouble at the preset visit and its
adaptation run never completed; the TRVZB threads straight onto the Oventrop M30
insert. The eTRV was removed from ZHA. Ada missed the "after" balancing run for it.
Still to do: find its trim (`number.trv_sonoff_ada_local_temperature_offset` -
negative = reads lower = heats more; the Küte table shows minus it as Trimm), check
which external-sensor settings ZHA exposes, update its firmware.

Originally: try one on a well-linked radiator, standalone (own sensor + trim, like the
Danfosses — Better Thermostat is gone). Direct valve control: closes properly, no
Danfoss summer 1 % hold, maintained firmware. Don't set its "closing degree"
parameter (breaks hvac_action); watch for calibration drift. Alternative:
Eurotronic Spirit Zigbee. Avoid Tuya/Aqara TRVs.

---

## HA work (no visit needed)

- **Immich backup-silence sensor** — "no new assets for 14 days". The initial sync
  finished 2026-09-03 (~11k photos), so the baseline exists. A phone backup can stop
  silently; belongs with `backup-monitor/`.
- **Bathroom fan on humidity** (after its relay is in): trigger on a fast rise
  (e.g. +8 points in 10 min = shower) or on being ~15 points above a reference room,
  off when back within a few points; minimum and maximum run time. Not a fixed %:
  the downstairs bathroom averages ~58 % in October and peaks at 92 %. **Before
  sizing a mechanical extract:** check no open-flue appliance shares the old
  chimney (backdraught). The Vitodens is room-sealed.
- **Underfloor zone control** — not eTRVs: solenoid valves on an **ESP32 relay
  board** (WiFi, likely ESPHome), **normally open** (no power = heat, so every
  failure fails warm). Relay ON = zone CLOSED: expose a "zone open" switch with the
  relay inverted so the UI never shows on for closed; boot with all relays off;
  check the valves' continuous-duty rating (powered while held closed); the logic
  must never close every zone (pump). Floors are slow: wide band, long minimum
  on/off times (30–60 min). Bathroom loops must stay on year-round. Logic in HA,
  in this repo. **Physical install first, then the logic** — record which relay
  drives which zone and room while wiring.
- **Condensation-risk check** from the outer-wall Alt sensors: room dew point vs
  Alt temperature (Lola's Alt read 4.8 °C below her door sensor through January
  2026).
- **Better light automations.**
- **Matter lights + extra downstairs lighting, Matter smoke detectors** — on a
  separate Thread mesh (see below).

---

## Background

### House

- Naturally ventilated: inlets in rooms, under-door gaps, extract via the old
  chimney (stack effect, little wind effect measured). Hallway extracts are an
  option; they would work by stack effect — high, into a warm flue — and one grille
  per flue.
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
