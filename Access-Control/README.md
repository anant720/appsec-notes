# Access Control & IDOR

## Overview
Access control vulnerabilities, primarily Insecure Direct Object References (IDOR) and Broken Access Control (BAC), occur when an application fails to cryptographically verify or enforce authorization checks on requested resources. Attackers exploit this by manipulating references (like database IDs, filenames, or usernames) to access data belonging to other users.

## Real-World Usage
- **Where it appears:** RESTful APIs, document management systems, user profile settings, and payment portals.
- **Commonly affected systems:** Multi-tenant SaaS applications where tenant boundaries are improperly enforced at the database query level.
- **Architectural Causes:** Trusting the client to not modify API parameters, or implementing authorization checks solely in the frontend UI while leaving the backend API exposed.
- **Why developers introduce it:** Assuming that if a user cannot *see* the UI button for another user's invoice, they won't manually craft the API request to fetch it.

## Where I Used / Observed This Concept
- **Sentinel Security Platform:** Engineered a multi-tenant SOC environment where IDORs would mean a catastrophic cross-tenant data breach. Implemented RBAC middleware to strictly enforce boundaries.
- **CTF Exploit Chains:** Escalated privileges horizontally by iterating sequential IDs on a user profile endpoint after bypassing JWT authentication.

## Attacker Mindset
- **What they look for:** Predictable, sequential identifiers (e.g., `user_id=1055`) in URLs, bodies, or headers.
- **Exploitation Goals:** Unauthorized data access (horizontal escalation) or administrative takeover (vertical escalation).
- **Evasion Tactics:** Method substitution (changing GET to POST), parameter pollution (sending two `user_id` parameters to bypass the check but exploit the query).

## Engineering Perspective
- **Defensive Architecture:** Authorization must be enforced at the data-access layer. Before returning a record, the backend must verify: `SELECT * FROM data WHERE id = $1 AND owner_id = $2`.
- **Secure Coding:** Replace easily guessable sequential IDs with cryptographically secure UUIDv4s. While UUIDs do not "fix" IDOR (it becomes an information disclosure issue), they prevent mass automated enumeration.

## Security Engineering Notes
- **Auth Middleware Validation:** Implement global middleware that explicitly requires an authorization definition for *every* route, failing closed if a definition is missing.
- **Tenant Isolation:** In multi-tenant environments, inject the `tenant_id` from the secure session token directly into all database queries, ignoring any client-provided tenant data.

## Detection Opportunities
- **Telemetry:** Monitor API logs for users requesting a high volume of `403 Forbidden` or `404 Not Found` errors across different resource IDs (indicating an IDOR enumeration attack).
- **SIEM Rules:** Alert on users tampering with JWT claims or session cookies.

## Related Vulnerabilities
- **Broken Object Level Authorization (BOLA):** The modern API-centric term for IDOR.
- **Mass Assignment:** Often combined with IDOR to modify another user's attributes.

## Interview Insights
- **Common Question:** "Does using UUIDs fix IDOR?"
  - *Answer:* No, it mitigates enumeration. If a UUID leaks (e.g., via Referer headers or a separate info leak), the attacker can still access the resource if access controls are broken. It's security by obscurity; true access control requires identity verification at the backend.

## Project Connections
- **Sentinel Security Platform:** Uses a robust RBAC implementation. Every request extracts the user's UUID and roles from the validated JWT, enforcing strict tenant isolation on every PostgreSQL query to mitigate Broken Access Control.

## References
- [OWASP: Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [PortSwigger: Insecure Direct Object References](https://portswigger.net/web-security/access-control/idor)
- [OWASP API Security Top 10: BOLA](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)