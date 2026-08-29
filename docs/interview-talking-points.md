# Interview Talking Points — IAM-Ops (STAR Format)

Prepared answers drawing directly from the IAM-Ops project. Use these as a starting point, not a script — adapt the wording to how the question is actually asked.

---

## 1. "Tell me about a time you automated an access control or provisioning process."

**Situation:** I wanted to prove I could build real IAM automation, not just describe it, so I built a full Joiner/Mover/Leaver pipeline against a live Okta environment as a portfolio project.

**Task:** I needed scripts that could provision a new user with correct department-based group access, handle a department transfer, and fully deprovision a leaver — all auditable.

**Action:** I wrote three Python CLI tools using Okta's REST API directly: `provision_user.py`, `move_user.py`, and `deprovision_user.py`. Each one logs its actions in structured JSON, and the deprovisioning script includes a `--dry-run` flag so it can be previewed before making a destructive change — something I felt was non-negotiable for a real leaver process.

**Result:** All three scripts run end-to-end against a real Okta org, correctly assign and remove group-based access, and produce an audit trail. I tested the full lifecycle on several accounts and verified group membership changes in the Okta console after each run.

---

## 2. "How do you approach access reviews or certifications?"

**Situation:** The role I was targeting explicitly mentioned SOX-related compliance support, so I built an access review component into my portfolio project rather than treating it as an afterthought.

**Task:** Design a way to identify accounts that shouldn't still have active access — stale accounts, never-activated accounts, or deactivated users who somehow retained group membership.

**Action:** I wrote a script that pulls every user and their group assignments, checks last-login timestamps against a staleness threshold, and flags anomalies into a CSV report. I paired it with a written access review policy defining cadence, sign-off responsibility, and escalation timelines — because a report without a process behind it doesn't actually solve the compliance problem.

**Result:** Running it against my live test environment surfaced two real flagged accounts — not staged data — which gave me a legitimate example of the tool actually working as intended, and reinforced why review cadence matters even in a small environment.

---

## 3. "Describe a security incident you've investigated, or how you'd respond to one."

**Situation:** While building an audit logging script that pulls Okta's System Log API, I also built a second script to detect suspicious patterns — specifically, clusters of failed MFA attempts.

**Task:** I wanted the detection logic tested against real data, not a fabricated scenario.

**Action:** During testing, the script actually caught a real cluster — 3 failed MFA attempts within 9 seconds on my own account. I used that as the basis for a documented incident scenario: what the pattern could indicate (credential stuffing, MFA fatigue attack, or a legitimate user struggling with their authenticator), and what I'd do about it — check IP/location data, contact the user through an out-of-band channel, and be ready to force a password reset and revoke sessions if compromise is confirmed.

**Result:** I have a real, working detection script and a documented response plan grounded in an actual event, not a hypothetical — which I think demonstrates the instinct to verify tooling against real signal rather than just assuming it works.

---

## 4. "How do you think about least privilege in your own work, not just in policy documents?"

**Situation:** Two moments in this project forced me to apply least privilege to my own access, not just design it for hypothetical users.

**Task / Action (admin roles):** When setting up an IT Admin role in my RBAC model, I deliberately assigned two scoped Okta admin roles (Application Administrator, Help Desk Administrator) instead of Super Admin, even though Super Admin would have been faster to configure.

**Task / Action (tooling access):** Separately, when I needed to push code from a GCP VM to GitHub, I generated a Personal Access Token and scoped it to only the `repo` permission — not `workflow`, `admin:org`, `delete_repo`, or any of the other options GitHub offers by default.

**Result:** Both were small decisions that took slightly longer than the "easy" option, but they're the kind of habit that actually matters in production — every credential and role should carry exactly the access it needs and no more.

---

## 5. "Tell me about a mistake or a time something didn't work as expected during a technical project."

**Situation:** Early in the project, my connectivity test to Okta's API failed with a confusing URL error.

**Task:** Debug why a script that looked correct was producing `None` for both my org URL and API token.

**Action:** I traced it back to calling `os.getenv()` with the actual values instead of the environment variable names — a subtle mistake that's easy to make and easy to miss. Later in the project, a nearly identical class of error resurfaced: I had the Okta *admin console* URL saved instead of the org's actual base URL, which broke both a REST call and, separately, an OIDC discovery endpoint at a different phase of the build.

**Result:** I kept a running troubleshooting log throughout the project — eleven real issues in total — rather than quietly fixing things and moving on. Recognizing that the second URL issue was the same root cause as an earlier one meant I fixed it in seconds instead of restarting a full debugging cycle, which I think is the actual skill: pattern recognition across failures, not just fixing individual bugs.

---

## Quick reference — what to point to for each topic

| Topic | File/artifact to reference |
|---|---|
| SSO/OIDC | `demo-app/main.py`, `docs/sso-architecture.md` |
| SAML | RSA Test SP integration, `docs/sso-architecture.md` |
| JML automation | `scripts/provision_user.py`, `move_user.py`, `deprovision_user.py` |
| RBAC design | `docs/rbac-design.md` |
| Access reviews / SOX | `scripts/access_review.py`, `docs/access-review-policy.md` |
| Security monitoring | `scripts/pull_system_log.py`, `flag_suspicious.py`, `docs/incident-scenario.md` |
| Debugging / troubleshooting | `docs/troubleshooting-log.md` |
| Deployment / infrastructure | GCP VM, systemd service, cron job, firewall discovery (troubleshooting-log entry 11) |
