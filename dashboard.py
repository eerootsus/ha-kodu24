#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["websockets", "pyyaml"]
# ///
"""Keep a storage-mode dashboard view and its YAML record in this repo in step.

Why this exists: both dashboards are storage mode (see CLAUDE.md "Dashboards"),
so HA owns the live copy in /config/.storage and the YAML under */dashboard/ is
only a record - which drifts the moment anyone edits in the UI. This replaces
the one-off scripts used to build the Küte view on 2026-10-17 with the
supported route: the websocket API (lovelace/config/load + save), which applies
live with no restart and touches ONLY the named view.

Usage:
  ./dashboard.py check heating     diff live view vs record (exit 1 if they differ)
  ./dashboard.py apply heating     push the record live; shows the diff, asks first
  ./dashboard.py pull heating      overwrite the record with the live view (after
                                   UI edits), keeping the record's header comment

Edit the record, `check`, then `apply`. If `check` shows changes you did not
make, someone edited in the UI - `pull` first, or they are lost on `apply`.

Connection: HA over the tailnet (same reasoning as deploy.sh), HA_URL to
override. Token: $HA_TOKEN, else `op read $HA_TOKEN_REF`, else the op:// ref in
the gitignored .claude/rules/local.md - so no secret ever lands in the repo.
Needs `websockets` and `pyyaml` (`uv run dashboard.py ...` installs them).
"""
import argparse
import asyncio
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import websockets
    import yaml
except ImportError:
    sys.exit("needs websockets + pyyaml: `uv run dashboard.py ...` or `pip install websockets pyyaml`")

ROOT = Path(__file__).resolve().parent
HA_URL = os.environ.get("HA_URL", "http://homeassistant.tail7c95c3.ts.net:8123")

# view path -> (dashboard url_path, None = the default "lovelace" one; record file)
VIEWS = {
    "heating": (None, "trv-climate/dashboard/heating_view.yaml"),
}


def token():
    if os.environ.get("HA_TOKEN"):
        return os.environ["HA_TOKEN"]
    ref = os.environ.get("HA_TOKEN_REF")
    if not ref:
        local = ROOT / ".claude/rules/local.md"
        m = re.search(r'op://[^"\s`]+', local.read_text()) if local.exists() else None
        ref = m.group(0) if m else None
    if not ref:
        sys.exit("no token: set HA_TOKEN or HA_TOKEN_REF (a 1Password op:// reference)")
    out = subprocess.run(["op", "read", ref], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"op read failed: {out.stderr.strip()}")
    return out.stdout.strip()


class HA:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def call(self, **msg):
        self.n += 1
        msg["id"] = self.n
        await self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get("id") == self.n:
                if not r.get("success"):
                    sys.exit(f"HA refused {msg['type']}: {r.get('error')}")
                return r.get("result")


async def connect():
    url = HA_URL.replace("http", "ws", 1).rstrip("/") + "/api/websocket"
    # Token first: HA drops an unauthenticated socket after ~10 s, and op read can
    # sit longer than that waiting for the 1Password approval.
    tok = token()
    ws = await websockets.connect(url, max_size=None)
    await ws.recv()
    await ws.send(json.dumps({"type": "auth", "access_token": tok}))
    if json.loads(await ws.recv()).get("type") != "auth_ok":
        sys.exit("HA rejected the token")
    return ws


def dump(view):
    return yaml.safe_dump(view, allow_unicode=True, sort_keys=False, width=100)


def read_record(path):
    text = path.read_text()
    return yaml.safe_load(text), text


def header(text):
    """The leading comment block of a record, which `pull` keeps."""
    lines = []
    for line in text.splitlines(keepends=True):
        if line.startswith("#") or (lines and not line.strip()):
            lines.append(line)
        else:
            break
    return "".join(lines)


async def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=["check", "apply", "pull"])
    ap.add_argument("view", choices=sorted(VIEWS))
    ap.add_argument("-y", "--yes", action="store_true", help="apply without asking")
    a = ap.parse_args()

    url_path, rec_rel = VIEWS[a.view]
    rec_path = ROOT / rec_rel
    record, rec_text = read_record(rec_path)

    async with await connect() as ws:
        ha = HA(ws)
        cfg = await ha.call(type="lovelace/config", url_path=url_path)
        idx = [i for i, v in enumerate(cfg["views"]) if v.get("path") == a.view]
        if not idx:
            sys.exit(f"no view with path '{a.view}' on dashboard {url_path or 'lovelace'}")
        live = cfg["views"][idx[0]]

        diff = list(difflib.unified_diff(dump(live).splitlines(), dump(record).splitlines(),
                                         "live", rec_rel, lineterm=""))
        if a.action == "check":
            print("\n".join(diff) if diff else f"{a.view}: live view matches {rec_rel}")
            sys.exit(1 if diff else 0)

        if a.action == "pull":
            if not diff:
                print("already in step, nothing to pull")
                return
            rec_path.write_text(header(rec_text) + dump(live))
            print(f"wrote live view into {rec_rel} - review with git diff")
            return

        # apply
        if not diff:
            print("already in step, nothing to apply")
            return
        print("\n".join(diff))
        if not a.yes and input("\napply this to the live dashboard? [y/N] ").strip().lower() != "y":
            sys.exit("not applied")
        cfg["views"][idx[0]] = record
        await ha.call(type="lovelace/config/save", url_path=url_path, config=cfg)
        again = await ha.call(type="lovelace/config", url_path=url_path)
        ok = again["views"][idx[0]] == record
        print("applied and verified" if ok else "saved, but the read-back differs - run check")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
