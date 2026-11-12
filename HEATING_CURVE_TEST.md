# Heating curve test

Holds the Vitodens 100 heating curve, raises it only when the house proves it too
low, and records how cold each curve survived - so we know whether the top-floor
radiators can run at heat-pump flow temperatures, and the curve stays as low as
holds the house.

`curve-test/heating_curve_test.yaml` is a self-contained HA package.

> **Deployed switched off (2026-11-05).** `curve_test:` is in `configuration.yaml`
> and `deploy.sh`, but nothing acts until `script.curve_test_start` turns
> `input_boolean.curve_test_enabled` on. **Start it once Lola's TRVZB is on and the
> trims have settled** (`PLANS.md` §2–3): until then her stopgap target (22.5 on a
> maxed eTRV trim) and the 2026-11-05 trim changes would read as curve shortfalls.
>
> History: written 2026-08 to *descend* the slope from 1.2; not deployed on
> 2026-10-17, when alert-only (`trv-climate/heating_alerts.yaml`) was chosen while
> trims went in. Reworked 2026-11-05: rooms judged against their own TRV targets,
> all five rooms, ascend-only by default, raises the shift in mild weather and the
> slope in real cold within caps, heating weather from met.no, abort restores the
> curve it started from. The alert stays: the test only acts on the curve, and only
> once started.

## Curve in force

| Since | Slope | Shift | Why |
|---|---|---|---|
| years until 2026-08-13 | 1.2 | 0 | gas-boiler default |
| 2026-08-13 | 0.9 | 0 | start-low-and-raise plan |
| 2026-10-17 | 0.9 | +2 | kitchen and Ada fully open on ~33 °C supply at +12 °C outside |
| 2026-10-19 | 0.9 | +3 | second, colder night (7.8 → 2 °C): Ada fully open (98–100 %) on her door sensor and still slid 22.1 → 21.6; kitchen the same |
| 2026-11-10 20:18 | 0.9 | +4 | kitchen valve 95–96 % all day, radiator hot all over (Kätlyn), room still sliding 20.4 → 20.1 on a 21.5 target at 5.8 °C with S wind 4.8 m/s onto the south wall: the boiler, not the valve. Set from HA (`number.vitodens_100_heating_curve_shift`), read back from ViCare |
| 2026-11-10 22:42 | 0.9 | **+5** | HA room thermostat on since 21:53 with every valve open (eTRVs 92-100 %, stairwell 44 %), boiler modulation 11 → 19 % and radiator heads warming, but every room flat at 20.3-20.7 on 21.5 for 45 min with 3-4 °C and S wind; the burner short-cycled (3-10 min) at ~44 °C supply: the water temperature, not the valves, limits. Eero's call (raise now) |
| 2026-11-11 07:59 | **1.0** | +5 | first night under the HA room thermostat: Master, Lola, Ada, stair room reached 21.4-21.8 (Master and Lola valves shut by HA), but the kitchen stayed 20.5-20.6 on 21.5 with its valve at 100 % all night, flow ~45 °C, 1.7-3 °C outside, S wind 3-5 m/s. Shift at its +5 cap, so the slope: ~+2.2 °C flow at +2 °C outside. Eero's call |
| 2026-11-12 16:43 | 1.0 | **+6** | kitchen valve 100 % for 18 h (22:00 → 16:36) and still 21.05-21.20 on 21.5, the shortfall flat from 2.4 to 6.3 °C outside (the curve dropped flow 53 → 46 °C as it warmed) with S wind 3.8-6 m/s; the other four rooms held 21.3-21.5 cycling. A flat, wind-driven shortfall is a shift, not slope 1.1 (Viessmann's "1.1+" assumes shift 0; 1.0/+5 already matches 1.2/0 down to ~-5 °C, 1.1/+5 would exceed it everywhere). Shift past the curve test's +5 cap, set by hand. Watch Master's night overshoot. Eero's call |

Why the shift and not the slope: the Viessmann curve (`VT = RT + shift − slope ×
DAR × (1.4347 + 0.021·DAR + 247.9e-6·DAR²)`, `DAR = outside − RT`, RT = the boiler's
room setting, 22) reproduces the observed 33 °C at +12 °C outside. A slope step
mostly adds heat in deep cold (+0.1 → ~+1 °C at +12, ~+4 °C at −20), a shift step
adds the same everywhere. The shortfall was in mild weather, so +2 shift: 35 °C at
+12, 46 °C at 0, 61 °C at −20 — still ~11 °C under the old 1.2 curve in real cold.
At these low radiator temperatures +2 °C is worth roughly +25–30 % emitter output.

**Low and flat is also easier to balance** (Eero's observation, 2026-10-17: the old
steep curve may be why rooms felt unbalanced - "23 too hot, 22 too cold"). Hot water
crowds a radiator's whole output into the first few % of valve travel, so the TRV
over- and undershoots; cool water spreads it over a wider stroke. The eTRV's
sensor error also grows with radiator temperature (seen within an hour on
2026-10-17), so a steep curve makes every cold snap shift the trims. And 1.2/0 has
the wrong shape across the weather - short in mild weather, hot in a cold snap.
So the efficiency goal and the balancing goal point the same way: as low a slope
as holds the house, with shift covering the mild end.

## Why this matters

A heat pump's COP is set almost entirely by flow temperature. For the Panasonic
WH-MDC07J3E5 (7 kW air-to-water, on site):

| Flow | SCOP (cold climate) | Radiator circuit worth |
|------|--------------------|------------------------|
| W35  | 4.18               | — (underfloor only)    |
| W55  | 2.98               | ~344 €/yr saved vs gas |

The boiler ran **slope 1.2, shift 0** for years — a gas-boiler curve that pushes
flow into the 60s on a cold day. It was moved to **0.9** by hand in Aug 2026 and is
still there (`number.vitodens_100_heating_curve_slope`), so the ascend-only mode
below is the live plan and 1.2 is the historical baseline the savings are measured
against. Radiators sized for a boiler are commonly oversized
enough to run 10–15 K cooler. If 80 m² of top-floor radiators hold temperature at
45–50 °C instead of 60–65 °C, the radiator leg moves from SCOP ~3.0 toward ~3.8 —
roughly **another 150–200 €/yr**, for no hardware spend.

The test costs nothing and answers this before any plumbing is committed. Full
financial context: `Kodu 24/Heating economics.md` in the Obsidian vault.

**It also pays on gas alone.** Slope 1.2 was raised by hand, without a controlled
before/after, during the period of unreliable TRV control — so it may be compensating
for valves that never opened rather than for genuine heat demand. A condensing boiler
gains efficiency as return temperature falls; dropping flow from ~60 °C to ~50 °C is
worth roughly **3–5% of space-heating gas, about 50–90 €/yr**, whether or not the heat
pump is ever finished. If 1.2 was never justified, that has been leaking money for years.

## Preconditions — read before enabling

1. **The radiator master valves must be open.** They are closed for summer (between
   the boiler and the radiator manifold; see `PLANS.md` §1, "Every summer"). With the radiator feed shut the test
   measures nothing and will step the slope down unopposed to its floor. Enable only
   after reopening in autumn.
2. **Heating season.** The revert automation only evaluates below 12 °C outside;
   step-down does not check this, so starting in September wastes steps on mild
   weather. Start when the heating is genuinely working.
3. **All five rooms are watched**, each against its own TRV target - so the
   targets have to mean the room. Lola's 22.5 does not (stopgap on a maxed eTRV
   trim); her TRVZB fixes that, and adding `lola` to the package's `sonoff` list is
   part of fitting it.

   (Between some HA upgrade and 2026-09-13 *every* room was blind: `danfoss.py`, now `room_climate.py`,
   threw on each run and all ten sensors read `unavailable`. Fixed. Worth
   re-checking before enabling the test, because with every monitored room
   unavailable nothing can register a shortfall and the descent runs unopposed to
   `curve_test_min_slope`.)

## Design

**Pass/fail is room temperature only.** It deliberately ignores
`pi_heating_demand`, `heat_required` and every other TRV attribute:

- Externally-fed Danfoss eTRVs hold a residual ~1 % demand regardless of room
  temperature (`DANFOSS.md` §2.6), so demand cannot distinguish "needs heat" from
  "idle".
- The mesh is unreliable; TRV reads may be stale.
- The TRVs are being replaced by Sonoff TRVZBs (Ada 2026-10-26, Lola 2026-11-12; kitchen, Master and stairwell still eTRVs). Room
  sensors are brand-agnostic, so the test survives a valve swap; the diagnosis map
  reads a TRVZB's `hvac_action` instead of demand.

**Each room against its own TRV target.** Originally a fixed 21.0 for every room,
from when Better Thermostat was expected to move setpoints under the test. With the
trims in force the dial is meant to mean the room (`TRV_REGULATION.md`), so each
radiator room is judged against its own TRV target, like the shortfall alert. A
target at or below 10 °C (off / summer) drops the room out.
`input_number.curve_test_target_temp` is now only the living room's line (it has no
TRV); `curve_test_bathroom_target` is the bathrooms'.

**Raise on a shortfall, shift or slope.** If any radiator room sits more than
`curve_test_tolerance` (default 0.5 K) below its target for 90 continuous minutes
in heating weather (met.no air below 12 °C), or an underfloor room below its line,
the curve goes up one step: the **shift** +1 when met.no's air temperature is at or
above `curve_test_raise_slope_below` (default 0 °C), the **slope** +0.1 below it -
the same rule as the hand changes (§ "Curve in force"). Caps:
`curve_test_max_shift` (5) and `curve_test_max_slope` (1.2); at both, it only
pushes. One raise per episode - the room has to recover before the next.

**Descent is optional.** In descent mode (slope floor below the slope in force) the
slope also steps down 0.1 every `curve_test_step_days` (default 7) while nothing
fails, and a genuine failure latches `curve_test_floor_found` and stops it.

The raise automation **stays armed after the floor is found**. A slope validated in
November at −2 °C has not been tested at −15 °C; when that arrives, the curve is
pushed back up automatically. This is what makes it safe to leave running unattended.

### Confounders — why a failure is diagnosed, not just recorded

A cold room at a low slope has three possible causes, and they are **not**
distinguishable from room temperature alone:

| Cause | Signature | Verdict |
|---|---|---|
| Emitters can't deliver at this flow temp | valve calling (demand > 1 %), room still short | `curve` — genuine floor |
| TRV stuck shut / lost the command | demand ≤ 1 % while room is short | `trv_not_calling` — **inconclusive** |
| Mesh dropped the node | entity stale > 120 min, or unavailable | `trv_unreachable` — **inconclusive** |

`sensor.curve_test_failure_diagnosis` makes this call, and the revert automation
branches on it. On an inconclusive result the curve is still raised (comfort first) but
**no floor is latched** — instead `curve_test_inconclusive` pauses the descent until
cleared by hand. This matters specifically because the house's history is one of flaky
valves: without the discriminator, one stuck TRV would "prove" the radiators need slope
1.2 and the whole test would confirm the very assumption it exists to challenge.

Note the asymmetry in how `pi_heating_demand` is used. It is worthless as a *demand*
signal (residual 1 % floor on all externally-fed eTRVs), but a room sitting below target
while its PID reports ≤ 1 % is still diagnostic — a working PID would be calling hard.
It is used only in that direction.

**Coldest temperature per step is recorded.** `curve_test_best_validated_slope` and
`curve_test_best_validated_outside` are the honest result: "0.9 held, but only down to
−4 °C" is a very different claim from "0.9 held at −15 °C". Do not size a heat pump
off a slope validated in mild weather.

## Ascend-only mode (the default)

`script.curve_test_start` records the curve in force (for abort) and sets the slope
floor to the slope in force, so step-down fails its own condition and never fires.
What remains: hold, monitor, **raise on any sustained shortfall**, record how cold
it survived. Because the step never rolls over, `curve_test_step_min_outside`
accumulates the coldest temperature survived since the last raise, which *is* the
result: "0.9 / +3 held, coldest −11 °C." `input_text.curve_test_result` carries
failures in one readable line.

It fails toward comfort and never probes downward on data you cannot rely on. To
descend instead, lower `input_number.curve_test_min_slope` by hand after starting.

## Install and run

Deployed by `./deploy.sh` (`curve-test/` is in its manifest, `curve_test:` in
`configuration.yaml`). New helpers need a reload of `input_boolean`, `input_number`,
`input_datetime`, `input_text`, `template`, `automation` and `script` (or a restart).

- **Start:** `script.curve_test_start` - records the curve in force, sets the
  defaults (tolerance 0.5 K, caps 1.2 / +5, slope-below 0 °C, living room 21,
  bathrooms 22), ascend-only, and enables.
- **Abort:** `script.curve_test_abort` - disables and restores the recorded starting
  curve. If start never ran, it leaves the curve alone and says so (a never-set
  helper sits at its minimum, slope 0.2 / shift −13, which must never reach the
  boiler).
- **Pause without restoring:** turn `input_boolean.curve_test_enabled` off.

## Entities

| Entity | Purpose |
|---|---|
| `input_boolean.curve_test_enabled` | master switch (off until started) |
| `input_boolean.curve_test_floor_found` | latched once a shortfall occurred |
| `input_number.curve_test_target_temp` | living room line, default 21.0 °C |
| `input_number.curve_test_bathroom_target` | bathrooms' line, default 22.0 °C |
| `input_number.curve_test_tolerance` | allowed deficit, default 0.5 K |
| `input_number.curve_test_step_days` | dwell per step, default 7 |
| `input_number.curve_test_min_slope` | descent floor; start sets it to the slope in force (ascend-only) |
| `input_number.curve_test_max_slope` / `_max_shift` | raise caps, 1.2 / +5 |
| `input_number.curve_test_raise_slope_below` | met.no air below which a raise is slope, not shift (0 °C) |
| `input_number.curve_test_start_slope` / `_start_shift` | the curve abort restores |
| `input_number.curve_test_best_validated_slope` | **the result** |
| `input_number.curve_test_best_validated_outside` | how cold it was proven at |
| `sensor.curve_test_rooms` | the five radiator rooms: room, own target, deficit, demand entity |
| `sensor.curve_test_worst_deficit` | max shortfall across them |
| `sensor.curve_test_worst_room` | which room is failing |
| `sensor.curve_test_failure_diagnosis` | curve / trv_not_calling / trv_unreachable / underfloor / ok |
| `sensor.curve_test_status` | idle / holding (ascend-only) / stepping down / floor found / paused |

Notifications go to `notify.mobile_app_eeros_iphone_17`, threaded as `curve-test`:
a daily digest at 20:00 and an alert on each step change.

## Reading the result

`sensor.vicare_supply_temperature` and `sensor.vicare_outside_temperature` are both
numeric, so HA long-term statistics retain hourly means indefinitely — the actual
achieved curve can be plotted from history afterwards without extra logging. Recorder
retention is short, so use the statistics graph card, not the history panel.

**The outside sensor sits in the sun, and that is deliberate.** It faces roughly
south-east, like most of the windows, so on clear days it reads far above air
temperature (5 °C at night → 22 °C mid-morning on 2026-04-21; 25.9 °C on
2026-10-07). The weather compensation therefore drops the supply temperature exactly
when solar gain enters the main glazing — an accidental solar correction, kept on
purpose (decided 2026-10-17). Do not shade or move it without reason. The reason to
watch for: on a cold clear day, a TRV at ~100 % demand while its room falls below
setpoint, most likely in the morning (the sensor warms in minutes, the rooms in
hours) and in rooms facing away from the sun.

Measured against met.no (`weather.forecast_kodu`, a model, not a measurement) over
Apr–Oct 2026, Vitodens minus met.no: the sun bias peaks at **09:00** (mean +3.4 °C,
worst tenth +8 °C, max +16.5 °C), fades by ~16:00, and scales with cloud — clear
mornings +4.0 °C on average, overcast +1.7 °C. It is strongest in **April** (morning
mean +6.3 °C), +3.7 °C in May and only +1.2–1.8 °C June–October. The fall-off tracks
the **trees leafing out** in front of the sensor, so expect bare-branch winter
mornings with low south-east sun to look like April or stronger. Separately there is
a **night bias** of +0.4 °C in summer rising to +1.3–1.7 °C in the heated months —
most likely heat leaking from the wall behind the sensor, so all winter the boiler
sees a night ~1.5–2 °C milder than it is. Both are baked into whatever slope is
validated here.

For this test it matters less than it looks: `curve_test_step_min_outside` records the
*coldest* reading, which comes at night when the sensor is shaded, so "held down to
−11 °C" stays honest. Hourly-mean plots of outside vs supply are what get skewed —
read them from overcast days or nights.

The number that matters for the heat pump is flow temperature at design outdoor
temperature (Tallinn ≈ −22 °C, but −15 °C is a realistic worst tested case). Map the
validated slope to flow temp at that outdoor temperature, then read the COP off the
Panasonic table.

## Interaction with the planned split system

The 100 L tank is a **hydraulic separator, not thermal storage** — boiler, heat pump
and the heating circuits all stay independent, each pumping into or drawing from the
tank. Consequence: whichever generator is charging the tank must lift it to the
temperature the *highest-demand* circuit needs, and the Aquavec shunt mixes down for
the underfloor. So the curve test is really asking **"what tank temperature does the
radiator circuit need?"** — which is exactly the number that decides whether the heat
pump can serve radiators at all, or only the underfloor.

The summer problem recorded in `TRV_REGULATION.md` (radiators warm while the
underfloor runs) needs no decoupling after all: the radiator master valves between
boiler and manifold shut the radiator feed alone (`PLANS.md` §1, "Every summer").

## Sources

- Panasonic WH-MDC07J3E5 COP/SCOP — `Kodu 24/2022 Õhkvesi küte/Specification_Sheet_5051.pdf`
- Danfoss residual 1 % demand — `DANFOSS.md` §2.6, `TRV_REGULATION.md`
- Viessmann ViCare entities — `sensor.vicare_*`, `number.vitodens_100_*`
