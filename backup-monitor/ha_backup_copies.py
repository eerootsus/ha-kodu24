"""Where HA's own newest automatic backup actually is.

Publishes `sensor.ha_backup_copies`: `ok` or `problem`, with the newest automatic
backup, its age, and per location whether it holds that backup encrypted.
`backup_monitor.yaml` turns it into the healthy strip, the push and a recap line.

Why the backup manager is asked directly instead of trusting its own sensors:
`sensor.backup_last_successful_automatic_backup` only advances when every upload
succeeded, which catches a failed upload, but a location that is *unavailable*
(the Hetzner mount down, say) is skipped before upload and the backup still counts
as a success - only a repair issue says otherwise. So "did a backup run" is the
wrong question; "is the newest one in every place it should be" is the right one.

The rule is two off-site copies, not one (2026-11-05). Nabu Casa keeps only the
newest backup, so on its own it is one copy with no history; the Hetzner Storage
Box (sub-account u647127-sub3, Supervisor mount `hetzner_ha`) is the second.
"""

from datetime import datetime, timezone
from logging import Logger
from homeassistant.core import HomeAssistant
from homeassistant.components.backup.const import DATA_MANAGER

# agent id -> name in messages. Every one must hold the newest automatic backup;
# the off-site ones must hold it encrypted.
LOCATIONS = {
    "hassio.local": "Yellow",
    "cloud.cloud": "Nabu Casa",
    "hassio.hetzner_ha": "Hetzner",
}
OFFSITE = {"cloud.cloud", "hassio.hetzner_ha"}

# Automatic backups run daily (~04:50); 26 h is the margin the other jobs use.
MAX_AGE_H = 26

hass: HomeAssistant
log: Logger


@service
@time_trigger("startup")
@time_trigger("cron(*/30 * * * *)")
@state_trigger("event.backup_automatic_backup")
async def update_ha_backup_copies():
    """Publish sensor.ha_backup_copies from the backup manager's own listing."""
    backups, agent_errors = await hass.data[DATA_MANAGER].async_get_backups()
    problems = []

    for agent_id, err in agent_errors.items():
        problems.append(f"{LOCATIONS.get(agent_id, agent_id)} unreachable: {err}")

    newest = None
    for b in backups.values():
        if b.with_automatic_settings and (newest is None or b.date > newest.date):
            newest = b
    copies = {}
    age_h = None
    if newest is None:
        problems.append("no automatic backup at all")
    else:
        age_h = round((datetime.now(timezone.utc) - datetime.fromisoformat(newest.date)).total_seconds() / 3600, 1)
        if age_h > MAX_AGE_H:
            problems.append(f"newest automatic backup is {age_h:.0f} h old")
        for agent_id, name in LOCATIONS.items():
            status = newest.agents.get(agent_id)
            if status is None:
                copies[name] = "missing"
                if agent_id not in agent_errors:
                    problems.append(f"{name} does not hold the newest backup")
            elif agent_id in OFFSITE and not status.protected:
                copies[name] = "unencrypted"
                problems.append(f"{name} copy is not encrypted")
            else:
                copies[name] = "encrypted" if status.protected else "plain"

    state.set(
        "sensor.ha_backup_copies",
        value="problem" if problems else "ok",
        new_attributes={
            "friendly_name": "HA backup copies",
            "icon": "mdi:backup-restore",
            "newest": newest.date if newest else None,
            "newest_id": newest.backup_id if newest else None,
            "age_h": age_h,
            "copies": copies,
            "problems": problems,
            # Changes every run, so last_updated proves the check itself is alive.
            "checked": datetime.now(timezone.utc).isoformat(),
        },
    )
    if problems:
        log.warning(f"HA backup copies: {'; '.join(problems)}")
