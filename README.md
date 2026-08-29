# IAM-Ops: Enterprise Identity Lifecycle & Access Governance Platform

A hands-on IAM engineering project built to demonstrate real-world identity and access management skills: SSO federation, automated user lifecycle management, RBAC design, access certification, security monitoring, and production deployment — all built against a live Okta environment.

**Built targeting:** IAM Engineer roles requiring Okta administration, SSO/SAML/OIDC integration, lifecycle automation, and compliance support (e.g., SOX-relevant access governance).

---

## What this project demonstrates

| JD Requirement | Where it's proven |
|---|---|
| Design, deploy, maintain IAM solutions (Okta) | Full Okta org setup, RBAC groups, admin role scoping |
| SSO, MFA, federation services | Working OIDC + SAML integrations, MFA enrolled on admin account |
| SAML, OAuth, OpenID Connect app integration | `demo-app/` (OIDC via FastAPI) + RSA SAML Test SP integration |
| User lifecycle (joiner/mover/leaver) | `scripts/provision_user.py`, `move_user.py`, `deprovision_user.py` |
| Automate provisioning/deprovisioning | Same JML scripts, fully API-driven, logged |
| RBAC models | `docs/rbac-design.md` + live Okta Groups/app assignments |
| Access reviews and certifications | `scripts/access_review.py` + `docs/access-certification-report.csv` |
| Least-privilege enforcement | Scoped Okta admin roles (not Super Admin) + least-privilege GitHub PAT scoping |
| Compliance support (SOX) | `docs/access-review-policy.md` |
| Monitor/respond to identity security incidents | `scripts/pull_system_log.py`, `flag_suspicious.py`, `docs/incident-scenario.md` (real detected MFA-failure cluster) |
| Maintain audit logs and documentation | `logs/`, `docs/troubleshooting-log.md` |
| Scripting/automation (Python, PowerShell-equivalent) | All scripts in `scripts/`, built and run via Python CLI tools |
| Work with APIs for system integrations | Every script uses Okta's REST API directly |
| Cross-functional support (IT/Security/HR/business) | RBAC design maps departments (Engineering, Finance, HR, IT) to access needs |

---

## Architecture

```
                     ┌─────────────────┐
                     │   Okta (IdP)    │
                     │ Integrator Free │
                     └────────┬────────┘
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────▼─────┐  ┌──────▼──────┐  ┌─────▼──────┐
       │ IAM-Ops    │  │ RSA SAML    │  │  Python    │
       │ Portal     │  │ Test SP     │  │  Scripts   │
       │ (OIDC/     │  │ (SAML)      │  │  (JML,     │
       │ FastAPI)   │  │             │  │  Review,   │
       └────────────┘  └─────────────┘  │  Audit)    │
                                          └─────┬──────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │  GCP VM (systemd +    │
                                    │  cron scheduled jobs) │
                                    └────────────────────────┘
```

---

## Tech stack

- **Identity Provider:** Okta (Integrator Free Plan)
- **Automation:** Python 3, `requests`, `python-dotenv`
- **SSO Demo App:** FastAPI + Authlib (OIDC Authorization Code flow)
- **SAML:** Okta RSA SAML Test Service Provider
- **Deployment:** GCP Compute Engine VM, systemd, cron
- **Version control:** Git/GitHub

---

## Repository structure

```
iam-ops/
├── demo-app/              # FastAPI OIDC demo application
│   └── main.py
├── scripts/               # JML automation, access review, audit logging
│   ├── provision_user.py
│   ├── move_user.py
│   ├── deprovision_user.py
│   ├── access_review.py
│   ├── pull_system_log.py
│   ├── flag_suspicious.py
│   ├── test_connection.py
│   └── README.md
├── docs/
│   ├── rbac-design.md
│   ├── access-review-policy.md
│   ├── access-certification-report.csv
│   ├── sso-architecture.md
│   ├── incident-scenario.md
│   └── troubleshooting-log.md
├── screenshots/            # Evidence for every phase, numbered by folder (01-setup through 08-deployment)
├── logs/                   # JSON-line audit logs (provisioning, moves, deprovisioning, audit)
├── requirements.txt
└── .env.example
```

---

## Setup (to run this yourself)

1. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/vdavidanalyst/iam-ops.git
   cd iam-ops
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your own Okta org URL, API token, and OIDC client credentials.
3. Run the connectivity test: `python scripts/test_connection.py`
4. Explore the JML scripts, access review, and audit tooling under `scripts/`.

---

## Key design decisions

- **Okta Integrator Free Plan** was chosen over the 30-day Okta trial specifically to avoid the project breaking mid-build or mid-interview-cycle due to expiry.
- **Bookmark apps and the RSA SAML Test Service Provider** were used in place of real SaaS integrations (Slack, GitHub) because those require ownership of a real backend domain — a sandbox-appropriate substitution that still proves group-based RBAC assignment and real SAML protocol handling.
- **Admin roles were scoped** (Application Administrator + Help Desk Administrator) rather than granting Super Admin, mirroring least-privilege principles applied to administrative access, not just end-user access.
- **The demo app is deployed but not publicly exposed** — a deliberate scope decision. The JD asks for IAM engineering, not public web hosting; exposing the app externally would add security surface with no relevant signal. See `docs/troubleshooting-log.md` entry 11 for a real example of catching and reasoning through this exact risk on the deployment VM.

---

## What I'd do differently at enterprise scale

- Use custom Okta admin roles with resource-set scoping (limited on the Integrator Free tier) instead of standard roles
- Add SCIM-based provisioning for real SaaS integrations instead of manual API calls
- Move from cron to a proper workflow orchestrator (e.g., Okta Workflows or an internal scheduler) for JML automation, with retries and alerting
- Add automated alerting (e.g., Slack/email webhook) when `flag_suspicious.py` detects a real pattern, rather than requiring a manual script run
- Store audit logs in a centralized SIEM rather than local JSON-line files

---

## Documentation index

- [`docs/rbac-design.md`](docs/rbac-design.md) — mock org structure, roles, RBAC matrix
- [`docs/sso-architecture.md`](docs/sso-architecture.md) — OIDC and SAML flow breakdown
- [`docs/access-review-policy.md`](docs/access-review-policy.md) — review cadence, sign-off, escalation
- [`docs/incident-scenario.md`](docs/incident-scenario.md) — real detected MFA-failure cluster and response plan
- [`docs/troubleshooting-log.md`](docs/troubleshooting-log.md) — 11 real issues hit and resolved during the build

---

## Author

Victor David Sarkibaka — IT professional pursuing IAM engineering roles. [GitHub](https://github.com/vdavidanalyst) · [X/Twitter](https://x.com/vdanalyst1)
