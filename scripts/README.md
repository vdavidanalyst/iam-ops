# IAM-Ops Automation Scripts

Python CLI scripts for automating Okta user lifecycle management (Joiner/Mover/Leaver).

## Setup
Requires `.env` in the repo root with `OKTA_ORG_URL` and `OKTA_API_TOKEN`.

## Usage

**Provision a new user:**
python scripts/provision_user.py --first-name Alex --last-name Rivera --email alex@example.com --department engineering
Departments: engineering, finance, it, standard

**Move a user to a new department:**
python scripts/move_user.py --email alex@example.com --new-department it

**Deprovision (deactivate) a user:**
python scripts/deprovision_user.py --email alex@example.com --dry-run
python scripts/deprovision_user.py --email alex@example.com

## Logs
Each script writes JSON-line logs to /logs/ (provisioning.log, moves.log, deprovisioning.log) for audit purposes.