#!/usr/bin/env python3
"""Heating-curve model: what supply temperature each room needs, against the Viessmann
curve. Written 2026-11-13; reasoning and results in HEATING_CURVE_TEST.md
"Reference curve".

A room whose valve is 100 % open and holding steady is calibrated by one point: its
supply temperature, outside temperature and room temperature at that moment. From it
the model scales to other weather:

  radiator output ~ (supply - room) ** n        n = 1.26 (Atol C3 H500, ISAN catalogue)
  room heat loss  ~ (room - gains - outside)    gains = free heat in K (cooking, people,
                                                 sun); 2.5 K = heating from ~19 C
                                                 outside, as four winters of gas show

It assumes constant water flow through the radiator (its temperature drop scales with
load) and a linear heat loss; wind is whatever it was on the calibration night. No
absolute radiator rating or room area enters - only the exponent and the gains - so
the result does not depend on catalogue watts or on which space the radiator heats.

Re-calibrate from a new night with the kitchen valve at 100 % (`heating-check.py --duty`)
by changing CAL. Other rooms are scaled from their valve duty: holding target at a
fraction d of full output means needing (supply - room) * d ** (1/n) at full flow.
"""

N = 1.26
CAL = dict(flow=49.3, out=2.6, room=21.27)  # kitchen, night 2026-11-12/13, valve 100 %
GAINS = 2.5                                 # K; try 0 and 4.5 for the range
DUTY = {"Ada": (0.37, 21.39), "Lola": (0.46, 21.40), "Stairwell": (0.16, 21.42), "Master": (0.05, 21.46)}
TEMPS = [10, 5, 0, -5, -10, -15, -22]       # -22: design temperature, Tallinn area
CURVES = [("1.0/+6 (11-12)", 1.0, 6), ("1.2/+2", 1.2, 2), ("1.3/0", 1.3, 0),
          ("1.4/-2 (11-13)", 1.4, -2), ("factory 1.4/0", 1.4, 0)]


def vt(out, slope, shift, rt=22.0):
    """Viessmann flow set temperature; rt = the boiler's room setting. Matches the
    observed supply within ~1 K (11-11..11-13)."""
    dar = out - rt
    return rt + shift - slope * dar * (1.4347 + 0.021 * dar + 247.9e-6 * dar * dar)


def ab(cal=CAL, gains=GAINS):
    return (cal["room"] - gains - cal["out"]) / (cal["flow"] - cal["room"]) ** N


def flow_for(room, out, gains=GAINS):
    """Supply the kitchen needs, valve fully open, to hold `room`."""
    return room + ((room - gains - out) / ab(gains=gains)) ** (1 / N)


def settles(flow, out, gains=GAINS):
    """Where the kitchen settles, valve fully open, on a given supply."""
    lo, hi = out, flow
    for _ in range(60):
        m = (lo + hi) / 2
        if ab(gains=gains) * (flow - m) ** N > (m - gains - out):
            lo = m
        else:
            hi = m
    return m


def room_need(duty, room, out, target=21.5, gains=GAINS):
    f0 = room + (CAL["flow"] - room) * duty ** (1 / N)
    ratio = (target - gains - out) / (room - gains - CAL["out"])
    return target + (f0 - room) * max(ratio, 0) ** (1 / N)


def main():
    head = "outside".ljust(26) + "".join(f"{t:>7}" for t in TEMPS)
    print(f"free heat {GAINS} K; supply °C, and where the kitchen settles with its valve open\n")
    print(head)
    for name, s, sh in CURVES:
        print(name.ljust(26) + "".join(f"{vt(t, s, sh):7.0f}" for t in TEMPS))
        print("  kitchen settles".ljust(26) + "".join(f"{settles(vt(t, s, sh), t):7.1f}" for t in TEMPS))
    print()
    for target in (21.5, 21.0):
        print(f"kitchen needs for {target}".ljust(26) + "".join(f"{flow_for(target, t):7.0f}" for t in TEMPS))
    for room, (d, r) in DUTY.items():
        print(f"{room} needs (duty {d:.0%})".ljust(26) + "".join(f"{room_need(d, r, t):7.0f}" for t in TEMPS))
    print("\nnight: room setting 21 on 1.4/-2, kitchen settles".ljust(26))
    print("".ljust(26) + "".join(f"{settles(vt(t, 1.4, -2, 21), t):7.1f}" for t in TEMPS))


if __name__ == "__main__":
    main()
