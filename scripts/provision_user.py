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

# Maps department -> Okta Group ID
DEPARTMENT_GROUP_MAP = {
    "engineering": "00g16v861c9AC7WBt698",
    "finance": "00g16v86w3kGmHrkv698",
    "it": "00g16v87fhx9qG44p698",
    "standard": "00g16v85mlu8hqZhJ698",
}

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "provisioning.log"


def log_action(action: dict):
    LOG_PATH.parent.mkdir(exist_ok=True)
    action["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(action) + "\n")


def create_user(first_name, last_name, email, department):
    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "login": email,
        }
    }

    resp = requests.post(
        f"{ORG_URL}/api/v1/users?activate=true",
        headers=HEADERS,
        json=payload,
    )

    if resp.status_code != 200:
        print(f"Failed to create user. Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
        log_action(
            {
                "action": "provision_failed",
                "email": email,
                "department": department,
                "error": resp.json(),
            }
        )
        sys.exit(1)

    user = resp.json()
    user_id = user["id"]
    print(f"User created: {email} (ID: {user_id})")

    # Add to department group
    group_id = DEPARTMENT_GROUP_MAP.get(department.lower())
    if not group_id:
        print(
            f"Warning: no group mapped for department '{department}'. Skipping group assignment."
        )
    else:
        group_resp = requests.put(
            f"{ORG_URL}/api/v1/groups/{group_id}/users/{user_id}",
            headers=HEADERS,
        )
        if group_resp.status_code == 204:
            print(f"Added to group for department: {department}")
        else:
            print(f"Failed to add to group. Status: {group_resp.status_code}")
            print(group_resp.text)

    log_action(
        {
            "action": "provision",
            "email": email,
            "user_id": user_id,
            "department": department,
        }
    )

    return user_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provision a new user in Okta")
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--department",
        required=True,
        choices=["engineering", "finance", "it", "standard"],
    )
    args = parser.parse_args()

    create_user(args.first_name, args.last_name, args.email, args.department)
