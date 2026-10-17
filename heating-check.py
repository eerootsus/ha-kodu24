#!/usr/bin/env python3
"""Heating check: how well each room holds its setpoint, over a time window,
side by side with a fixed baseline - so the result is repeatable and comparable.

Why this exists: on 2026-10-17 the TRV trims (`regulation_setpoint_offset`) were
set and the workshop band raised to 17-19 C. "Is it better now?" needs the same
numbers computed the same way for before and after, not ad-hoc queries. Every
room/valve/offset/gas figure comes from HA long-term statistics (hourly, kept
indefinitely), so any past window can be recomputed exactly, any time.

Comparable, not just repeatable: outdoor weather swings too much for raw
numbers to compare week to week, so each window also reports its weather
(met.no mean and heating degree-days) and gas per degree-day. Room shortfall
vs setpoint is the main result - it is what the trims are meant to fix and is
fairly insensitive to weather once the valves have headroom.

met.no (`weather.forecast_kodu`) is used for weather rather than the Vitodens
sensor, which sits in the sun (see HEATING_CURVE_TEST.md). met.no history comes
from the recorder, not statistics, so it only reaches back recorder retention
(180 days): degree-days are blank for windows older than that.

Usage:
  ./heating-check.py                         baseline vs the last 7 days
  ./heating-check.py --from 2026-10-24 --to 2026-10-31
  ./heating-check.py --days 14               baseline vs the last 14 days

Same ssh transport as deploy.sh (HA_HOST / HA_PORT / HA_USER).
"""
import argparse
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Tallinn")

# The week before the 2026-10-17 tweaks: trims were written at 13:01 local, so
# the baseline stops at 13:00. Rooms ran 1.2-2.5 C under setpoint in it.
BASELINE = ("2026-10-10 00:00", "2026-10-17 13:00")

HDD_BASE = 17.0  # C; heating degree-day base

ROOMS = [  # (label, trv slug, room sensor or None)
    ("Ada", "ada", "sensor.climate_ada_s_room_temperature"),
    ("Master", "master", "sensor.climate_bedroom_temperature"),
    ("Lola", "lola", "sensor.climate_lola_s_room_temperature"),
    ("Kitchen", "kitchen", "sensor.climate_kitchen_temperature"),
    ("Stairwell", "stairwell", None),
]

HOST = os.environ.get("HA_HOST", "homeassistant.tail7c95c3.ts.net")
PORT = os.environ.get("HA_PORT", "22")
USER = os.environ.get("HA_USER", "root")
# One shared connection: the key lives in the 1Password agent, which prompts per
# signature (same reason as deploy.sh).
SSH = ["ssh", "-p", PORT, "-o", "ControlMaster=auto", "-o", "ControlPath=/tmp/ha-check-%C",
       "-o", "ControlPersist=60", f"{USER}@{HOST}"]
DB = "/config/home-assistant_v2.db"


def sql(query):
    out = subprocess.run(SSH + [f"sqlite3 -separator '|' {DB}"], input=query,
                         capture_output=True, text=True, check=True).stdout
    return [line.split("|") for line in out.splitlines() if line]


def ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=TZ).timestamp()


def stat_mean(entity, t0, t1, cond=""):
    """Hour-weighted mean of hourly means; also the share of hours matching cond."""
    rows = sql(f"""SELECT avg(st.mean), count(*) FROM statistics st
        JOIN statistics_meta m ON st.metadata_id = m.id
        WHERE m.statistic_id = '{entity}' AND st.start_ts >= {t0} AND st.start_ts < {t1}
        {cond};""")
    mean, n = rows[0] if rows else ("", "0")
    return (float(mean) if mean else None), int(n)


def stat_share(entity, t0, t1, cond):
    _, total = stat_mean(entity, t0, t1)
    _, hit = stat_mean(entity, t0, t1, f"AND {cond}")
    return hit / total if total else None


def stat_sum_delta(entity, t0, t1):
    """Consumption over the window from the statistics running sum."""
    q = lambda t: sql(f"""SELECT st.sum FROM statistics st JOIN statistics_meta m
        ON st.metadata_id = m.id WHERE m.statistic_id = '{entity}' AND st.start_ts < {t}
        ORDER BY st.start_ts DESC LIMIT 1;""")
    a, b = q(t0), q(t1)
    return float(b[0][0]) - float(a[0][0]) if a and b else None


def state_series(entity, t0, t1, expr="s.state"):
    """(ts, value) from the recorder, including the value in force at t0."""
    sel = f"""SELECT s.last_updated_ts, {expr} FROM states s
        JOIN states_meta sm ON s.metadata_id = sm.metadata_id
        LEFT JOIN state_attributes sa ON s.attributes_id = sa.attributes_id
        WHERE sm.entity_id = '{entity}'"""
    before = sql(f"{sel} AND s.last_updated_ts < {t0} ORDER BY 1 DESC LIMIT 1;")
    during = sql(f"{sel} AND s.last_updated_ts >= {t0} AND s.last_updated_ts < {t1} ORDER BY 1;")
    return [(max(float(t), t0), v) for t, v in before + during]


def time_weighted(series, t1):
    """Yield (value, seconds held) for a step series ending at t1."""
    for (t, v), nxt in zip(series, series[1:] + [(t1, None)]):
        yield v, nxt[0] - t


def weather(t0, t1):
    series = state_series("weather.forecast_kodu", t0, t1, "json_extract(sa.shared_attrs, '$.temperature')")
    held = [(float(v), dt) for v, dt in time_weighted(series, t1) if v not in ("", None)]
    secs = sum(dt for _, dt in held)
    if not held or secs < 0.5 * (t1 - t0):
        return None, None  # older than recorder retention
    mean = sum(v * dt for v, dt in held) / secs
    hdd = sum(max(0.0, HDD_BASE - v) * dt for v, dt in held) / 86400 * (t1 - t0) / secs
    return mean, hdd


def setpoints(slug, t0, t1):
    """Setpoint step series (ts, float). Unavailable/blank samples are skipped,
    so the last real setpoint carries over a restart."""
    return [(t, float(v)) for t, v in state_series(
        f"climate.trv_danfoss_{slug}", t0, t1, "json_extract(sa.shared_attrs, '$.temperature')")
        if v not in ("", None)]


def setpoint_label(series, t1):
    """The setpoint, or 'a/b!' if it changed during the window (ignoring blips < 1 h)."""
    total = {}
    for v, dt in time_weighted(series, t1):
        total[v] = total.get(v, 0) + dt
    held = sorted(v for v, secs in total.items() if secs > 3600)
    return held[0] if len(held) == 1 else (held or None)


def shortfall(room, sp_series, t0, t1):
    """Mean of (hourly room mean - setpoint in force that hour). Correct across
    setpoint changes, which a single 'room avg - setpoint' is not."""
    rows = sql(f"""SELECT st.start_ts, st.mean FROM statistics st JOIN statistics_meta m
        ON st.metadata_id = m.id WHERE m.statistic_id = '{room}'
        AND st.start_ts >= {t0} AND st.start_ts < {t1} AND st.mean IS NOT NULL;""")
    diffs = []
    for start, mean in rows:
        mid = float(start) + 1800
        sp = [v for t, v in sp_series if t <= mid]
        if sp:
            diffs.append(float(mean) - sp[-1])
    return sum(diffs) / len(diffs) if diffs else None


def last_state(entity, t1):
    rows = sql(f"""SELECT s.state FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id
        WHERE sm.entity_id = '{entity}' AND s.last_updated_ts < {t1}
        AND s.state NOT IN ('unavailable', 'unknown') ORDER BY s.last_updated_ts DESC LIMIT 1;""")
    return rows[0][0] if rows else None


def window(label, t0, t1):
    r = {"label": label, "t0": t0, "t1": t1, "rooms": {}}
    for name, slug, room in ROOMS:
        sps = setpoints(slug, t0, t1)
        r["rooms"][name] = {
            "sp": setpoint_label(sps, t1),
            "room": stat_mean(room, t0, t1)[0] if room else None,
            "short": shortfall(room, sps, t0, t1) if room else None,
            "demand": stat_mean(f"sensor.trv_danfoss_{slug}_pi_heating_demand", t0, t1)[0],
            "open50": stat_share(f"sensor.trv_danfoss_{slug}_pi_heating_demand", t0, t1, "st.mean >= 50"),
            "offset": stat_mean(f"sensor.trv_offset_{slug}_settled", t0, t1)[0] if room else None,
            "trim": last_state(f"number.trv_danfoss_{slug}_regulation_setpoint_offset", t1),
        }
    r["met_mean"], r["hdd"] = weather(t0, t1)
    r["gas"] = stat_sum_delta("sensor.vicare_heating_gas_consumption_current_day", t0, t1)
    r["supply"] = stat_mean("sensor.vicare_supply_temperature", t0, t1)[0]
    r["workshop"] = stat_mean("sensor.ikea_of_sweden_vindstyrka_temperature", t0, t1)[0]
    heat = sum(dt for v, dt in time_weighted(state_series("climate.workshop_hvac", t0, t1), t1) if v == "heat")
    r["ws_heat_h_day"] = heat / 3600 / ((t1 - t0) / 86400)
    return r


def f(v, fmt="{:.1f}", none="-"):
    if v is None:
        return none
    if isinstance(v, list):
        return "/".join(fmt.format(x) for x in v) + "!"
    return fmt.format(float(v))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--from", dest="frm", help="window start, 'YYYY-MM-DD[ HH:MM]' local")
    ap.add_argument("--to", help="window end (default now)")
    ap.add_argument("--days", type=int, default=7, help="window length if --from is omitted")
    a = ap.parse_args()
    norm = lambda s: s if " " in s else s + " 00:00"
    t1 = ts(norm(a.to)) if a.to else datetime.now(TZ).timestamp()
    t0 = ts(norm(a.frm)) if a.frm else t1 - a.days * 86400

    base = window("baseline", ts(BASELINE[0]), ts(BASELINE[1]))
    cur = window("window", t0, t1)
    span = lambda w: (f"{datetime.fromtimestamp(w['t0'], TZ):%Y-%m-%d %H:%M} -> "
                      f"{datetime.fromtimestamp(w['t1'], TZ):%Y-%m-%d %H:%M}")
    print(f"baseline  {span(base)}   (before the 2026-10-17 trims)")
    print(f"window    {span(cur)}\n")

    print("Room      setpoint        |  room avg     | vs setpoint   | valve demand  | open>=50%   | settled offset| trim")
    print("           base      now  |  base   now   |  base   now   |  base   now   |  base  now  |  base   now   | now")
    for name, *_ in ROOMS:
        b, c = base["rooms"][name], cur["rooms"][name]
        print(f"{name:9s} {f(b['sp']):>9s} {f(c['sp']):>6s}  | {f(b['room']):>5s} {f(c['room']):>5s}   |"
              f" {f(b['short'], '{:+.1f}'):>5s} {f(c['short'], '{:+.1f}'):>5s}   |"
              f" {f(b['demand'], '{:.0f}%'):>5s} {f(c['demand'], '{:.0f}%'):>5s}   |"
              f" {f(b['open50'], '{:.0%}'):>4s} {f(c['open50'], '{:.0%}'):>4s}   |"
              f" {f(b['offset'], '{:+.1f}'):>5s} {f(c['offset'], '{:+.1f}'):>5s}   | {f(c['trim'], '{:+.1f}')}")

    print("\nContext                      base      now")
    rows = [
        ("outside, met.no mean (C)", "met_mean", "{:.1f}"),
        (f"heating degree-days (base {HDD_BASE:.0f})", "hdd", "{:.1f}"),
        ("heating gas (m3)", "gas", "{:.1f}"),
        ("supply temp mean (C)", "supply", "{:.1f}"),
        ("workshop mean (C)", "workshop", "{:.1f}"),
        ("workshop HVAC heating (h/day)", "ws_heat_h_day", "{:.1f}"),
    ]
    for label, key, fmt in rows:
        print(f"  {label:28s} {f(base[key], fmt):>6s}  {f(cur[key], fmt):>6s}")
    per = lambda w: (w["gas"] / w["hdd"]) if w["gas"] is not None and w["hdd"] else None
    print(f"  {'gas per degree-day (m3)':28s} {f(per(base), '{:.2f}'):>6s}  {f(per(cur), '{:.2f}'):>6s}")
    print("\nSetpoint 'a/b!' = changed during the window; 'vs setpoint' still compares each")
    print("hour against the setpoint in force then.")
    print("Settled offset is '-' until the valve modulates near setpoint (offset.yaml).")
    print("Before 2026-10-17 13:00 its gate tested the ROOM against setpoint (since fixed),")
    print("so baseline settled offsets come from rare near-setpoint hours - indicative only.")
    print("Workshop heating is a separate split unit, not boiler gas; it adds heat")
    print("to the kitchen floor above, so the kitchen row is not a pure trim effect.")


if __name__ == "__main__":
    main()
