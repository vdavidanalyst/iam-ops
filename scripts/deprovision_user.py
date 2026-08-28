import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ORG_URL = os.getenv("OKTA_ORG_URL")
TOKEN = os.getenv("OKTA_API_TOKEN")

if not ORG_URL or not TOKEN:
    raise RuntimeError("Missing OKTA_ORG_URL or OKTA_API_TOKEN in .env")

HEADERS = {
    "Authorization": f"SSWS {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "deprovisioning.log"


def log_action(action: dict):
    LOG_PATH.parent.mkdir(exist_ok=True)
    action["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(action) + "\n")


def find_user_by_email(email):
    resp = requests.get(
        f"{ORG_URL}/api/v1/users/{email}",
        headers=HEADERS,
    )
    if resp.status_code != 200:
        print(f"User not found: {email}")
        sys.exit(1)
    return resp.json()


def get_user_groups(user_id):
    resp = requests.get(
        f"{ORG_URL}/api/v1/users/{user_id}/groups",
        headers=HEADERS,
    )
    return resp.json() if resp.status_code == 200 else []


def deprovision_user(email, dry_run=False):
    user = find_user_by_email(email)
    user_id = user["id"]
    status = user.get("status")

    groups_before = get_user_groups(user_id)
    group_names = [g["profile"]["name"] for g in groups_before]
    print(f"Current status: {status}")
    print(f"Current group memberships: {group_names}")

    if dry_run:
        print("[DRY RUN] No changes made. Remove --dry-run to actually deactivate.")
        return

    if status == "DEPROVISIONED":
        print("User is already deactivated.")
        log_action(
            {
                "action": "deprovision_skipped",
                "email": email,
                "user_id": user_id,
                "reason": "already deactivated",
            }
        )
        return

    # Deactivate the user (Okta automatically removes app/group assignments on deactivation)
    resp = requests.post(
        f"{ORG_URL}/api/v1/users/{user_id}/lifecycle/deactivate",
        headers=HEADERS,
    )

    if resp.status_code != 200:
        print(f"Failed to deactivate. Status: {resp.status_code}")
        print(resp.text)
        log_action(
            {
                "action": "deprovision_failed",
                "email": email,
                "user_id": user_id,
                "error": resp.text,
            }
        )
        sys.exit(1)

    print(f"User deactivated: {email}")

    # Verify groups were cleared
    groups_after = get_user_groups(user_id)
    print(
        f"Group memberships after deactivation: {[g['profile']['name'] for g in groups_after]}"
    )

    log_action(
        {
            "action": "deprovision",
            "email": email,
            "user_id": user_id,
            "groups_before": group_names,
            "groups_after": [g["profile"]["name"] for g in groups_after],
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deprovision (deactivate) a user in Okta"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the action without making changes",
    )
    args = parser.parse_args()

    deprovision_user(args.email, dry_run=args.dry_run)
