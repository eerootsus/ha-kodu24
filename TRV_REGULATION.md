# TRV regulation: how each radiator valve controls its room

Since 2026-11-10 **HA's room thermostat** (`trv-climate/room_thermostat.yaml`) decides
every valve: from each room's door sensor against `input_number.room_target_<room>`
(kitchen 21.0 since 2026-11-13, the others 21.5) it sets the TRV to **32 (open)** or
**5 (shut)**. The TRVs' own regulation - internal sensor plus a per-room trim - is the
**fallback**, used when a room's sensor is silent for 20 min or the thermostat is
switched off. This file is the record of that: where control sits, the **trims in
force** for the fallback (the `input_number.trv_trim_<room>` helpers follow this table;
`trv-climate/trim_check.yaml` compares the devices against them), how to measure and
set a trim, the radiator presets, and the device baseline. `DANFOSS.md` is the eTRV
device reference.

**Design rule:** the one in force is `CLAUDE.md` "Control principle" (all logic in HA,
devices plain). It superseded the 2026-10-17 rule "automation advises, a human
adjusts", which came out of the Better Thermostat trial ("History: Better Thermostat"
at the end of this file - the one place that history is kept).

## Where control actually sits now

```
labelled room sensors ──► room_climate.py ──► sensor.climate_<area>_temperature
 (door sensor, weight 2;                                   │
  outer-wall Alts weight 0)                                ▼
         input_number.room_target_<room> ──► room_thermostat.yaml (every 5 min)
                                              room < target − 0.2 → setpoint 32 (open)
                                              room ≥ target       → setpoint 5  (shut)
                                                           │
                                                           ▼
                                                     TRV ──► valve

fallback (room sensor silent 20 min, or input_boolean.room_thermostat off):
TRV internal sensor + trim ──► TRV's own PID ──► valve      (setpoint = room target)
```

While the thermostat runs, the TRV's head reading and its trim decide nothing: at 32
the valve opens, at 5 it shuts. Why it was built (2026-11-10 21:30): Ada's TRVZB sat
0.5 K under its own target for 17 min and would not heat, and the Master, Lola and
stairwell valves were throttled with their rooms 1 K short while the kitchen ran flat
out - the heads, not the rooms, were deciding. Switched on at 21:53, all five valves
opened within 3 min.

The TRVs' own external-sensor inputs stay off: the eTRVs' feed is disabled
(`0x4015 = -8000`, left over from the BT preparation), the TRVZBs' external input is
switched off. So in fallback each TRV regulates on its internal sensor, which sits by
the radiator and reads warm. The static per-room trim corrects that - chosen
2026-10-17 over leaving the error alone or re-enabling the eTRV feed (which brings
back the summer 1 % floor, "Open issue" below).

### Trims in force (fallback only; current value in bold)

> **The trims live in HA helpers**, `input_number.trv_trim_<room>`
> (`trv-climate/trims.yaml`, since 2026-11-10), in "+ heats more" units for every room -
> a TRVZB's `local_temperature_offset` is minus its helper. Set a trim there and it is
> written to the device and read back; `trim_check.yaml` compares the devices against
> the helpers. Under the room thermostat they only matter in fallback; the automatic
> ±0.5 adjuster was removed 2026-11-12. This table stays the record of why.

> **Taking the head off resets the trim to 0 on the device** (found 2026-10-27):
> after the 2026-10-26 preset visit kitchen and master read `0x404B = 0` while HA
> still showed +2.0 / +1.5 - ZHA's number entity is a cache and only refreshes on a
> report or a read. Both rooms ran a night ~1 K short before it was spotted. Since
> 2026-11-05 `trv-climate/trim_check.yaml` reads every trim back from the device
> nightly and on remount signals and pushes a mismatch with its helper (it never
> rewrites). A one-off read by hand: websocket
> `zha/devices/clusters/attributes/value`, cluster `0x0201`, attribute `0x404B`,
> manufacturer `0x1246`, value in 0.1 K.

The goal is that the dial means the room. Set from the first cold fortnight, as each
room's shortfall below its setpoint. **The TRVZB rows (Ada, Lola) are the device's
`local_temperature_offset`, with the opposite sign to the helper:** −1.8 there does
what +1.8 does on an eTRV.

| Room | Trim | Room vs setpoint before | Note |
|---|---|---|---|
| Ada | eTRV +1.4 → +2.0; TRVZB offset −1.2 → −1.4 → −1.8 → −2.3 (wind) → **−2.8** (helper +2.8) | −1.2 … −1.4 | Sonoff TRVZB since **2026-10-26** (`climate.trv_sonoff_ada`, M30 thread, no adapter collar) - the eTRV's collar failed at the preset visit. Control accuracy **−0.2** (the default −1.0 band let the room sit ~1 K under). Her head's error over the room grows with cold (+0.3 → +1.2 K, 10-30 → 11-05), which is why the offset kept growing. ZHA truncates the offset to tenths: write −1.21 to get −1.2. Target 21.5. Step-by-step detail in git history. |
| Master | +1.5 → +2.2 → +2.0 → +1.5 → +1.0 → 0 → **+0.5** (wind) | −1.3 … −1.6 | +2.2 on 2026-10-17 16:03 (throttling 0.7 short). Back to +2.0 on 2026-10-18: held 22.0–22.6, i.e. a touch over. Tuning rule: err slightly under target, not over. Uncontrolled heat in: nearest the manifold, en-suite floor loops, heated rooms on three sides (the manifold inside its wall judged negligible, 2026-11-06) - expect it to need the smallest trim ("Radiator presets" below). 2026-10-19: 22.5–22.8 overnight with the valve at 6–7 % - uncontrolled heat dominates; 1.5 lets the valve close. Target 22 → 21 on 2026-10-21 (Kätlyn): settled in ~2 days to 21.2–21.6, i.e. 0.2–0.5 over and drifting down - steady, left alone. **2026-10-27: trim found reset to 0 after the preset visit, rewritten +1.5; target 21.5** (house felt chilly with 22 + no trim). **2026-11-05: +1.0** - on +1.5 / 21.5 it ran +0.6…+0.9 over from 10-30 to 11-03 with the valve at 2–8 %, back to ±0.3 only in the 11-04 cold. Read back from the device: `0x404B = 10`. **2026-11-06 08:27: → 0 for a test night**: if the room still holds ~22 on 21.5, its radiator is not what keeps it warm. **Kept at 0 (read 11-09):** four nights at +0.6 / +0.2 / +0.3 / 0.0 K over 21.5 (outside 5.8–7.5 °C), valve 3–6 % - its radiator is the reserve, not what keeps it warm. 11-09 by day −0.7, but the whole house ran 0.5–0.9 K cool that day with every valve throttled. |
| Lola | eTRV +2.0 → +2.5 (its cap); TRVZB **offset −2.5** (helper +2.5) | −1.8 … −2.2 | The warm pocket (headboard + curtains, two windows; "Warm pockets" below): her eTRV head read +3.4…+4.0 K over the room in the cold, past its 2.5 cap, and swung ~2 K with valve opening, so her dial ran 0.5-1 K above the room target to compensate; automatic offset mode (2026-10-18/19) did not help. Sonoff TRVZB fitted **2026-11-12** (`climate.trv_sonoff_lola`), under the room thermostat from 18:09 that day; control accuracy −0.2 (set 2026-11-17; it had been −1.0). **Passed 2026-11-17**: nights 21.35-21.46 on 21.5 (11-13 → 17) with the valve 24-50 % open at night - the test for replacing the other eTRVs (`PLANS.md` §3). Her head still reads ~28 while heating, which is why open is 32 (`room_thermostat.yaml` header). Step-by-step detail in git history. |
| Kitchen | +2.5 → +2.0 → **+1.5** | −2.1 … −2.5; TRV reads ~3 K warm | Still ~0.5 K short at best - **against the outer-wall sensor** (`TH01 Sonoff Kitchen Alt`), the only one until 2026-10-25. A door sensor (SNZB-02P, weight 2) was added then and the Alt went to weight 0; first reading door 21.9 vs Alt 20.5, so the shortfall above is overstated by ~1.4 K. Against the door sensor the TRV reads only ~1 K warm (22.4 vs 21.4), so +2.5 would aim the room at ~22.5 on a 21 target: trimmed to +2.0 on 2026-10-25 12:37. Its valve sat at ~95 % for days at the old 22 target: that was the trim making the TRV chase 24.5 on its own sensor, not starvation - the kitchen is a 9 m run, level with Lola ("Radiator presets" below). Next check: whether 21 holds on a cold night. **2026-10-27: trim found reset to 0 after the preset visit, rewritten +2.0; target 21.5.** **2026-11-05: +1.5** - +0.2…+0.5 over in the milder days 10-31..11-03; in the 11-04 cold it fell 0.1–0.4 short at 93–98 % valve, i.e. curve-limited, so a smaller trim costs nothing there. Read back: `0x404B = 15`. **2026-11-12: valve pin worked by hand on site** (the 11-09 "hot at 1 %" suspicion): moved freely and sprang back, so the insert is fine and a short kitchen is the curve and the wind. The remount reset the trim to 0 and lost the clock; +1.5 rewritten and read back, clock restored by `trv_clock_sync`. |
| Stairwell | 0 → −0.5 → **0** (wind) | no room sensor until 2026-10-25 | Sheltered, small outer wall; stable without it. Room sensor (SNZB-02P, weight 2) added 2026-10-25, first reading 23.7 - now in the Diagnostika table and the shortfall alert. **2026-11-05: −0.5** (read back `0x404B = −5`). The only TRV whose head reads **cold**: it sits in a draught, 0.3–1.1 K under the room. On 0 / target 21 the head held 21.0 with the valve at 2–4 % while the room ran +0.3…+1.1 over (most in the milder days 10-30..11-02): its heat is mostly downstairs heat rising up the stairwell, not its radiator. −0.5 lets the valve close; expect only a few tenths off, since the rest is not its radiator's. **Same day 16:25: target 21 → 21.5** (Eero, every room to 21.5). Night 11-05/06: 21.7 → 21.3 with the valve at 3 %, within 0.2 K of target |

**Wind trims, 2026-11-10 (kept).** For a south-wind spell onto the long south wall
the trims were raised: Master 0 → +0.5, stairwell −0.5 → 0, Ada's TRVZB offset
−1.8 → −2.3 (since −2.8). Kept: under the room thermostat the trims only act in
fallback, so putting them back would spend device writes for nothing. Revisit only if
a fallback lands a room over target.

**How the trims were found (2026-10-17 → 11-05), briefly.** A TRV head's error grows
with radiator output, so within an hour of the first trims it grew (Lola +2.0 → +3.2,
Master +1.5 → +2.4, kitchen +3.0 → +3.8) and they were raised the same afternoon. In
those first days the room reference became the door sensor alone (the outer-wall Alts went
to weight 0; rooms read 0.2-0.6 K warmer), so the earliest trims were sized against a
cold reference. Settings were frozen 2026-10-19 → 10-26 for the radiator balancing
("Radiator presets" below); what stands from the freeze: one lever at a time, ~2 days
to settle after a change. Curve changes over the same weeks are in
`HEATING_CURVE_TEST.md` "Curve in force"; night-by-night detail is in git history.

**Tuning rule (Eero, 2026-10-18): err slightly under, never over.** An overshoot
is what people notice, and the reflex is to turn the dial far lower than needed,
which then undershoots. So when a trim lands a room +0.3…+0.6 over, take it down
a step; a room 0.2–0.4 under is acceptable.

**Alert:** `trv-climate/heating_alerts.yaml` pushes when a room stays 0.5 K under its
room target for 3 h in heating weather, naming the cause from the setpoint HA left the
TRV on (open = the radiator is flat out, so the curve; shut = the thermostat or its
sensor; fallback = the sensor). Its header is the reference. Alert only.

**Check with `./heating-check.py`** (`--duty` for valve duty under the room thermostat,
see `CLAUDE.md` "Heating check") — the default report prints, per room, setpoint, room average,
shortfall vs setpoint (hour by hour against the setpoint in force), valve demand,
settled offset and trim, side by side with a fixed pre-trim baseline
(2026-10-10 → 2026-10-17 13:00), plus the window's weather (met.no degree-days)
and gas per degree-day so different weeks can be compared. Everything but the
weather comes from long-term statistics, so any window can be recomputed later.

**Warm pockets.** The kitchen looked like the worst case - its TRV boxed in between
a couch and the wall, the offset ~3 K for days - but most of that was its outer-wall
reference: against the door sensor (from 2026-10-25) its head reads only ~1–1.5 K
warm. **Lola's** is the real one (curtains + headboard): moving the furniture
(2026-10-25) cut her error 4.5 → 3.0 K, but in cold weather it is +3.4…+4.0 K, past
the eTRV's 2.5 K cap, and it swings ~2 K with valve opening. Covered mode
(`0x4016 = TRUE` + external feed) was used last winter but the house ran hot with
it, and automatic offset mode (§2.3) was tried on Lola 2026-10-18/19 without effect
(`trv-climate/room_feed.yaml`, deleted 2026-11-12, in git history). She has a TRVZB
since 2026-11-12, and under the room thermostat her head no longer decides - except
that it reaches ~28 while heating, so the open setpoint has to stay well above that.

Write gotcha: `number.set_value` with `1.4` landed as **1.3** (the value is sent in
0.1 K units and 1.4 × 10 truncates to 13). `1.41` gave 14. Read the entity back
after writing.

### Measuring the trim before setting it

`trv-climate/offset.yaml` (added 2026-09-13) publishes, per room:

    offset = TRV internal reading − true room temperature

A **positive** offset means the TRV reads warm, so its room settles that much
**colder** than the dial — and the same positive number is what to write as the
trim. Read it off `sensor.trv_offset_<room>_settled`, never the raw sibling: the raw
one is published all day including the many hours the valve is shut and the error is
~0, so its mean is pulled toward zero and understates the trim. The settled one only
publishes while the valve is modulating against a setpoint the room is near, which is
the equilibrium the trim has to be right for. Both feed long-term statistics; give it
a few genuinely cold weeks and read the mean off a statistics graph card
(`trv-climate/dashboard/offset_card.yaml`).

A TRVZB (Ada, Lola) applies its offset to the reading it reports, so its offset
sensors add it back to give the raw error, and the value to write there is **minus**
the settled number. The stairwell got its offset sensors on 2026-11-05 (room sensor since
2026-10-25); its head reads cold, so its offset is negative.

Nothing will appear until the heating actually runs — at summer setpoints the gate is
never open, which is correct, not broken. **While the room thermostat runs the gate
never opens either** (setpoints 32 / 5 are never near the room), so these sensors are
dormant; they matter again in fallback or with the thermostat off.

### Which of the two offset knobs to use

The eTRVs expose both, each ±2.5 K in 0.1 steps, and they reach the same place from
opposite directions:

| Entity | What it shifts | Effect |
|---|---|---|
| `number.trv_danfoss_<room>_regulation_setpoint_offset` (`0x404B`) | the PID's target, display unchanged | write **+offset**: the valve aims higher, the room lands on the displayed setpoint while the TRV keeps showing its own warm reading |
| `number.trv_danfoss_<room>_local_temperature_offset` | the sensor reading itself | write **−offset**: the TRV's reported temperature becomes the true room temperature, so setpoint and display both become honest |

**Tested 2026-10-17 — and the trim (`regulation_setpoint_offset`) is what is used.**
On Ada, `local_temperature_offset` = −1.4 with the setpoint offset at 0 kept the
valve calling (92–94 %), so the calibration *is* applied internally — but the eTRV
keeps **reporting its raw temperature** (attr `0x0000` stayed at ~23.2 °C with
`0x0010` = −14). So it does not make the display honest, which was the only reason
to prefer it; both knobs are equivalent for control and share the ±2.5 limit. Ada
was put back on the setpoint offset so all rooms use one knob. The original
reasoning, kept for the record:

~~**Use `local_temperature_offset`.**~~ It is the conceptually right one — this *is* a
sensor error, so correct the sensor and both the setpoint and the display become
honest. It was unavailable on Lola until 2026-09-13; it is now on all four rooms that
have an external sensor, under matching entity ids. Keep all four on the same knob so
they stay comparable.

`local_temperature_offset` is 0 on every eTRV; the trims in force are all
`regulation_setpoint_offset`. (The TRVZB is different: there `local_temperature_offset`
*is* the trim, and it does change the reported reading.)

## Radiator presets (balancing, 2026-10-26)

Moved here from `PLANS.md` §1 once done; the open steps (fine-tune by temperature
drop, the "after" re-run) stay there. Why: all radiators share one pump and nothing had
ever been balanced, so short runs and small radiators got more than they needed and
the trims were hiding the imbalance.

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
heat off. Confirmed by four nights on trim 0 (11-06 → 09, Master row above): its
radiator is the reserve, for real cold or the en-suite door shut.

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
the summer shut-off is the radiator master valves (`PLANS.md` §1 "Every summer").

So the balancing knob is the **presetting on the insert** (under the eTRV). Seen
2026-10-25 on one radiator: brass insert stamped **"OV"** (Oventrop's mark) plus a
type code (~"0637AT", "1181"), with a **black preset ring numbered around the pin**,
read against a nubbin on the brass body. Oventrop's inserts normally run **1–6,
6 = fully open** (also the factory setting); found at the visit mostly at 6 (see
"Presets before → after"). Still unknown: the exact insert's flow (kv) table, if the
type code can be read. The
ring turns by hand or with Oventrop's plastic key, eTRV off. The manifold is no
alternative: **plain ball valves only, all fully open** (2026-10-25).

**Before run** (`script.balancing_test`, 2026-10-25, label "before (4h cool)").
**Use `cool_minutes: 240`, `open_minutes: 90`**: a 60-min cool left the radiators
at 22-23 °C, so that run rose only 0.0-0.7 °C and compares nothing; the 4 h cool
brought all five to 20.3-20.7 °C. Outside 10.6 °C, supply 51.3 → 39.7 °C, rise on
each TRV's own sensor:

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

**Starting point** from the radiator table (flow: kitchen fully open, Ada and Lola about
half, master a bit below half for its extra heat, stairwell about a third) was kitchen
6 · Lola 5 · Ada 5 · master 4 · stairwell 3 on Oventrop's 1-6 scale (not linear, kv
table unknown). **Adjusted by the "before" run** (2026-10-25 21:24, 4 h cool / 90 min open; rise
on each TRV's own sensor): kitchen 2.4 · stairwell 2.5 · Ada 2.7 · master 3.0
(fastest start) · Lola 3.3 °C. The stairwell heated as slowly as the kitchen, so
it is not the over-fed room the table suggested (its never-fed valve may also
ramp slowly); Lola climbed most. Chosen: **kitchen 6 · Ada 5 · Lola 4 · master 4
· stairwell 4**.

**Presets before → after** (set 2026-10-26): kitchen 6 → 6 · master 6 → 4 ·
Lola 6 → 4 · Ada 6 → 5 · stairwell 5 → 4. Ada's ring was found a little past 6,
towards 1; the stairwell's at 5, not the factory 6.

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
late, not flow. Lola went *faster* despite 6 → 4 (freed pin? `PLANS.md` §1 "Debris"). Kitchen
is still the slowest by +60 and cannot open further, so any next step is throttling
the others (Lola, stairwell → 3), not the kitchen. Not acted on. The kitchen's pin was
exercised on site 2026-11-12 and moves freely (kitchen row above), and since 2026-11-10
the room thermostat holds every room at target whatever its share of flow, so further
throttling is only worth it if valve duty shows a room over-fed (`PLANS.md` §1).

## Per-room mapping

| Room | TRV climate entity | Room sensor (was BT's input) |
|------|---------------------|--------------------------|
| Ada | `climate.trv_sonoff_ada` (TRVZB) | `sensor.climate_ada_s_room_temperature` |
| Master/Bedroom | `climate.trv_danfoss_master` | `sensor.climate_bedroom_temperature` |
| Kitchen | `climate.trv_danfoss_kitchen` | `sensor.climate_kitchen_temperature` |
| Lola | `climate.trv_sonoff_lola` (TRVZB) | `sensor.climate_lola_s_room_temperature` |
| Stairwell | `climate.trv_danfoss_stairwell` | `sensor.climate_trepihall_temperature` (door sensor since 2026-10-25) |

## Firmware & config baseline (verified)

As of 2026-09-13, when all five were eTRVs. Ada's was replaced by a Sonoff TRVZB on
2026-10-26 (firmware `0x00001404`, no update offered as of 2026-11-05) and Lola's on
2026-11-12, so "all five" below means the eTRVs of the time; three remain (kitchen,
Master, stairwell), to be replaced by TRVZBs (`PLANS.md` §3).

- **Firmware is already uniform and current:** all five report
  `sw_version = 0x00000020`, and every `update.*_firmware` entity is `off`
  (installed == latest). **No OTA update is needed or available** — don't chase one.
- **The hardware really is identical — verified 2026-09-13, not assumed.** All five
  report `Danfoss` / `eTRV0103` / `sw 0x00000020`, and their Zigbee signatures are
  byte-identical: endpoint 1, profile 260, device type 769, in-clusters
  `0,1,3,10,32,513,516,2821`. No unit is a different model internally. So every
  difference below is ZHA-side.
- **But the entity sets are not identical:** Ada/Kitchen/Master expose 39, Lola 32,
  Stairwell 26. Two separate causes, and only the cosmetic one is harmless:
  - *Naming* — EN "prioritise" / EN "prioritize", Estonian on Stairwell
    (`valine_temperatuuriandur`, `kasuta_koormuse_tasakaalustamist`), and a
    `climate.<device>` vs `climate.<device>_thermostat` split. Captured at pairing
    from HA's language and from entity-id collisions. Cosmetic, but note it makes
    `switch.*_prioritise_*` un-templatable across devices.
  - *Missing features* — Lola has no `local_temperature_offset`; Stairwell lacks 13
    entities including both offsets. These are real gaps, not naming.

### The ZHA unsupported-attribute cache (investigated 2026-09-13)

ZHA caches attributes it believes a device does not support, in
`unsupported_attributes_v12` in `/config/zigbee.db`. Across five identical TRVs the
cache was inconsistent — `513/0x0010` (`LocalTemperatureCalibration`, the attribute
behind `local_temperature_offset`) was marked unsupported **on Lola alone**, plus
scattered singletons on Kitchen and Master. Identical firmware cannot genuinely
differ that way; it is the signature of attribute reads timing out during interview
and being recorded as unsupported. Lola was at `rssi −93` when she was interviewed.

It is also self-sealing: zigpy short-circuits attributes it believes unsupported, so
`zha.set_zigbee_cluster_attribute` on `0x0010` never reaches the radio. The cache can
only be cleared in the database.

**Done, and it worked — in two steps, both needed.**

1. With core stopped and the DB backed up to `/config/zigbee.db.bak-20260913`, the 10
   rows that were not unanimous across the five were deleted. All five now carry an
   identical 13 rows. **This alone changed nothing** — the entity stayed missing
   across a restart, which ruled out the cache being the whole story.
2. A **Reconfigure** on Lola (Settings → Devices & Services → ZHA → device →
   Reconfigure) then brought six entities back: 32 → 38. `0x0010` was *not* re-marked
   unsupported, confirming the read succeeded this time.

Both steps were necessary and neither was sufficient. ZHA discovers these config
entities at **device interview**, not at startup, so an already-initialised device
keeps whatever entity set it was paired under — which is why restarts never helped.
But a reconfigure alone would have re-read `0x0010`, found it in the unsupported
cache, and skipped it. Clear the cache *then* reconfigure.

Lola now has `local_temperature_offset` like the other three. Still missing:
`sensor:timestamp` (the eTRV clock readout, 38 vs 39) — harmless, nothing uses it.

**Entity IDs come back in HA's instance language.** The instance runs `language: et`,
so the six new entities were created as
`number.lola_s_room_trv_danfoss_lola_kohalik_temperatuuri_nihe` and similar, while the
older ones carry English slugs from when they were paired. Display names were already
uniform — `friendly_name` is translated at runtime, so *every* TRV shows Estonian —
but the ids were not, which breaks templating across devices. They were renamed back
to the `trv_danfoss_<room>_<feature>` pattern over the websocket API
(`config/entity_registry/update`; there is no REST equivalent). **Expect to redo this
after any future reconfigure.**

**Stairwell got the same treatment** and went 26 → 39, so four of the five now expose
an identical entity set. It had no unique unsupported-cache rows, so the reconfigure
alone was what it needed.

### Where the five ended up (2026-09-13)

All five were reconfigured and the ids normalised. Counts 39 / 39 / 38 / 39 / 39,
**38 of 39 features common to all**, every id on the `trv_danfoss_<room>_<feature>`
pattern, and no Estonian slugs anywhere. The single remaining difference:

- `sensor:timestamp` missing on Lola. Accepted as an open gap — see below.

Settled along the way, and worth not re-litigating:

- `climate.trv_danfoss_<room>_thermostat_N` on Kitchen/Master/Stairwell were dedup
  artefacts from earlier re-pairings. Renamed to the bare `climate.trv_danfoss_<room>`
  that Ada and Lola already used. **`trv-climate/offset.yaml`, the curve-test package
  and this file were updated to match** — anything new referencing a TRV climate
  entity should use the bare form.
- `prioritise` vs `prioritize` was a British/American split captured at pairing.
  Settled on `prioritize`, the spelling three of the five already carried.

### Known gap: Lola has no `timestamp` sensor (accepted 2026-09-13)

> **Moot since 2026-11-05:** ZHA no longer provides this sensor on *any* eTRV - on
> kitchen, master and stairwell it was only a restored registry entry, `unavailable`
> with no real value in recorder history. Those three were disabled (not deleted,
> so a future ZHA that brings it back finds them). Nothing uses it.

The one feature not on all five. **Do not re-investigate from scratch** — this is what
was already ruled out.

The entity is `sensor.trv_danfoss_<room>_timestamp`, `entity_category: diagnostic`,
unique_id `<ieee>-1-513-setpoint_change_source_timestamp`. It reads Thermostat cluster
`0x0032` **SetpointChangeSourceTimestamp** (decimal 50) — when the setpoint last
changed. Its siblings are `0x0030` SetpointChangeSource and `0x0031`
SetpointChangeAmount.

`0x0032` was one of the three attributes uniquely marked unsupported on Lola in ZHA's
cache, alongside `0x0010` (calibration) and `0x0001`, all from her bad interview at
`rssi −93`. All three rows were deleted together. `0x0010` came back on the next
reconfigure; `0x0032` did not, across **two** reconfigures.

Checked and ruled out — after the reconfigures there is no recorded difference between
Lola and the other four:

| Check | Lola | Other four |
|---|---|---|
| `0x0032` in `unsupported_attributes_v12` | no (stayed deleted) | no |
| `0x0032` in `attributes_cache_v12` | absent | **also absent** |
| `0x0030` cached | `0` | `0` or `2` |
| Time cluster `0x000A` in `in_clusters` | present | present |
| anything marked unsupported on cluster 10 | none | none |
| entry in `deleted_entities` for that unique_id | none | — |
| any registry entry anywhere holding that unique_id | none | — |
| duplicate / deleted device record for her ieee | none, exactly one | — |

So nothing in the ZHA databases or the HA registries explains it. A read that *times
out* does not populate the unsupported cache the way an explicit
`UNSUPPORTED_ATTRIBUTE` response does, which was the working theory — but two
reconfigures leaving no trace at all weakens it. More likely ZHA is not attempting that
read for her, for a reason not visible in inspectable state.

**Why it was dropped rather than fixed.** Nothing in this repo reads it; it is a
diagnostic. It reports against the eTRV's internal clock, which this project stopped
syncing when `set_time` was removed, so its timestamps would be against an unsynced
clock anyway. The remaining routes are a re-pair — costing her entity ids, recorder
history and the `sensor_weight_X` device labels, then another renaming pass — or
reading ZHA's discovery source for the exact condition that gates this sensor. Neither
is worth it for one diagnostic entity.

**If it ever matters,** the next thing to try is reading `0x0032` directly during a
known wake window and watching whether ZHA logs a failure, since that is the one
observation missing. There is no read service; use the websocket or
`trv_debug.py`, which already dumps raw attributes.

### Language: two separate settings

Entity **IDs** are slugged from the translated name at creation, using the *instance*
language (`Settings → System → General`), which was `et`. Entity **display** names are
translated at runtime, and each user's *profile* language controls what they see —
Eero's was already `en-GB`, which is why the UI looked English while new entities were
being created with Estonian ids.

The instance language is now `en-GB`. **It did not take effect immediately**: Stairwell
was reconfigured after the change and still produced Estonian ids, because HA caches
translations at load. After a restart the display names did flip to English
(`'TRV Danfoss Ada Local temperature offset'`, `'... Battery'`), which is the proxy for
translations having reloaded.

**Still unproven for ids, though.** Reconfiguring all five after the restart created no
new entities — they already had their full sets — so nothing was slugged and the fix
was never exercised. Check the first entity the next reconfigure produces rather than
assuming; if it comes out Estonian, the instance language is not the slug source and
this section is wrong.

A cosmetic leftover: `switch.trv_danfoss_<room>_prioritize_external_temperature_sensor`
now displays as "Prioritise" — en-GB in the translated name, US spelling in the id that
was settled on. Ids are what matter for templating, so this was left alone.

## Open issue: radiator TRVs stuck at 1 % (summer warmth)

Four radiator TRVs (ada, master, kitchen, lola) held `pi_heating_demand = 1 %` and
the radiators stayed warm in summer 2026 (Ada's eTRV has since been replaced by a
TRVZB, Lola's on 2026-11-12; a TRVZB drives its valve directly and should close fully); only **stairwell** idles at 0 %. Because the
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

**Chosen resolution:** physically shut the radiator feed for summer — bulletproof,
independent of TRV/mesh. Since 2026-10-25 that means the **radiator master valves**
between the boiler and the radiator manifold (`PLANS.md` §1, "Every summer"): one
place, and the bathroom underfloor keeps running. Accepted trade-off: no radiator
can be turned on for a cold summer night until they are reopened.

**If the mesh is improved later:** re-deploy `trv_debug.py` (attribute dump) and
`trv_unstick.py` (cycle covered + setpoint nudge), re-run on the reliable network,
and confirm writes land via fresh read-back before trusting any result.

## History: Better Thermostat (trialled and dropped 2026-09-13)

This file was `BETTER_THERMOSTAT.md` until 2026-11-05.

**Outcome (2026-09-13): Better Thermostat was installed, trialled and removed.** It
offered nothing meaningful over the eTRVs' own control, so the integration is gone
and there is no `climate.*_better_thermostat` entity.

**The real reason, in Eero's words (2026-10-17):** it "seemed like another
obfuscation layer on top of everything, making balancing even harder". With BT,
the curve, the external feeds and the TRVs' own logic all in play, a cold room had
too many suspects. Everything was reset to a plain baseline instead (curve 0.9, no
external feeds, TRVs on their own sensors), and the 2026-10-17 "automation advises"
rule came out of it (superseded 2026-11-10 by `CLAUDE.md` "Control principle"). What follows is why it was tried and what was changed on the
TRVs for it; the device changes that are still in force are described above.

### What we were trying to fix

The Danfoss eTRV's **native external room sensor** feature gives accurate
room-based control but holds an anticipatory ~1 % valve opening that never fully
closes (see `DANFOSS.md` — the PID floor, observed year-round on every
externally-fed TRV; only the one TRV *without* an external sensor idles at 0 %).
With this firmware you cannot have both accurate external-sensor control **and** a
fully-closing valve. The plan was to hand control to **Better Thermostat (BT)** and
use each eTRV as a calibrated actuator instead.

### Target architecture that was planned (not built)

```
weighted room sensors (danfoss.py)  ──►  Better Thermostat (per room)  ──►  eTRV
sensor.climate_<area>_temperature        target temp + calibration            (actuator)
                                          outdoor threshold (summer off)
```

- **danfoss.py (now `room_climate.py`) was made sensor-aggregation only:** `update_room_climate_sensors`
  publishes the weighted `sensor.climate_<area>_temperature` (BT's per-room input)
  plus its helpers. **All TRV writes were removed** (time sync, radiator-covered,
  load-balancing, external-sensor feed, retry queue) so it cannot fight BT.
- **eTRV native external sensor is turned OFF** so it doesn't fight BT:
  `prioritize external temperature sensor = off` and external sensor = `-8000`
  (done on all TRVs).

### Setup steps (not to be followed — kept for what they changed on the devices)

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

`danfoss.py` (renamed `room_climate.py` 2026-11-05) was trimmed to sensor-aggregation only for this plan. That trimming
stands — it writes nothing to the TRVs. Room-based control came back as a separate HA
package instead, `trv-climate/room_thermostat.yaml` (2026-11-10); see "Where control
actually sits now" above.

### Status — 2026-09-13

- **Better Thermostat: installed, trialled, removed.** It offered nothing meaningful
  over the eTRVs' own control. `/config/custom_components/` holds only `hacs` and
  `pyscript`; no BT entity exists. Not a regression — a decision.
- **Room sensors: working again.** They had been dead for some time — `danfoss.py`
  threw on every run after an HA change to the device registry (fixed 2026-09-13).
  Four rooms report; Stairwell is `unavailable` because it has no labelled external
  sensor, which is correct rather than broken.
- **TRVs: running on their own internal sensors**, setpoints set by hand. Four still
  sit at `pi_heating_demand = 1` and Stairwell at 0.

## Sources
- Danfoss Ally PID quirks / unstick (cycle radiator_covered + setpoint) — https://github.com/Koenkk/zigbee2mqtt/discussions/19495
- Better Thermostat docs — https://better-thermostat.org/configuration
- Danfoss Ally external-sensor calibration writeup — https://ha-praksis.dk/en/case-calibrating-danfoss-ally-with-external-temperature-sensors/
- Danfoss Ally firmware archive (v1.28/v1.20/v1.18/v1.08), ZHA/deCONZ/Z2M —
  https://community.home-assistant.io/t/danfoss-ally-thermostat-firmware-archive-v1-28-v1-20-v1-18-v1-08-specifications-zha-deconz-zigbee2mqtt/261951
