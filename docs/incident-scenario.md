# Incident Scenario — Failed MFA Cluster

## Detection
On 2026-08-27, the `flag_suspicious.py` script (run against pulled Okta System Log data) detected a cluster of 3 failed MFA authentication attempts for user Victor David Sarkibaka within a 9-second window (23:18:58 to 23:19:07 UTC), followed shortly after by additional failures and an eventual successful authentication at 23:19:38.

## Triage
In a real environment, this pattern warrants investigation because:
- Multiple rapid MFA failures can indicate a credential-stuffing attempt, a stolen/guessed password paired with MFA prompt bombing, or (less concerning) a legitimate user struggling with their authenticator app.
- The short window between failures (under 10 seconds apart in places) is more consistent with automated or rapid manual retry behavior than typical human pacing.

## Response steps (what would be taken in production)
1. **Do not assume benign** — treat as a potential account compromise attempt until ruled out.
2. **Check IP/location data** on each failed attempt (available in the full System Log payload, not just the summarized fields pulled here) — consistent IP suggests the legitimate user; inconsistent/foreign IP suggests attack.
3. **Contact the user directly** through a known-good channel (not email, in case that's compromised) to confirm whether the attempts were theirs.
4. **If confirmed malicious:** force a password reset, revoke all active sessions (`/api/v1/users/{userId}/lifecycle/reset_password` and session revocation endpoints), and temporarily suspend the account pending investigation.
5. **If confirmed benign:** no action needed beyond noting the pattern; consider whether the user needs help with their MFA method.

## Documentation
This event and its resolution would be logged in the access/security incident tracker with a timestamp, root cause, and outcome — matching the audit trail requirement in the JD.

## Detection logic used
See `scripts/flag_suspicious.py` — flags any actor with 3+ failed MFA events within a 10-minute rolling window, using real pulled Okta System Log data rather than synthetic test data.