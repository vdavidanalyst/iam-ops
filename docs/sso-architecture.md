# SSO Architecture — IAM-Ops

This document describes the two federation protocols implemented in this project, why both were built, and how they differ.

---

## Why both protocols

The target role (IAM Engineer) explicitly lists both **SAML** and **OIDC** as required integration protocols. Most real enterprise environments run a mix of both — legacy and enterprise SaaS apps often only support SAML, while modern apps and internal tooling increasingly default to OIDC. An IAM Engineer needs to be fluent in configuring and troubleshooting both, not just one.

---

## Component overview

| Component | Role |
|---|---|
| **Okta** | Identity Provider (IdP) for both flows |
| **IAM-Ops Portal** (custom FastAPI app) | Service Provider for the OIDC flow |
| **RSA SAML Test Service Provider** | Service Provider for the SAML flow (Okta catalog test app, no real backend ownership required) |
| **`vdanalyst test`** | Dedicated non-admin test user, member of `GRP-Standard-Employee`, used to validate the real end-user SSO experience |

---

## OIDC Flow (Authorization Code)

**Apps involved:** IAM-Ops Portal (FastAPI) ↔ Okta

**Flow:**
1. User visits the IAM-Ops Portal and clicks **Login with Okta**.
2. The app redirects the user's browser to Okta's `/authorize` endpoint, requesting the `openid profile email` scopes.
3. User authenticates against Okta (username/password + MFA if configured).
4. Okta redirects back to the app's registered redirect URI (`/authorization-code/callback`) with a short-lived authorization code.
5. The app exchanges that code server-side for an **ID token** (JWT) and access token, calling Okta's token endpoint directly (not via the browser).
6. The app decodes the ID token to get the user's profile (name, email) and stores it in a server-side session.
7. User is shown as logged in on the portal.

**Key characteristic:** Tokens are JSON Web Tokens (JWTs) exchanged over REST calls. The authorization code never contains user data itself — it's just a one-time reference used to fetch tokens server-to-server, which is what makes this flow resistant to token interception in the browser.

---

## SAML Flow (IdP-initiated)

**Apps involved:** RSA SAML Test Service Provider ↔ Okta

**Flow:**
1. User (already authenticated to Okta) clicks the **RSA SAML Test Service Provider** tile from their Okta "My Apps" dashboard.
2. Okta builds a **SAML assertion** — an XML document containing the user's NameID (email) and any mapped attributes, cryptographically signed with Okta's SAML signing certificate.
3. Okta's browser response auto-submits this assertion via an HTML form POST directly to the Service Provider's Assertion Consumer Service (ACS) URL.
4. The RSA test site receives and validates the signed assertion, extracts the NameID and attributes, and displays the "Subject Information" confirming successful federation.

**Key characteristic:** The entire user identity payload (NameID, attributes) travels inside the signed XML assertion itself, POSTed via the browser in one step — there's no separate server-to-server token exchange the way OIDC has. Trust is established entirely through the signing certificate Okta generates for the app.

---

## SAML vs OIDC — summary

| | SAML | OIDC |
|---|---|---|
| **Data format** | XML assertions | JSON / JWTs |
| **Transport** | Browser-based HTTP POST | REST API calls (server-to-server for token exchange) |
| **Trust mechanism** | Signing certificate on the assertion | Client ID/secret + signed JWT |
| **Typical use case in this project** | Legacy/enterprise SaaS-style app (RSA test SP) | Custom internal app (FastAPI portal) |
| **Initiation tested** | IdP-initiated (from Okta dashboard) | SP-initiated (from the app's own login link) |

---

## Testing approach

Both flows were validated using a **dedicated non-admin test user** (`vdanalyst test`), added to `GRP-Standard-Employee`, rather than the org's Super Admin account. This was a deliberate choice after discovering that Super Admin accounts don't land on the standard end-user "My Apps" dashboard by default (see `troubleshooting-log.md`, entry 10) — using a real standard-employee identity gives a more accurate picture of what an actual end user experiences during SSO login, which matters more for validating the RBAC model than testing as an admin would.

---

## What's next

- Extend RBAC scoping so different roles see different app tiles (already partially in place via group-based assignment — see `rbac-design.md`)
- Add MFA enforcement policy specifically for the OIDC/SAML sign-on flows, not just the admin console
- In a production environment, replace the RSA test SP with a real SP-initiated SAML flow against an actual owned application, and enable SCIM-based provisioning alongside SSO for the apps that support it
