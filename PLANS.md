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

### 1. Hydraulic balance — radiator lockshields

**Heating settings are frozen until this is done** (see `BETTER_THERMOSTAT.md`). The
week of data until then is the "before" picture.

**Why (2026-10-17/18):** all radiators share one pump and the lockshields are
fully open, never balanced. The radiator nearest the manifold gets the easiest
path and the most water, the farthest is starved. Exactly that pattern shows: the
master bedroom (nearest, plus heat from the en-suite floor) overshoots with its
valve nearly shut, the kitchen (farthest) only rises once the others close.
Without balance, the trims just hide the imbalance.

**The master bedroom has three heat sources besides its radiator:** it is nearest
the manifold (most flow), the en-suite floor loops warm it through the wall, and
**the manifold itself sits inside the master bedroom wall** — distribution pipes
give off heat whenever the system circulates, valve open or not. So the master
needs the most throttled lockshield and the smallest trim of any room, and will
never fully close its own heat off. If it still runs warm after balancing,
insulating the manifold cavity/pipes is the remaining lever (it also keeps that
heat for the rooms that need it).

**Order from the manifold:** master → Lola → Ada → kitchen (check the plans if
unsure).

1. **Before:** tell Claude — it sets all four TRV targets high for an hour (all
   valves open) and records how fast each radiator warms (the TRV's own reading
   rising is a rough flow proxy). Repeated after, so the effect is measured.
2. **Close each lockshield fully, counting turns** — that gives the range
   (typically 3–5 turns) and a way back. **Write the counts down below.**
3. **Starting point (turns open from closed):** master ~1 · Lola ~1.5 ·
   Ada ~2–2.5 · kitchen fully open.
4. **Fine-tune by temperature drop:** TRV fully open, IR thermometer on supply
   and return pipe. Aim for ~5–8 °C drop at 35–40 °C supply, about the same on
   each. Small drop (2–3 °C) = water rushing through → throttle; large drop =
   starved → open.
5. **After:** a day on the Küte dashboard's Diagnostika table, then the trims
   (master most likely down). One lever at a time.

**Measured turns:** master … · Lola … · Ada … · kitchen … (fill in on site).

**Every spring:** the summer fix is closing the lockshields — count the turns
when closing and reopen to the same count in autumn, or the balance is lost.

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

### 7. Sonoff TRVZB test (one on the shelf)

Try one on a well-linked radiator, standalone (own sensor + trim, like the
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
