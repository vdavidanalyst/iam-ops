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

DEPARTMENT_GROUP_MAP = {
    "engineering": "00g16v861c9AC7WBt698",
    "finance": "00g16v86w3kGmHrkv698",
    "it": "00g16v87fhx9qG44p698",
    "standard": "00g16v85mlu8hqZhJ698",
}

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "moves.log"


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


def move_user(email, new_department):
    user = find_user_by_email(email)
    user_id = user["id"]

    new_group_id = DEPARTMENT_GROUP_MAP.get(new_department.lower())
    if not new_group_id:
        print(f"No group mapped for department '{new_department}'")
        sys.exit(1)

    # Find current department groups (any group that's one of our 4 managed department groups)
    current_groups = get_user_groups(user_id)
    managed_group_ids = set(DEPARTMENT_GROUP_MAP.values())
    old_department_groups = [g for g in current_groups if g["id"] in managed_group_ids]

    old_departments = []
    for group in old_department_groups:
        group_id = group["id"]
        # Remove from old department group (skip if it's already the target group)
        if group_id != new_group_id:
            remove_resp = requests.delete(
                f"{ORG_URL}/api/v1/groups/{group_id}/users/{user_id}",
                headers=HEADERS,
            )
            if remove_resp.status_code == 204:
                dept_name = [
                    k for k, v in DEPARTMENT_GROUP_MAP.items() if v == group_id
                ][0]
                old_departments.append(dept_name)
                print(f"Removed from: {dept_name}")

    # Add to new department group
    add_resp = requests.put(
        f"{ORG_URL}/api/v1/groups/{new_group_id}/users/{user_id}",
        headers=HEADERS,
    )
    if add_resp.status_code == 204:
        print(f"Added to: {new_department}")
    else:
        print(f"Failed to add to new group. Status: {add_resp.status_code}")
        print(add_resp.text)
        sys.exit(1)

    log_action(
        {
            "action": "move",
            "email": email,
            "user_id": user_id,
            "old_departments": old_departments,
            "new_department": new_department,
        }
    )

    print(f"Move complete: {email} -> {new_department}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Move a user to a new department in Okta"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--new-department",
        required=True,
        choices=["engineering", "finance", "it", "standard"],
    )
    args = parser.parse_args()

    move_user(args.email, args.new_department)
