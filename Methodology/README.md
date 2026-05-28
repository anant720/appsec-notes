# Pentesting & Vulnerability Research Methodology

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