import os
from pathlib import Path

import requests
from dotenv import load_dotenv
import json

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
org_url = os.getenv("OKTA_ORG_URL", "").removesuffix("/admin/home").rstrip("/")
token = os.getenv("OKTA_API_TOKEN")

if not org_url or not token:
    raise RuntimeError(
        "Set OKTA_ORG_URL and OKTA_API_TOKEN in .env before running this script"
    )

headers = {"Authorization": f"SSWS {token}", "Accept": "application/json"}
resp = requests.get(f"{org_url}/api/v1/users/me", headers=headers)

print(resp.status_code)
print(json.dumps(resp.json(), indent=2))
# print(f"Status: {resp.status_code}, Email: {resp.json()['profile']['email']}")
