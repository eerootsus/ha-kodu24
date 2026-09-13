#!/usr/bin/env bash
# Snapshot the ZHA mesh topology: who parents whom, and at what first-hop LQI.
#
# Why this exists: nothing in HA records the two facts that decide whether a
# sleepy device is reachable -- its *parent* and its *first-hop* LQI. The
# per-device `sensor.*_lqi` entities do NOT measure that. LQI is a MAC-layer
# measurement taken by the receiving radio, so the coordinator's number
# describes the last hop into the coordinator. For anything behind a router
# that is a different radio link entirely: on 2026-09-13 the Ada TRV read a
# comfortable 178 on its sensor while its actual hop to its parent was 45.
#
# The real numbers live only in ZHA's neighbour table in /config/zigbee.db,
# which is overwritten on every topology scan and never historised. This
# script reads it over ssh (same transport as deploy.sh, no HA token needed)
# and prints a stable, sorted, diffable report.
#
# Usage:
#   ./zigbee-topology.sh            print the current topology
#   ./zigbee-topology.sh --save     also store it under topology/ (tracked)
#   ./zigbee-topology.sh --diff     diff the two most recent saved snapshots
#
# Freshness caveat: the neighbour table only changes when ZHA runs a topology
# scan (periodically, and at startup). A snapshot taken seconds after a
# re-parent may still show the old parent. For a deliberate before/after test
# see "Confirming a router actually helps" below.
#
# Confirming a router actually helps -- the order matters, because end devices
# do NOT migrate on their own:
#   1. ./zigbee-topology.sh --save          baseline
#   2. install and power the new router, let it join
#   3. power-cycle the OLD parent of the device you want to move; the child
#      orphans within ~7s (the eTRVs' long poll interval) and rejoins, picking
#      the best-heard router at that moment
#   4. wait for the next topology scan, or restart HA to force one
#   5. ./zigbee-topology.sh --save && ./zigbee-topology.sh --diff
# Skipping step 3 is how you wrongly conclude that adding routers did nothing.
set -euo pipefail

HA_HOST="${HA_HOST:-homeassistant.tail7c95c3.ts.net}"
HA_PORT="${HA_PORT:-22}"
HA_USER="${HA_USER:-root}"
HA_DB="${HA_DB:-/config/zigbee.db}"

cd "$(dirname "$0")"
SNAPDIR="topology"

MODE="print"
for arg in "$@"; do
  case "$arg" in
    --save) MODE="save" ;;
    --diff) MODE="diff" ;;
    -h|--help) sed -n '2,40p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [ "$MODE" = "diff" ]; then
  mapfile -t snaps < <(ls -1 "$SNAPDIR"/*.txt 2>/dev/null | tail -2)
  if [ "${#snaps[@]}" -lt 2 ]; then
    echo "need two saved snapshots in $SNAPDIR/ -- run --save twice" >&2
    exit 1
  fi
  echo "--- ${snaps[0]}"
  echo "+++ ${snaps[1]}"
  diff -u "${snaps[0]}" "${snaps[1]}" || true
  exit 0
fi

# ControlMaster for the same reason deploy.sh uses one: the ssh key lives in
# the 1Password agent and prompts per signature.
CTL="/tmp/ha-topology-%C"
SSH_OPTS=(-p "$HA_PORT"
          -o ControlMaster=auto -o ControlPath="$CTL" -o ControlPersist=60
          -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new)
cleanup() { ssh "${SSH_OPTS[@]}" -O exit "$HA_USER@$HA_HOST" 2>/dev/null || true; }
trap cleanup EXIT

# Names come from the Basic cluster (0x0000): attr 4 manufacturer, 5 model.
# Devices are keyed by the last two IEEE octets, which is what the neighbour
# table rows are readable by.
# Names come from the Basic cluster (0x0000): attr 4 manufacturer, 5 model.
# Devices are keyed by the last two IEEE octets, which is how the neighbour
# table rows read most legibly.
VIEWS="
CREATE TEMP VIEW names AS SELECT ieee, CAST(value AS TEXT) model
  FROM attributes_cache_v15 WHERE cluster_id=0 AND attr_id=5;
CREATE TEMP VIEW mfrs AS SELECT ieee, CAST(value AS TEXT) mfr
  FROM attributes_cache_v15 WHERE cluster_id=0 AND attr_id=4;
"

Q_ENDDEVICES="$VIEWS
SELECT substr(n.ieee,19)        AS device,
       cm.model                 AS model,
       substr(n.device_ieee,19) AS parent,
       pm.model                 AS parent_model,
       n.lqi                    AS first_hop_lqi
FROM neighbors_v15 n
LEFT JOIN names cm ON cm.ieee=n.ieee
LEFT JOIN names pm ON pm.ieee=n.device_ieee
WHERE n.relationship=1 AND n.rx_on_when_idle=0
ORDER BY cm.model, device;
"

Q_ROUTERS="$VIEWS
SELECT substr(r.ieee,19) AS router,
       rm.model          AS model,
       rf.mfr            AS mfr,
       r.lqi             AS lqi_at_coord,
       (SELECT COUNT(*) FROM neighbors_v15 c
         WHERE c.device_ieee=r.ieee AND c.relationship=1) AS children
FROM neighbors_v15 r
LEFT JOIN names rm ON rm.ieee=r.ieee
LEFT JOIN mfrs  rf ON rf.ieee=r.ieee
WHERE r.device_ieee=(SELECT ieee FROM devices_v15 WHERE nwk=0)
  AND r.rx_on_when_idle=1
ORDER BY router;
"


# A device claimed as a child by more than one router means one of those rows
# is stale: the device re-parented and the old parent has not been rescanned
# yet. That is a direct volatility indicator -- these are the links that moved
# recently.
Q_MOVED="$VIEWS
SELECT substr(n.ieee,19) AS device, cm.model AS model,
       GROUP_CONCAT(substr(n.device_ieee,19) || '(' || n.lqi || ')', '  ') AS claimed_by
FROM neighbors_v15 n
LEFT JOIN names cm ON cm.ieee=n.ieee
WHERE n.relationship=1
GROUP BY n.ieee HAVING COUNT(*) > 1
ORDER BY cm.model, device;
"

q() { ssh "${SSH_OPTS[@]}" "$HA_USER@$HA_HOST" "sqlite3 -header -column '$HA_DB'" <<<"$1"; }

report() {
  echo "# ZHA topology  $(date '+%Y-%m-%d %H:%M:%S %Z')  from $HA_USER@$HA_HOST:$HA_DB"
  echo "# first_hop_lqi = the parent's measurement of the child. NOT sensor.*_lqi,"
  echo "# which measures the last hop into the coordinator and says nothing about"
  echo "# a device that sits behind a router."
  echo
  echo "== END DEVICES  (first-hop LQI is the number that matters) =="
  q "$Q_ENDDEVICES"
  echo
  echo "== ROUTERS  (uplink LQI as the coordinator hears them, and child load) =="
  q "$Q_ROUTERS"
  echo
  echo "== RECENTLY MOVED  (claimed by >1 router; one row is stale) =="
  q "$Q_MOVED"
}

if [ "$MODE" = "save" ]; then
  mkdir -p "$SNAPDIR"
  OUT="$SNAPDIR/$(date '+%Y-%m-%d_%H%M').txt"
  report | tee "$OUT"
  echo
  echo "saved: $OUT"
else
  report
fi
