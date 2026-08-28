import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
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

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"

# Event types worth tracking for identity security monitoring
RELEVANT_EVENTS = [
    "user.authentication.auth_via_mfa",
    "user.mfa.factor.deactivate",
    "user.account.update_profile",
    "application.lifecycle.update",
    "user.session.start",
    "user.lifecycle.deactivate",
    "policy.evaluate_sign_on",
]


def pull_logs(hours_back=24):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

    resp = requests.get(
        f"{ORG_URL}/api/v1/logs",
        headers=HEADERS,
        params={"since": since, "limit": 100},
    )

    if resp.status_code != 200:
        print(f"Failed to pull logs. Status: {resp.status_code}")
        print(resp.text)
        return

    events = resp.json()
    print(f"Pulled {len(events)} total events from the last {hours_back}h.\n")

    LOG_PATH.parent.mkdir(exist_ok=True)
    relevant_count = 0

    with open(LOG_PATH, "a") as f:
        for event in events:
            event_type = event.get("eventType", "")
            actor = event.get("actor", {}).get("displayName", "Unknown")
            outcome = event.get("outcome", {}).get("result", "UNKNOWN")
            published = event.get("published")

            record = {
                "eventType": event_type,
                "actor": actor,
                "outcome": outcome,
                "published": published,
            }

            f.write(json.dumps(record) + "\n")

            if event_type in RELEVANT_EVENTS or "failure" in outcome.lower():
                relevant_count += 1
                print(f"[{published}] {event_type} — {actor} — {outcome}")

    print(
        f"\n{relevant_count} relevant/notable events found. All events logged to {LOG_PATH}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull Okta System Log events")
    parser.add_argument(
        "--hours", type=int, default=24, help="How many hours back to pull events from"
    )
    args = parser.parse_args()

    pull_logs(hours_back=args.hours)
