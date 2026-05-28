# 🛡️ Access Control, RBAC & IDOR Research Notes

*Author: Anant | GitHub: [anant720](https://github.com/anant720)*

---

## 📌 Overview
Access control vulnerabilities—primarily Insecure Direct Object References (IDOR) and Broken Access Control (BAC)—occur when an application fails to cryptographically verify or enforce authorization checks on requested resources. Unlike Injection or XSS, access control flaws are purely **business logic failures** that cannot be caught by generic Web Application Firewalls (WAFs).

This document outlines my offensive methodology for discovering these flaws and the architectural patterns I use to eliminate them in my own production applications.

---

## 🏗️ Real-World Engineering Context (My Projects)

Building multi-tenant systems requires absolute certainty in tenant isolation. Here is how I approach Access Control in my repositories:

### 1. [GigFlow](https://github.com/anant720/GigFlow) (Freelance Marketplace)
- **Role-Based Access Control (RBAC):** GigFlow handles distinctly different user roles (Clients, Freelancers, Admins). I architected the backend to ensure vertical privilege separation—so a Freelancer can never access Client billing endpoints or approve their own proposals.
- **Object-Level Security:** When a client accesses a private gig proposal, the Express backend explicitly verifies that the requested proposal ID belongs to the authenticated client's `userId`.

### 2. [Peblo-AI-Notes](https://github.com/anant720/Peblo-AI-Notes) (AI Workspace)
- **Workspace Isolation:** Because users store sensitive markdown notes and AI action items, horizontal privilege escalation (IDOR) would be catastrophic. I leveraged **NextAuth** to securely extract the user's session token and enforce that every API query filters strictly by the authenticated `userId`. User A literally cannot query User B's notes.

### 3. [pass-storage](https://github.com/anant720/pass-storage) (Credential Vault)
- **Strict Data Ownership:** In a password management context, relying on frontend UI hiding is unacceptable. Every retrieval query structurally mandates an ownership check at the database level, ensuring cross-tenant data leaks are mathematically impossible within the query structure.

---

## 🚨 Vulnerability Classifications & My Defenses

### 1. Horizontal Privilege Escalation (IDOR)
**The Flaw:** An attacker accesses resources belonging to another user with the identical privilege level (User A accesses User B's data).
**Attacker Mindset:** I map the API and look for identifiers: `GET /api/notes?id=502`. I change it to `503`. If it returns data, the access control is broken.
**Engineering Defense ([pass-storage implementation](https://github.com/anant720/pass-storage)):**
- Never trust the ID provided in the URL or body.
- Always append the authenticated user's ID to the database query.
- *SQL Example:* `SELECT * FROM passwords WHERE id = $1 AND owner_id = $2;`

### 2. Vertical Privilege Escalation
**The Flaw:** A standard user accesses administrative or higher-privileged functions.
**Attacker Mindset:** I intercept the registration or profile update payload and inject `"role": "admin"`. Alternatively, I force-browse to `/admin/dashboard` or `DELETE /api/users/12` using a standard session token.
**Engineering Defense ([GigFlow implementation](https://github.com/anant720/GigFlow)):**
- Implement strict global middleware that validates the JWT payload's `role` claim against a hardcoded list of required roles for the endpoint.

### 3. Missing Function Level Access Control
**The Flaw:** UI buttons for sensitive functions (like "Delete Project") are hidden from standard users, but the API endpoint itself (`POST /api/project/delete`) remains completely unprotected.
**Engineering Defense ([Peblo-AI-Notes implementation](https://github.com/anant720/Peblo-AI-Notes)):**
- Security by obscurity is not security. Every server-side Next.js API route must independently verify the NextAuth session before processing any logic.

---

## 🛠️ Security Engineering Architecture

When designing authorization systems, I enforce the following:

1. **Deny by Default:** Middleware must fail closed. If a route does not have an explicit authorization definition attached to it, the application should crash or return `403 Forbidden` by default.
2. **UUIDs over Sequential IDs:** Replace auto-incrementing integers (`user_id=105`) with cryptographically secure UUIDv4s (`user_id=f47ac10b-58cc-4372-a567-0e02b2c3d479`).
   - *Note:* UUIDs do not "fix" IDOR (it becomes an information disclosure issue), but they completely neutralize automated mass enumeration attacks.
3. **Decouple AuthN from AuthZ:** Authentication (AuthN - "Who are you?") is handled by JWT/NextAuth. Authorization (AuthZ - "What can you do?") must be evaluated on *every single request* inside the business logic controller.

---

## 🎤 Interview Insights

**Q: If you use a cryptographically unguessable UUID for your API endpoints, do you still need access control checks in the backend?**
*A:* Absolutely yes. Using a UUID only prevents *enumeration*. If a UUID leaks through a Referer header, a shared link, or a separate vulnerability (like a GraphQL introspection flaw), an attacker can access the resource if there is no backend ownership check (IDOR). Relying solely on UUIDs is security by obscurity.

**Q: How do you efficiently test for IDORs in a massive API?**
*A:* I use the **Autorize** extension in Burp Suite. I configure it with a low-privileged user's session cookie, and then I navigate the application manually using a high-privileged (Admin) account. Autorize automatically repeats all the admin's background requests using the low-privileged token and highlights which endpoints failed to block the unauthorized access.

---

## 🔗 References & My Repository Implementations
- **Workspace Isolation & NextAuth AuthZ:** [Peblo-AI-Notes Source Code](https://github.com/anant720/Peblo-AI-Notes)
- **Role-Based Access Control (RBAC):** [GigFlow Source Code](https://github.com/anant720/GigFlow)
- **Strict Data Ownership & Vault Security:** [pass-storage Source Code](https://github.com/anant720/pass-storage)
- [OWASP Top 10: Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [PortSwigger: Insecure Direct Object References (IDOR)](https://portswigger.net/web-security/access-control/idor)
- [OWASP API Security Top 10: Broken Object Level Authorization (BOLA)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)