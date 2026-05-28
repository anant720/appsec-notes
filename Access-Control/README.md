# Access Control & IDOR

## Overview
Access control vulnerabilities, primarily Insecure Direct Object References (IDOR) and Broken Access Control (BAC), occur when an application fails to cryptographically verify or enforce authorization checks on requested resources. Attackers exploit this by manipulating references (like database IDs, filenames, or usernames) to access data belonging to other users.

## Vulnerability Classifications

### 1. Horizontal Privilege Escalation
An attacker accesses resources belonging to a user with the same privilege level.
- **Example:** User A (`user_id=101`) modifies an API request to `GET /api/invoices?user_id=102` and views User B's invoices.

### 2. Vertical Privilege Escalation
A standard user accesses administrative or higher-privileged functions.
- **Example:** A standard user navigates directly to `/admin/dashboard` or modifies a POST payload during registration to include `"role": "admin"`.

### 3. Context-Dependent Access Control
Flaws in multi-tenant architectures where users might be admins in "Tenant A" but only standard users in "Tenant B", and the application fails to validate the context of the request.

## Methodology for Discovering IDORs
1. **Extensive Mapping:** Identify all endpoints that consume identifiers (in the URI path, query strings, request bodies, or custom headers).
2. **Multi-Account Matrix Testing:** Utilize Burp Suite's "Auth Matrix" extension or manually configure two separate, low-privileged accounts (User A and User B).
3. **Parameter Tampering:** Intercept User A's requests and swap identifiers with User B's to test horizontal escalation.
4. **Method Substitution:** If a strict endpoint like `GET /api/users/123` is properly protected, test alternate methods like `POST`, `PUT`, `PATCH`, or `DELETE` to the same endpoint.

## Engineering Insights from Sentinel Security Platform
During the development of the **Sentinel Security Platform** (a multi-tenant SOC telemetry platform), access control was a primary architectural focus.

- **The Anti-Pattern:** Enforcing role checks purely at the UI layer (hiding buttons) while leaving the underlying API routes unprotected.
- **Secure Architecture:** I implemented Role-Based Access Control (RBAC) at the middleware layer. Every API endpoint validates the user's session token, extracts the associated UUID, and explicitly queries PostgreSQL (with a Redis caching layer) to verify permissions against the requested resource.
- **Identifier Obfuscation:** Replaced sequential integer IDs with UUIDv4 across all database schemas. While UUIDs do not inherently fix access control flaws (if leaked, the resource is still accessible), they make automated IDOR enumeration and discovery exponentially harder.