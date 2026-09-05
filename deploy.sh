#!/usr/bin/env bash
# Deploy this repo's packages to Home Assistant.
#
# Requires the "Advanced SSH & Web Terminal" add-on (port 22222) with this
# workstation's public key in its `authorized_keys` option.
#
# Always over the tailnet: HA sits on a network segment this workstation
# cannot reach directly (its LAN address does not even ping from the wifi),
# so the tailnet name is the only route. Nabu Casa remote UI cannot carry
# ssh -- it proxies the frontend only.
#
# ControlMaster is not an optimisation here: the ssh key lives in the
# 1Password agent, which prompts for approval per signature. Without a shared
# connection every rsync in the manifest would raise its own prompt and the
# later ones would time out waiting.
#
# What is NOT deployed: `dashboard/` directories are records of storage-mode
# dashboards and paste-in card templates, not files HA loads. Copying them
# into /config would be harmless but misleading.
set -euo pipefail

HA_HOST="${HA_HOST:-homeassistant.tail7c95c3.ts.net}"
HA_PORT="${HA_PORT:-22222}"
HA_USER="${HA_USER:-root}"
HA_CONFIG="${HA_CONFIG:-/config}"

DRY=""
RESTART=""
for arg in "$@"; do
  case "$arg" in
    -n|--dry-run) DRY="--dry-run" ;;
    --restart)    RESTART=1 ;;
    -h|--help)
      sed -n '2,20p' "$0" | sed 's/^# \?//'
      echo
      echo "Usage: $0 [-n|--dry-run] [--restart]"
      echo "Env: HA_HOST HA_PORT HA_USER HA_CONFIG"
      exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# src (repo-relative)   dst (under $HA_CONFIG)   mirror?
#
# mirror=yes adds --delete, so a file removed from the repo also leaves HA.
# It is deliberately OFF for themes/ and pyscript/, which are shared with
# things this repo does not own -- HACS drops themes into config/themes/, and
# deleting a HACS theme because it is not in this repo would be a nasty
# surprise. Package directories we fully own are mirrored.
MANIFEST=(
  "danfoss.py         pyscript/danfoss.py   no"
  "trv-climate/       trv-climate/          yes"
  "backup-monitor/    backup-monitor/       yes"
  "battery-monitor/   battery-monitor/      yes"
  "chores/            chores/               yes"
  "curve-test/        curve-test/           yes"
  "themes/            themes/               no"
)

cd "$(dirname "$0")"

# %C is an ssh token (hash of the connection), so this is unique per target
# without mktemp getting involved.
CTL="/tmp/ha-deploy-%C"
SSH_OPTS=(-p "$HA_PORT"
          -o ControlMaster=auto -o ControlPath="$CTL" -o ControlPersist=180
          -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new)
cleanup() { ssh "${SSH_OPTS[@]}" -O exit "$HA_USER@$HA_HOST" 2>/dev/null || true; }
trap cleanup EXIT

echo "==> $HA_USER@$HA_HOST:$HA_PORT$HA_CONFIG${DRY:+  (dry run)}"
if ! ssh "${SSH_OPTS[@]}" "$HA_USER@$HA_HOST" true 2>/dev/null; then
  echo "cannot reach HA over ssh. Is the Advanced SSH & Web Terminal add-on" >&2
  echo "installed, started, and holding this workstation's public key?" >&2
  exit 1
fi

for entry in "${MANIFEST[@]}"; do
  read -r src dst mirror <<<"$entry"
  [[ -e "$src" ]] || { echo "  skip $src (not in repo)"; continue; }
  DEL=""; [[ "$mirror" == "yes" ]] && DEL="--delete"
  echo "  $src -> $HA_CONFIG/$dst${DEL:+  (mirrored)}"
  ssh "${SSH_OPTS[@]}" "$HA_USER@$HA_HOST" "mkdir -p '$(dirname "$HA_CONFIG/$dst")'"
  rsync -a $DEL $DRY \
        --exclude 'dashboard/' --exclude '*.md' --exclude '__pycache__/' \
        -e "ssh ${SSH_OPTS[*]}" \
        "$src" "$HA_USER@$HA_HOST:$HA_CONFIG/$dst"
done

[[ -n "$DRY" ]] && { echo "==> dry run, nothing changed"; exit 0; }

echo "==> checking configuration"
if ssh "${SSH_OPTS[@]}" "$HA_USER@$HA_HOST" "ha core check" ; then
  echo "==> config OK"
else
  echo "!! config check FAILED - not restarting. Fix before reloading." >&2
  exit 1
fi

if [[ -n "$RESTART" ]]; then
  echo "==> restarting Home Assistant"
  ssh "${SSH_OPTS[@]}" "$HA_USER@$HA_HOST" "ha core restart"
else
  echo
  echo "Not reloaded. New helper entities (input_text, input_datetime) only"
  echo "appear after a restart or Developer Tools -> YAML -> Reload all."
  echo "Re-run with --restart to do it here."
fi
