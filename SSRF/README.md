# Server-Side Request Forgery (SSRF)

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