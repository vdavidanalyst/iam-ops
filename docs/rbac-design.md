# IAM-Ops RBAC Design

## Mock Organization Structure

**Departments:** Engineering, Finance, HR, IT

## Roles & Access Design

### 1. Standard Employee
- **Department:** All (baseline role, every user gets this)
- **Apps needed:** Company email, Slack/Teams, HR self-service portal
- **Justification:** Minimum viable access for any employee to function — no sensitive systems.

### 2. Engineering Manager
- **Department:** Engineering
- **Apps needed:** Everything Standard Employee has + engineering tooling (e.g., GitHub/GitLab admin, CI/CD dashboard), team performance/HR-lite data for direct reports
- **Justification:** Needs elevated access to manage a team and ship product, but not finance or company-wide HR data.

### 3. Finance-Sensitive User
- **Department:** Finance
- **Apps needed:** Everything Standard Employee has + finance/accounting system (e.g., NetSuite/QuickBooks-style app), payroll-adjacent tools
- **Justification:** Handles sensitive financial data — SOX-relevant. Access should be tightly scoped and reviewed most frequently of all roles.

### 4. IT Admin
- **Department:** IT
- **Apps needed:** Everything Standard Employee has + Okta Admin Console, device management, all app assignment capabilities
- **Justification:** Requires the broadest access to support the org, but this is exactly the role that needs the strongest MFA/PAM controls since it's the highest-value target for attackers.
- **Implementation note:** Assigned via Okta standard admin roles (Application Administrator + Help Desk Administrator), constrained to apps/groups where supported. Okta's Integrator Free tier limits custom resource-set scoping to Identity Governance-tier features — in a production environment, this would be tightened further using custom admin roles with granular resource sets.

## RBAC Matrix

| Role                   | Group                  | Apps Assigned                          | Justification                                    |
|-------------------------|--------------------------|-------------------------------------------|-----------------------------------------------------|
| Standard Employee       | GRP-Standard-Employee    | Email, Slack                              | Baseline access for all staff                       |
| Engineering Manager     | GRP-Engineering          | Email, Slack, GitHub Admin                | Team + product management needs                     |
| Finance-Sensitive User  | GRP-Finance-Sensitive    | Email, Slack, Finance App                 | Least-privilege, SOX-scoped, reviewed quarterly      |
| IT Admin                | GRP-IT-Admin             | Email, Slack, Okta Admin Console          | Broad access, requires strongest controls            |