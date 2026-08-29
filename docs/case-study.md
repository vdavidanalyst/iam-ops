# Case Study: IAM-Ops — Building an Identity Lifecycle & Access Governance Platform

## The problem

Most IAM job postings ask for the same core competencies: SSO/federation (SAML, OIDC), automated user lifecycle management, RBAC design, access certification for compliance (SOX and similar), and incident response for identity-related security events. It's rare to find a single portfolio project that demonstrates all of these together, end-to-end, against a real identity provider rather than a slide deck or a theoretical writeup.

I built IAM-Ops to close that gap — a working system, not a description of one.

## Scope and constraints

I deliberately built this against Okta's **Integrator Free Plan** rather than a 30-day trial, so the environment wouldn't expire mid-project or during an active interview cycle. I also made an early scope decision to keep the deployment target as **real infrastructure that proves automation works outside a laptop**, not a public-facing production web app — nothing in a typical IAM Engineer JD asks for web hosting or public exposure, and adding that would have introduced security surface with no relevant signal to a hiring manager.

## What I built

**Identity foundation.** A live Okta org with MFA enforced on the admin account, an API token scoped for automation, and four RBAC groups mapped to a mock organizational structure (Engineering, Finance, HR, IT).

**SSO federation, both protocols.** A custom FastAPI application (`IAM-Ops Portal`) implementing the OIDC Authorization Code flow end-to-end, plus a SAML integration via Okta's RSA Test Service Provider, validated by a dedicated non-admin test user to reflect the real end-user login experience rather than testing as a Super Admin.

**Joiner/Mover/Leaver automation.** Three Python CLI scripts hitting Okta's REST API directly: `provision_user.py` (creates a user and assigns department-based group membership), `move_user.py` (handles department transfers, removing old group membership and adding new), and `deprovision_user.py` (deactivates a user and verifies access is fully revoked, with a `--dry-run` safety flag). Every action is logged in structured JSON for auditability.

**Access certification.** A script that pulls all users and their group memberships, flags accounts that are stale, never-activated, or retain access after deactivation, and outputs a CSV report suitable for an actual access review meeting — backed by a written policy document defining review cadence and escalation.

**Security monitoring.** A script that pulls Okta's System Log API and a second script that detects clusters of failed MFA attempts within a time window. This wasn't tested against synthetic data — it caught a **real cluster of 3 failed MFA attempts within 9 seconds** on my own account during testing, which became the basis for a documented incident-response scenario.

**Deployment.** Both the demo app and the automation scripts run on a GCP VM: the app as a systemd service, the access review script on a weekly cron schedule. During deployment, I discovered the app was briefly reachable from the public internet due to a broad, pre-existing firewall rule shared with another project on the same VM. Rather than modify infrastructure outside this project's scope, I hardened the app itself by binding it to localhost only — an example of not relying on a single, inherited control for a new service's security posture.

## What I learned

A few patterns stood out as I built this:

- **The same root cause can surface twice in different disguises.** Confusing the Okta admin console URL with the actual org base URL broke both my API connectivity test and my OIDC discovery endpoint, at two different phases, before I recognized the pattern.
- **Sandbox environments have real limits that are worth naming, not hiding.** Slack and GitHub's Okta integrations require ownership of a real backend domain — something a demo org doesn't have. Substituting Bookmark apps and a purpose-built SAML test SP wasn't a workaround to hide; it's an accurate reflection of what a free-tier sandbox can and can't demonstrate, and I said so directly in the documentation.
- **Correctly triggered access denials are successes, not bugs.** When my OIDC login first failed with "user not assigned to application," that was Okta's RBAC enforcement working exactly as designed — the fix was closing a gap in test data, not a flaw in the system.
- **Security posture shouldn't assume a single boundary is enough.** Discovering the firewall exposure and choosing to harden at the application layer, rather than touching a rule shared with unrelated infrastructure, reflects real operational judgment: know what you can safely change and what you shouldn't.

## Outcome

A fully working, documented, and deployed IAM environment: real OIDC and SAML federation, real lifecycle automation with audit logging, a real access certification pipeline, and a real (not staged) security incident detected and documented — all traceable back to specific requirements in the target job posting.

## What I'd do next at enterprise scale

- Replace standard Okta admin roles with custom roles using resource-set scoping for tighter least-privilege control
- Add SCIM-based provisioning for real SaaS applications instead of manual API-driven group assignment
- Move JML automation from cron-scheduled scripts to a proper orchestration layer (Okta Workflows or an internal job scheduler) with retries and alerting
- Route flagged security events to a real alerting channel (Slack/email) instead of requiring a manual script run
- Centralize audit logs in a SIEM rather than local JSON-line files
