# IAM-Ops Troubleshooting Log

A running record of real issues hit during this build and how they were resolved. Kept intentionally — this is exactly the kind of debugging an IAM Engineer does day-to-day, and it's stronger portfolio material than pretending everything worked on the first try.

---

### 1. PowerShell `mkdir -p` syntax error
**Where:** Phase 1, repo scaffolding
**Symptom:**
```
mkdir : A positional parameter cannot be found that accepts argument 'config'.
```
**Cause:** `mkdir -p scripts config docs screenshots logs` is bash syntax. PowerShell's `mkdir` (aliased to `New-Item`) doesn't accept multiple positional folder names with a `-p` flag the same way.
**Fix:** Used comma-separated syntax instead:
```powershell
mkdir scripts, config, docs, screenshots, logs
```

---

### 2. `os.getenv()` called with values instead of variable names
**Where:** Phase 1, first connectivity test
**Symptom:**
```
requests.exceptions.MissingSchema: Invalid URL 'None/api/v1/users/me': No scheme supplied.
```
**Cause:** `os.getenv()` was passed the actual Org URL and API token as arguments instead of the environment variable *names* (`OKTA_ORG_URL`, `OKTA_API_TOKEN`). Both lookups returned `None`, and `None` concatenated with `/api/v1/users/me` produced an invalid URL.
**Fix:** Corrected calls to `os.getenv("OKTA_ORG_URL")` and `os.getenv("OKTA_API_TOKEN")`. Also switched `.env` loading to always resolve from the repo root using `pathlib.Path`, so the script works regardless of the current working directory it's run from.

---

### 3. Org URL included the admin console path
**Where:** Phase 1 connectivity test, and again in Phase 3 OIDC setup
**Symptom (Phase 1):** Malformed base URL for API calls.
**Symptom (Phase 3):**
```
httpx.HTTPStatusError: Client error '404 Not Found' for url
'https://integrator-9803645-admin.okta.com/admin/home/.well-known/openid-configuration'
```
**Cause:** `OKTA_ORG_URL` in `.env` was set to the browser/admin console URL (`...-admin.okta.com/admin/home`) instead of the actual org base URL used by the API and OIDC discovery endpoint.
**Fix:** Corrected `.env` to the plain org base URL:
```
OKTA_ORG_URL=https://integrator-9803645.okta.com
```
No `-admin` suffix, no `/admin/home` path, no trailing slash.

---

### 4. Missing `dotenv` module when run with system Python
**Where:** Phase 1 validation
**Symptom:**
```
ModuleNotFoundError: No module named 'dotenv'
```
**Cause:** Script was run with the system Python interpreter instead of the project's virtual environment, which is where `python-dotenv` was actually installed.
**Fix:** Ran the script explicitly with the venv interpreter:
```powershell
.\venv\Scripts\python.exe .\scripts\test_connection.py
```

---

### 5. Dense/unreadable JSON output on connectivity test
**Where:** Phase 1, after initial success
**Symptom:** Full raw Okta user object printed as a single-line Python dict, including dozens of irrelevant `_links` entries (password reset URLs, factor reset URLs, etc.) — unreadable and not screenshot-friendly.
**Fix:** Replaced `print(resp.json())` with `print(json.dumps(resp.json(), indent=2))` for readable formatting, and later refactored to print only the relevant profile fields (ID, status, email, name, created date, last login) instead of the full payload.

---

### 6. Slack / GitHub app integrations required a real, owned domain
**Where:** Phase 2, RBAC app assignment
**Symptom:** Slack's Okta integration form returned:
```
Domain: The field cannot be left blank
```
and expected a real Slack workspace domain (e.g. `yourteam.slack.com`) to configure live SSO against.
**Cause:** Slack, GitHub, and similar catalog integrations are built to federate into a real, existing backend service — not usable as placeholder apps in a sandbox org with no real workspace behind them.
**Fix:** Switched to Okta's generic **Bookmark App** integration type for RBAC demonstration purposes (`Slack (Demo)`, `Expensify (Demo)`, `GitHub (Demo)`), which only requires a label and any URL — sufficient to demonstrate group-based app assignment without needing to own the real backend service.

---

### 7. Duplicate admin role assignment error
**Where:** Phase 2, IT Admin role assignment
**Symptom:**
```
error: An action or an object with the same parameters already exists.
```
**Cause:** Likely a double-submission on the admin role assignment form; the first request had already succeeded before the error appeared.
**Fix:** No code change needed — verified via **Security → Administrators** that both roles (Application Administrator, Help Desk Administrator) were already correctly assigned to `GRP-IT-Admin`. Treated the error as a harmless duplicate-request rejection.

---

### 8. `httpx` missing despite Authlib being installed
**Where:** Phase 3, first attempt to run the FastAPI OIDC app
**Symptom:**
```
ModuleNotFoundError: No module named 'httpx'
```
**Cause:** Authlib's Starlette integration depends on `httpx` for its async HTTP client, but it isn't automatically pulled in as a dependency in this Authlib version.
**Fix:**
```powershell
pip install httpx
pip freeze > requirements.txt
```

---

### 9. OIDC login returned 400 — user not assigned to application
**Where:** Phase 3, first login attempt through the FastAPI app
**Symptom:**
```
400 Bad Request — User is not assigned to the client application.
Error Code: access_denied
```
**Cause:** The `IAM-Ops Portal` OIDC app was assigned to `GRP-Standard-Employee`, but the account being used to test login was not a member of that group.
**Fix:** Added the test account to `GRP-Standard-Employee` via **Directory → Groups → GRP-Standard-Employee → People → Add People**, rather than assigning the app directly to the individual — kept access flowing through group membership to stay consistent with the RBAC model, not a one-off exception.

---

## Patterns worth noting for interviews

- Several issues (2, 3) trace back to the same root cause — confusing the **admin console URL** with the **org base URL**. Once recognized, the second occurrence took seconds to fix instead of a full debugging cycle.
- Issue 6 is a useful example of **sandbox environment limitations vs. production reality** — real orgs won't hit this, since they own the backend services being integrated.
- Issue 9 demonstrates the RBAC model actually being enforced correctly by Okta, not a bug — the "fix" was closing an intentional gap in test data, not overriding a security control.

---
### 10. Admin account couldn't reach end-user dashboard
**Where:** Phase 3, SAML testing
**Symptom:** Logging in as the org's Super Admin always routed to the Admin Console, with no way to reach the standard "My Apps" end-user view.
**Cause:** Super Admin accounts on Okta don't get the standard end-user dashboard experience by default.
**Fix:** Created a dedicated non-admin test user and added them to `GRP-Standard-Employee`, which correctly landed on the standard end-user dashboard — also a more realistic way to validate the actual employee SSO experience anyway.