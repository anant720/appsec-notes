# Pentesting & Vulnerability Research Methodology

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