import os
import csv
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
}

# Simulated staleness threshold — flags anyone with no login in this many days
STALE_DAYS_THRESHOLD = 0

REPORT_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "access-certification-report.csv"
)


def get_all_users():
    resp = requests.get(f"{ORG_URL}/api/v1/users?limit=200", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_user_groups(user_id):
    resp = requests.get(f"{ORG_URL}/api/v1/users/{user_id}/groups", headers=HEADERS)
    return resp.json() if resp.status_code == 200 else []


def days_since(iso_timestamp):
    if not iso_timestamp:
        return None
    last = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - last).days


def run_access_review():
    users = get_all_users()
    rows = []

    print(f"Reviewing {len(users)} users...\n")

    for user in users:
        profile = user["profile"]
        name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
        email = profile.get("email")
        status = user.get("status")
        last_login = user.get("lastLogin")

        groups = get_user_groups(user["id"])
        group_names = [
            g["profile"]["name"]
            for g in groups
            if not g["profile"]["name"].startswith("Everyone")
        ]

        days_inactive = days_since(last_login)

        flagged = "N"
        reason = ""

        if status == "DEPROVISIONED" and group_names:
            flagged = "Y"
            reason = "Deactivated user still has active group assignments"
        elif (
            days_inactive is not None
            and days_inactive >= STALE_DAYS_THRESHOLD
            and group_names
        ):
            flagged = "Y"
            reason = f"Inactive {days_inactive} days with active access"
        elif last_login is None and status == "ACTIVE" and group_names:
            flagged = "Y"
            reason = "Never logged in but has active access"

        rows.append(
            {
                "Name": name,
                "Email": email,
                "Status": status,
                "Groups": "; ".join(group_names) if group_names else "None",
                "Last Login": last_login or "Never",
                "Flagged": flagged,
                "Reason": reason,
            }
        )

        print(f"{name:<25} {status:<15} Flagged: {flagged}")

    REPORT_PATH.parent.mkdir(exist_ok=True)
    with open(REPORT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Name",
                "Email",
                "Status",
                "Groups",
                "Last Login",
                "Flagged",
                "Reason",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    flagged_count = sum(1 for r in rows if r["Flagged"] == "Y")
    print(f"\nReview complete. {flagged_count} of {len(rows)} users flagged.")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    run_access_review()
