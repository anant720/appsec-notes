import os

files = {
    "README.md": """# AppSec Research & Knowledge Vault

## Overview
Welcome to my Application Security (AppSec) knowledge repository. This vault serves as a centralized collection of my research, vulnerability analysis, exploit chain documentation, and defensive engineering strategies. 

## Research Philosophy
My approach to cybersecurity bridges the gap between the attacker mindset and engineering resilience. Having built systems like the **Sentinel Security Platform** and **AI Guardian Engine**, I analyze vulnerabilities not just to exploit them, but to understand root causes at the architectural level. Security is an engineering quality, not a patch.

## Objectives
- **Knowledge Consolidation:** Systematically document vulnerability classes, attack vectors, and real-world exploit chains.
- **Defensive Engineering:** Provide actionable mitigation strategies for developers, focusing on secure defaults.
- **Continuous Learning:** Track my progress in web application security, CTFs, and vulnerability research.

## Tooling & Expertise
- **Languages/Frameworks:** Node.js, React, Fastify
- **Databases:** PostgreSQL, Redis
- **Security Tools:** Burp Suite Professional, Wireshark, Nmap, Kali Linux
- **Infrastructure:** Docker, Linux
- **Domains:** API Security, JWT Authentication, RBAC, WebSockets

## Projects Integration Context
- **Sentinel Security Platform:** Multi-tenant SOC telemetry platform, heuristic intrusion detection engine, JWT auth, RBAC, API security.
- **AI Guardian Engine:** AI phishing/scam detection system, LLM integrations, NLP analysis, risk scoring.
- **SecurePass Analyzer:** Password security analyzer, entropy scoring, HaveIBeenPwned integration.

## Repository Structure
- `/Web-Cache-Deception` - Analysis of WCD mechanics, caching misconfigurations, and PortSwigger labs.
- `/JWT` - Deep dives into JSON Web Token vulnerabilities (alg confusion, null signatures).
- `/SSRF` - Server-Side Request Forgery mechanics, cloud metadata exfiltration, and chaining strategies.
- `/Access-Control` - Insecure Direct Object References (IDOR), Broken Access Control, and RBAC implementation flaws.
- `/API-Security` - API data exposure, mass assignment, and REST attack surfaces.
- `/Methodology` - My structured approach to web application pentesting and CTF exploit chains.
- `/Payloads` - Curated list of context-specific payloads for various injection and logic flaws.
- `/BurpSuite-Tips` - Optimization workflows, essential extensions, and efficient proxy configurations.

---
*Anant | B.Tech CSE Cybersecurity*
*GitHub: [anant720](https://github.com/anant720)*
""",

    "Web-Cache-Deception/README.md": """# Web Cache Deception (WCD)

## Overview
Web Cache Deception is a vulnerability where an attacker tricks a caching server (like a CDN, reverse proxy, or load balancer) into storing sensitive, user-specific content (such as a profile page, API response, or dashboard) which the attacker can subsequently access. This occurs due to discrepancies in how the cache server and the origin server parse and route the requested URI.

## Core Mechanism
The vulnerability manifests when three architectural conditions are met:
1. **Aggressive Edge Caching:** The edge server is configured to cache files based purely on static extensions (e.g., `.js`, `.css`, `.png`, `.jpg`).
2. **Permissive Origin Routing:** The origin server employs a routing mechanism that ignores unknown or trailing path extensions and resolves to the base endpoint (e.g., `/api/user/settings/nonexistent.css` maps to `/api/user/settings`).
3. **Session-Dependent Responses:** The origin server returns private data based on the authentication state (cookies, session tokens) of the requester.

## Real-World Usage
- **Where it appears:** Heavily utilized REST APIs sitting behind Cloudflare, Akamai, or AWS CloudFront.
- **Commonly affected systems:** SPAs (Single Page Applications) where routing is handled on the client-side, causing the backend to permissively return the `index.html` or base JSON response regardless of the URL path.
- **Why developers introduce it:** Misunderstanding the separation of concerns between edge caching rules (regex matching on `.js`/`.css`) and backend routing frameworks (like Express or Fastify ignoring trailing extensions).
- **Architectural Causes:** Monolithic architectures shifting to CDN-backed microservices without updating legacy routing fallbacks.

## Where I Used / Observed This Concept
- **PortSwigger Web Cache Deception Lab:** Exploited WCD to expose a victim's API key by manipulating path parameters and understanding cache rules via Param Miner.
- **Sentinel Security Platform:** While developing the telemetry API, I ensured our Nginx reverse proxy explicitly ignores path extensions for dynamic `/api/*` routes, preventing caching of sensitive SOC metrics.

## Attacker Mindset
- **What they look for:** Discrepancies between load balancers and backend servers. An attacker will append `.js`, `;x.css`, or `%0a.png` to sensitive endpoints and observe the `X-Cache` header for `HIT` or `MISS`.
- **Exploitation Goals:** Steal PII, API keys, CSRF tokens, or session identifiers that are embedded in the victim's cached page.
- **Trust Boundary Failures:** The cache implicitly trusts that if a URL ends in `.css`, the origin actually served a public CSS file, failing to validate the `Content-Type`.

## Engineering Perspective
- **Defensive Architecture:** Cache configurations must factor in the `Content-Type` header returned by the origin, not rely solely on the URL extension.
- **Secure Coding:** Origin servers must strictly enforce routing. A request for `/api/profile/x.js` should return a `404 Not Found`, not gracefully degrade to the `/api/profile` endpoint.

## Security Engineering Notes
- **Cache-Control Headers:** Ensure all sensitive endpoints explicitly return `Cache-Control: private, no-store, must-revalidate`.
- **Vary Headers:** Use `Vary: Cookie` or `Vary: Authorization` so caches separate entries based on the user session.
- **API Gateway Hardening:** Ensure your API Gateway strictly drops requests with file extensions targeting dynamic endpoints.

## Detection Opportunities
- **Log Indicators:** Monitor origin access logs for an unusually high volume of `404` or `200` requests to sensitive API endpoints appended with static extensions (`/api/settings/styles.css`).
- **Telemetry:** Alert on caching of endpoints explicitly defined as dynamic in the OpenAPI spec.

## Related Vulnerabilities
- **Web Cache Poisoning:** WCD steals user data (attacker accesses victim's cache); Web Cache Poisoning serves malicious payloads (victim accesses attacker's cached payload).
- **HTTP Request Smuggling:** Often relies on similar proxy-vs-origin parsing discrepancies.

## Interview Insights
- **Common Question:** "What is the difference between Web Cache Deception and Web Cache Poisoning?"
  - *Answer:* Deception tricks the cache into saving the *victim's* sensitive data so the attacker can read it. Poisoning tricks the cache into saving the *attacker's* malicious payload (like XSS) so it's served to victims.
- **Architecture Tradeoff:** Balancing CDN performance (caching everything static) versus security (ensuring no dynamic data is accidentally cached).

## Project Connections
- **Sentinel Security Platform:** Uses strict `Cache-Control` headers for all dashboard routes to prevent SOC telemetry from lingering in intermediate caches.

## References
- [PortSwigger: Web Cache Deception](https://portswigger.net/web-security/web-cache-deception)
- [MDN: HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [RFC 7234 - HTTP/1.1 Caching](https://datatracker.ietf.org/doc/html/rfc7234)
""",

    "JWT/README.md": """# JSON Web Token (JWT) Security

## Overview
JWTs are the industry standard for stateless authentication. However, their security relies entirely on the integrity of the cryptographic signature. Implementation flaws in libraries, or misconfigurations in backend validation logic, frequently lead to critical authentication bypasses and vertical privilege escalation.

## Vulnerability Deep Dives: Alg Confusion & 'None' Alg

### 1. Algorithm Confusion (RS256 to HS256)
The JWT specification requires the header to dictate the signing algorithm (e.g., `alg: RS256`). When a server expects an asymmetric RS256 signature but fails to enforce it, an attacker can alter the header to `HS256` and sign the token using the application's public key as the HMAC secret.

### 2. The 'None' Algorithm (CVE-2015-9256)
If the backend doesn't explicitly reject tokens with the `none` algorithm, an attacker can submit an unsigned token that the server parses as valid.

## Real-World Usage
- **Where it appears:** Microservice architectures where authentication is handled by an API Gateway, but backend services also parse the JWT independently.
- **Commonly affected systems:** Custom OAuth implementations or applications using outdated JWT libraries (pre-2016).
- **Why developers introduce it:** Using generic `jwt.verify(token, key)` methods without explicitly passing the `algorithms: ['RS256']` options object.
- **Architectural Causes:** Decoupling the token issuance (Auth service) from token verification (Resource service) without strict cryptographic agreements.

## Where I Used / Observed This Concept
- **Sentinel Security Platform:** Architected the multi-tenant auth system. I implemented strict RS256 algorithm enforcement in Fastify and managed key rotation.
- **CTF Exploit Chains:** Successfully executed an RS256 to HS256 algorithm confusion attack by leveraging an SSRF to leak the public key from an internal `.well-known/jwks.json` endpoint.

## Attacker Mindset
- **What they look for:** Public key exposure (e.g., JKWS endpoints). Once obtained, attackers modify the JWT header, elevate their payload role to `"admin"`, and attempt to forge the signature.
- **Trust Boundaries:** The core failure is trusting client-supplied metadata (the JWT header) to dictate the cryptographic verification process.
- **Exploitation Goals:** Complete account takeover and vertical privilege escalation.

## Engineering Perspective
- **Secure System Design:** The algorithm must be decided by the server's configuration, not the token. Keys must be handled securely, ensuring symmetric verification logic is entirely separated from asymmetric logic.
- **Defensive Architecture:** Treat the token payload as strictly untrusted until the signature is cryptographically verified against a hardcoded algorithm list.

## Security Engineering Notes
- **Token Storage:** To prevent XSS exfiltration, store short-lived JWTs in memory, and opaque refresh tokens in `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
- **Key Rotation:** Implement automated rotation for JWT signing keys using JWKS.
- **Auth Middleware Validation:** Ensure middleware drops tokens immediately if the `kid` (Key ID) header points to an external or unauthorized domain.

## Detection Opportunities
- **Telemetry:** Monitor for JWTs submitted with `alg: none` or algorithms mismatched with the endpoint's expectation. Alert if a user attempts to change their `"role"` claim in the token payload.
- **SIEM Detection Ideas:** Alert on anomalous `kid` headers trying to trigger directory traversal (e.g., `../../../public.key`).

## Related Vulnerabilities
- **SSRF:** Often chained to leak the public/private keys needed for JWT forgery.
- **Insecure Direct Object Reference (IDOR):** Bypassing JWT auth leads directly to IDOR and lateral movement.

## Interview Insights
- **Discussion Point:** "Why are JWTs stateless, and how do you invalidate them?"
  - *Answer:* They cannot be natively invalidated before expiration. You must implement a token blocklist (via Redis) or rely on short-lived access tokens paired with revocable refresh tokens.
- **Architecture Tradeoff:** The performance benefit of stateless JWT validation versus the security control of stateful database sessions.

## Project Connections
- **Sentinel Security Platform:** Implements JWT auth with an opaque refresh token strategy, storing tokens in secure cookies and utilizing Redis for immediate session revocation, mitigating authentication abuse risks.

## References
- [RFC 7519 — JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
- [OWASP: JSON Web Token Cheat Sheet for Java](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Auth0: JWT Algorithm Confusion](https://auth0.com/blog/critical-vulnerabilities-in-json-web-token-libraries/)
""",

    "SSRF/README.md": """# Server-Side Request Forgery (SSRF)

## Overview
Server-Side Request Forgery (SSRF) allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain of the attacker's choosing. This vulnerability effectively turns the target server into a proxy, enabling attackers to pivot into internal corporate networks, bypass edge firewalls, and exfiltrate highly sensitive cloud metadata.

## Real-World Usage
- **Where it appears:** Webhooks, PDF generators, image fetchers/resizers, and link-preview features.
- **Commonly affected systems:** Applications hosted on AWS, GCP, or Azure that have misconfigured Instance Metadata Service (IMDS) protections.
- **Architectural Causes:** Passing user-supplied URLs directly to HTTP client libraries (like `axios` or `node-fetch`) without validation or DNS resolution checks.
- **Why developers introduce it:** Assuming internal network spaces (like `10.x.x.x` or `169.254.x.x`) are unreachable from public inputs without explicitly blocking them at the application layer.

## Where I Used / Observed This Concept
- **CTF Exploit Chain (SSRF -> JWT -> IDOR -> XXE -> RCE):** I utilized a webhook endpoint to trigger an SSRF, querying an internal metadata endpoint to leak a public key. This became the foundation for an entire exploit chain.
- **Sentinel Security Platform:** Implemented strict URL validation on the webhook integration module to prevent users from probing internal SOC infrastructure.

## Attacker Mindset
- **What they look for:** Any parameter named `url`, `endpoint`, `callback`, `api`, or `webhook`.
- **Exploitation Goals:** Map internal networks, exploit unauthenticated internal services (like Redis or Memcached), or exfiltrate cloud IAM credentials via `169.254.169.254`.
- **Evasion Tactics:** Using decimal IP encoding (`http://2130706433`), IPv6, or custom DNS rebinding domains to bypass naive regex filters.

## Engineering Perspective
- **Defensive Architecture:** SSRF is solved through network-level isolation (Zero Trust). Web servers should have egress traffic heavily restricted via security groups.
- **Secure Coding:** Never rely on regex to parse URLs. Resolve the DNS record of the user-supplied URL and verify the IP address does not fall within private/internal ranges (e.g., RFC 1918) *before* making the request.

## Security Engineering Notes
- **Cloud Hardening:** Always enforce IMDSv2 (AWS) which requires a specific PUT request and session token, effectively killing simple GET-based SSRF.
- **Network Segmentation:** Utilize dedicated, isolated proxy containers for fetching external resources, entirely segregated from the internal network.

## Detection Opportunities
- **Log Indicators:** Look for backend HTTP requests heading to `169.254.169.254`, `localhost`, or internal subnet IPs.
- **SIEM Rules:** Flag user-supplied URLs that contain IP encodings, `gopher://`, or `dict://` schemas.

## Related Vulnerabilities
- **XML External Entity (XXE):** Often utilized to achieve SSRF via XML parsers fetching external DTDs, leading to cloud metadata abuse.
- **Command Injection:** If the SSRF is executed via an unsafe `curl` or `wget` shell call.

## Interview Insights
- **Practical Question:** "How do you securely fetch an image from a user-provided URL?"
  - *Answer:* Resolve the domain, check the IP against internal blocklists, enforce HTTP/HTTPS only, restrict redirects, and use a heavily restricted egress proxy.
- **Cloud Context:** Be prepared to explain the difference between AWS IMDSv1 and IMDSv2, and how IMDSv2 mitigates SSRF via its token-based requirement.

## Project Connections
- **AI Guardian Engine:** When analyzing external links for phishing, the engine uses isolated sandboxes and headless browsers that are completely cut off from the internal host network to prevent SSRF pivoting.

## References
- [OWASP: Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [PortSwigger: SSRF](https://portswigger.net/web-security/ssrf)
- [AWS: Transition to IMDSv2](https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/)
""",

    "Access-Control/README.md": """# Access Control & IDOR

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
""",

    "API-Security/README.md": """# API Security & Architecture

## Overview
Modern web applications are heavily decentralized, relying on REST, GraphQL, and gRPC APIs. Securing these interfaces requires strict input validation, robust authentication, and meticulous control over data exposure, as APIs often bypass traditional web application firewalls.

## Core Concepts: Mass Assignment & Excessive Data Exposure
- **Mass Assignment:** When frameworks automatically bind incoming HTTP parameters to database objects. Attackers inject unauthorized fields (e.g., `"is_admin": true`).
- **Excessive Data Exposure:** When APIs return full database records, relying on the frontend UI to filter sensitive data.

## Real-World Usage
- **Where it appears:** Frameworks like Express, Spring Boot, or Ruby on Rails that offer "magic" data binding features.
- **Commonly affected systems:** Mobile backends and modern SPAs (React/Vue) where APIs are designed to be overly generic to support multiple views.
- **Architectural Causes:** Lack of strict Data Transfer Objects (DTOs) and failing to define explicit data serialization contracts between the backend and frontend.
- **Why developers introduce it:** Prioritizing rapid feature development by reusing the same database query for multiple different UI views, over-fetching data.

## Where I Used / Observed This Concept
- **Sentinel Security Platform:** Built the API layer utilizing Node.js and Fastify. I heavily utilized JSON Schema validation to explicitly reject any undocumented parameters, preventing mass assignment.
- **SecurePass Analyzer:** Designed the API to return strictly the entropy score and boolean exposure flags, never echoing back the user's input password in the response to prevent excessive data exposure and caching leaks.

## Attacker Mindset
- **What they look for:** API responses containing fields that aren't rendered in the UI (e.g., finding a `password_hash` or `role` in a profile response via Burp Suite).
- **Exploitation Goals:** Elevate privileges, modify internal accounting balances, or exfiltrate PII.
- **Evasion Tactics:** Utilizing GraphQL introspection to map hidden endpoints, or appending old API versions (e.g., `/api/v1/profile`) to bypass modern WAF rules (Shadow APIs).

## Engineering Perspective
- **Defensive Architecture:** Enforce strict request validation at the edge. Implement response serialization to guarantee that sensitive internal fields are stripped before JSON serialization occurs.
- **Secure Coding:** Never blindly pass `req.body` into an ORM update function (e.g., `User.update(req.body)`).

## Security Engineering Notes
- **API Gateway Hardening:** Terminate SSL, enforce global rate limits, and validate JWT structures at the API Gateway level before traffic reaches microservices.
- **Rate Limiting Strategies:** Implement sliding window rate limits backed by Redis, keyed by IP and User-ID, to mitigate credential stuffing and enumeration.

## Detection Opportunities
- **Log Indicators:** API requests containing undocumented JSON keys, or requests targeting deprecated API versions (`/v1/`, `/beta/`).
- **Telemetry:** Spikes in 400 Bad Request errors often indicate automated parameter fuzzing.

## Related Vulnerabilities
- **Business Logic Flaws:** Mass assignment is essentially a business logic bypass.
- **Insecure Direct Object Reference (IDOR / BOLA):** Often chained with API flaws.

## Interview Insights
- **Architecture Level Reasoning:** Be prepared to explain how to secure a public-facing API. Discuss rate limiting, WAFs, API gateways, strict schema validation, DTOs, and short-lived stateless authentication.
- **Tradeoff Analysis:** Discussing the flexibility of GraphQL vs the strictness and predictability of REST APIs.

## Project Connections
- **Sentinel Security Platform:** Employs Fastify's highly performant JSON schema validation to act as an internal firewall, strictly defining what data enters and exits the API boundaries.

## References
- [OWASP API Security Project](https://owasp.org/www-project-api-security/)
- [MDN: HTTP CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [REST API Security Essentials](https://restfulapi.net/security-essentials/)
""",

    "Methodology/README.md": """# Pentesting & Vulnerability Research Methodology

## The Attacker Mindset
Effective security research requires a systematic, analytical approach. Before firing automated payloads or scanners, the focus must be on deeply understanding the application's business logic, architectural patterns, and underlying technology stack.

## Real-World Usage
In industry, a scattergun approach (running automated scanners) yields low-value results. High-impact vulnerabilities (IDORs, Logic Flaws, Auth Bypasses) require a deep understanding of the application's unique business context. 
- **Where it appears:** Professional red team engagements, bug bounties, and internal security assessments.
- **Why developers introduce bugs here:** Developers test for the "happy path." Attackers explicitly test the "unhappy paths" and edge cases.

## Phase 1: Reconnaissance & Mapping
1. **Passive Recon:** Understand the target's external footprint (subdomains, open ports, historical data).
2. **Active Mapping:** Manually spider the application through a proxy (Burp Suite). Map every input vector, API endpoint, header, and parameter.
3. **Tech Stack Identification:** Analyze HTTP headers (`X-Powered-By`, `Server`), error messages, and frontend frameworks. Payload selection is heavily dependent on the stack (e.g., Node.js handles arrays in query parameters differently than PHP).

## Phase 2: Vulnerability Discovery Workflow
1. **Authentication & Authorization:** Test for session fixation, JWT weaknesses, IDORs, and Broken Access Control. This yields the highest impact.
2. **Input Validation:** Fuzz parameters for XSS, SQLi, SSRF, XXE, and Command Injection.
3. **Business Logic Flaws:** Analyze the application for race conditions, price manipulation, or bypasses in multi-step processes.
4. **Configuration & Infrastructure:** Inspect CORS policies, Security Headers, and Cache configurations.

## Where I Used This Concept
- **CTF Exploit Chains:** Applied this methodology to build complex chains. By mapping first, I identified a low-impact SSRF, which I later chained with a JWT vulnerability and an IDOR, culminating in an XXE to achieve RCE.

## Security Engineering Notes
- **Telemetry Collection:** As an engineer, understanding this methodology helps me design better logging. I know attackers will map APIs, so I ensure 404s and 403s generate actionable telemetry for the SOC.

## Detection Opportunities
- **Suspicious Behavior Patterns:** Look for user agents behaving like scanners (e.g., massive spikes in traffic rapidly iterating through payloads), or a single IP triggering multiple different rule categories in a short time frame.

## Interview Insights
- **Practical Question:** "How do you approach testing a new web application?"
  - *Answer:* Emphasize the reconnaissance phase. Mention mapping the attack surface, identifying user roles, testing access controls first, and then moving to input validation. Highlight the importance of understanding business logic over running tools.

## Project Connections
- **Sentinel Security Platform:** Built the heuristic intrusion detection engine around observing the very methodology attackers use to map environments.
- **AI Guardian Engine:** Applies risk scoring concepts similar to how a pentester scores the likelihood and impact of a vulnerability.

## References
- [OWASP Web Security Testing Guide (WSTG)](https://owasp.org/www-project-web-security-testing-guide/)
- [PTES (Penetration Testing Execution Standard)](http://www.pentest-standard.org/)
""",

    "Payloads/README.md": """# Context-Specific Payloads Vault

## Overview
A curated collection of context-specific payloads for testing various vulnerability classes. These are abstract, engineered examples used strictly for educational, research, and authorized testing purposes.

## Real-World Usage
Generic payloads rarely work in production environments due to WAFs (Web Application Firewalls) and context-specific sanitization. These payloads represent the *foundational* logic that must be encoded, mutated, and adapted based on the specific framework (Node.js vs Spring) and deployment architecture.

## Server-Side Request Forgery (SSRF)
Targeting internal services and bypassing naive filters.
- **Localhost Variations:**
  ```text
  http://127.0.0.1
  http://0.0.0.0
  http://localhost
  http://[::1]
  http://2130706433 (Decimal representation)
  http://0x7F000001 (Hex representation)
  ```
- **Cloud Metadata (AWS):**
  ```text
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
  ```

## XML External Entity (XXE)
- **Classic Local File Inclusion (LFI):**
  ```xml
  <?xml version="1.0" encoding="ISO-8859-1"?>
  <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
  <data>&xxe;</data>
  ```

## Cross-Site Scripting (XSS)
- **Polyglot Payload (Context-agnostic):**
  ```javascript
  javascript://%250Aalert(1)//"onclick=alert(1)//<svg/onload=alert(1)>
  ```

## JSON Web Tokens (JWT)
- **The 'None' Algorithm Header:**
  ```text
  eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0
  ```
  *(Decodes to: `{"alg":"none","typ":"JWT"}`)*

## SQL Injection (PostgreSQL Context)
- **Time-based Blind:** 
  ```sql
  1; SELECT pg_sleep(5)--
  ```

## Attacker Mindset
- **Exploitation Goals:** Attackers don't just use payloads; they test application reactions to specific payload segments to map out exactly what WAF or sanitization library is in place, then craft a payload to specifically evade it.

## Detection Opportunities
- **Logging Indicators:** Monitor logs for decoding errors or unusual character encodings. For instance, double-URL encoded characters often indicate an attempt to bypass frontend WAFs.

## Project Connections
- **AI Guardian Engine:** I utilized variations of these XSS and SQLi payloads to train the NLP heuristic detection engine to identify and flag malicious input structures.
- **SecurePass Analyzer:** Relates to credential security; observing SQL injection payloads underscores why password security and proper database hashing architectures are vital.

## References
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings)
- [SecLists](https://github.com/danielmiessler/SecLists)
""",

    "BurpSuite-Tips/README.md": """# Burp Suite Pro Workflow Optimization

## Overview
Efficient utilization of Burp Suite separates junior testers from experienced researchers. This section details workflows to minimize noise and maximize vulnerability discovery.

## Real-World Usage
In enterprise environments, web applications generate massive amounts of background noise (telemetry, analytics, polling). A professional engineer must configure Burp to filter this noise to identify the core business logic requests.

## Workflow Efficiency & Proxy Management
- **Target Scope:** Always configure the target scope strictly. Enable `Drop all out-of-scope requests` in the proxy settings. This keeps the HTTP history clean and reduces memory consumption.
- **Repeater Organization:** Name Repeater tabs logically (e.g., `IDOR - User Profile POST`, `SSRF - Webhook Update`).
- **Match and Replace Rules:** Utilize `Proxy -> Options -> Match and Replace` to automatically modify traffic on the fly (e.g., bypassing WAFs by injecting `X-Forwarded-For: 127.0.0.1`).

## Essential Extensions (BApp Store)
1. **Autorize:** Crucial for automating IDOR and BAC testing. Feed it a low-privileged session token, browse as an administrator, and Autorize will flag endpoints lacking privilege separation.
2. **JSON Web Token Attacker:** Automates signing, alg confusion, and none-algorithm attacks.
3. **Param Miner:** Essential for discovering hidden parameters leading to Web Cache Poisoning/Deception.

## Where I Used This Concept
- **CTF Exploit Chains:** Utilized the JSON Web Token Attacker to streamline RS256 to HS256 conversions, and heavily relied on Match and Replace rules to automate header injections during SSRF hunting.

## Engineering Perspective
- **Security Testing Pipelines:** Workflows learned in Burp Suite often translate directly to DAST (Dynamic Application Security Testing) pipeline configurations in CI/CD environments.

## Interview Insights
- **Common Question:** "How do you test for IDOR at scale?"
  - *Answer:* Explain the use of the Autorize extension in Burp Suite. You configure it with a lower-privileged user's cookies, navigate the application as an admin, and the extension automatically repeats every request with the lower-privileged token, flagging endpoints where the responses match.

## Project Connections
- **Sentinel Security Platform:** The telemetry patterns analyzed in Burp Suite directly influenced the anomaly detection logic built into Sentinel's intrusion detection engine.

## References
- [PortSwigger: Burp Suite Documentation](https://portswigger.net/burp/documentation)
- [OWASP ZAP (Alternative Proxy)](https://www.zaproxy.org/)
"""
}

def enrich_files():
    base_dir = r"c:\Users\Anant\OneDrive\Desktop\Appsec-Notes"
    
    for filepath, content in files.items():
        full_path = os.path.join(base_dir, filepath.replace('/', os.sep))
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
            
    print("Successfully enriched knowledge base files.")

if __name__ == "__main__":
    enrich_files()
