# Heating curve test

Finds the lowest Vitodens 100 heating-curve slope that still holds the house, so we
know whether the top-floor radiators can run at heat-pump flow temperatures.

`curve-test/heating_curve_test.yaml` is a self-contained HA package.

> **Not deployed — alert-only chosen instead (2026-10-17).** With per-room trims in
> force and every room meant to hit its *own* target, a shortfall can be the curve,
> the trim or the valve, and an automatic raise would blur which. Eero raises the
> slope by hand; `trv-climate/heating_alerts.yaml` pushes an alert that names the
> likely cause from the valve opening (>= 80 % = curve). Before ever enabling this
> package: its start script defends a fixed 21.0 °C, checks the living room against
> that same line, still lists Lola as unmonitored (her sensors work now), gates on
> the sunlit Vitodens sensor, and `curve_test_abort` restores 1.2, not today's 0.9.

## Curve in force

| Since | Slope | Shift | Why |
|---|---|---|---|
| years until 2026-08-13 | 1.2 | 0 | gas-boiler default |
| 2026-08-13 | 0.9 | 0 | start-low-and-raise plan |
| 2026-10-17 | 0.9 | **+2** | kitchen and Ada fully open on ~33 °C supply at +12 °C outside |

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

1. **The radiator lockshields must be open.** They are physically closed for summer
   (see `BETTER_THERMOSTAT.md`, summer fix). With the radiator feed shut the test
   measures nothing and will step the slope down unopposed to its floor. Enable only
   after reopening in autumn.
2. **Heating season.** The revert automation only evaluates below 12 °C outside;
   step-down does not check this, so starting in September wastes steps on mild
   weather. Start when the heating is genuinely working.
3. **Blind zones — one now, not two.** Lola's room has since been fitted with two
   labelled sensors (`TH01 Sonoff Lola` and `Lola Alt`, both `sensor_weight_2`), so
   only **Stairwell/Trepihall** has no external sensor and stays unmonitored. It is
   also the one TRV that idles correctly, which makes it the least urgent gap.

   (Between some HA upgrade and 2026-09-13 *every* room was blind: `danfoss.py`
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
- The TRVs are candidates for replacement (Sonoff TRVZB). Room sensors are
  brand-agnostic, so the test survives a valve swap.

**Target is a fixed number, not a TRV setpoint.** This was written when Better
Thermostat was expected to move setpoints and apply calibration offsets. BT was
dropped, but the reasoning holds for the eTRVs' own setpoints too:
`input_number.curve_test_target_temp` (default 21.0 °C) is the comfort line being
defended, independent of whatever any valve is currently aiming at.

**Optimistic descent, automatic recovery.** Step down 0.1 every
`curve_test_step_days` (default 7). If any monitored room sits more than
`curve_test_tolerance` (default 0.5 K) below target for 90 continuous minutes in
heating weather, step back up, latch `curve_test_floor_found`, and stop descending.

The revert automation **stays armed after the floor is found**. A slope validated in
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

## Ascend-only mode (start low, raise if needed)

The slope was set to **0.9** manually in Aug 2026 on a start-low-and-raise plan. To run
that instead of descending, set `curve_test_min_slope` to the current slope (0.9):
step-down then fails its own condition and never fires. What remains is the half that
matters for this strategy — hold, monitor, **raise 0.1 on any sustained shortfall**,
record how cold it survived.

Because the step never rolls over in this mode, `curve_test_step_min_outside`
accumulates the coldest temperature the slope has survived since starting, which *is*
the result: "0.9 held, coldest −11 °C." `input_text.curve_test_result` carries the same
in one readable line.

Ascend-only is the better choice if the valves are not yet trustworthy: it fails toward
comfort, and never probes downward on data you cannot rely on.

## Install

```
config/
└── curve-test/
    └── heating_curve_test.yaml
```

```yaml
homeassistant:
  packages:
    curve_test: !include curve-test/heating_curve_test.yaml
```

Restart HA, then run `script.curve_test_start` (sets defaults, stamps the step, and
enables). `script.curve_test_abort` disables the test and restores slope **1.2** —
note that is the old gas-boiler curve, not the 0.9 the boiler runs today, so an
abort *raises* the slope. Check the hard-coded value in
`curve-test/heating_curve_test.yaml` before relying on it.

## Entities

| Entity | Purpose |
|---|---|
| `input_boolean.curve_test_enabled` | master switch |
| `input_boolean.curve_test_floor_found` | latched once a shortfall occurred |
| `input_number.curve_test_target_temp` | comfort line, default 21.0 °C |
| `input_number.curve_test_tolerance` | allowed deficit, default 0.5 K |
| `input_number.curve_test_step_days` | dwell per step, default 7 |
| `input_number.curve_test_min_slope` | descent floor, default 0.6 |
| `input_number.curve_test_best_validated_slope` | **the result** |
| `input_number.curve_test_best_validated_outside` | how cold it was proven at |
| `sensor.curve_test_worst_deficit` | max shortfall across monitored rooms |
| `sensor.curve_test_worst_room` | which room is failing |
| `sensor.curve_test_blind_zones` | advisory TRV temps for Lola / Trepihall |
| `sensor.curve_test_status` | idle / stepping / floor found |

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

Decoupling also fixes the summer problem recorded in `BETTER_THERMOSTAT.md`: once the
radiator circuit is independent, the bathroom underfloor loops can run from the tank
without keeping the radiator loop hot, and the lockshield workaround becomes
unnecessary.

## Sources

- Panasonic WH-MDC07J3E5 COP/SCOP — `Kodu 24/2022 Õhkvesi küte/Specification_Sheet_5051.pdf`
- Danfoss residual 1 % demand — `DANFOSS.md` §2.6, `BETTER_THERMOSTAT.md`
- Viessmann ViCare entities — `sensor.vicare_*`, `number.vitodens_100_*`
