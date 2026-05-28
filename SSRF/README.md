# 🌐 Server-Side Request Forgery (SSRF) Research Notes

*Author: Anant | GitHub: [anant720](https://github.com/anant720)*

---

## 📌 Overview
Server-Side Request Forgery (SSRF) occurs when an attacker can coerce the backend server into making HTTP requests to an arbitrary domain. Rather than attacking the application directly, SSRF uses the application as a proxy to pivot into internal corporate networks, bypass perimeter firewalls, and exfiltrate highly sensitive cloud metadata.

Because SSRF leverages the server's own trusted network position, it is one of the most critical vulnerabilities in modern cloud-native architectures.

---

## 🏗️ Real-World Engineering Context (My Projects)

In modern web applications, backend servers constantly fetch external resources. Here is how I manage SSRF risks in my own architectures:

### 1. [Sentinel Security Platform](https://github.com/anant720/Sentinel) (SOC Telemetry)
- **Threat Intel Fetching:** Sentinel frequently ingests telemetry and queries third-party threat intelligence APIs. If an attacker injects a malicious IP into a threat feed URL, the Node.js backend might query internal SOC infrastructure (like a local Elasticsearch or Redis instance). 
- **Defensive Engineering:** I implemented strict DNS resolution checks and an egress proxy pattern. The backend explicitly blocks any resolved IP that falls within RFC 1918 private IP ranges (`10.x.x.x`, `192.168.x.x`) before the HTTP client executes the request.

### 2. [GigFlow](https://github.com/anant720/GigFlow) (Freelance Marketplace)
- **Webhook Integration Risk:** If I were to allow clients to configure webhooks for "Job Completed" notifications, an attacker could set the webhook URL to `http://169.254.169.254/latest/meta-data/`.
- **Defensive Engineering:** Webhook dispatchers must be completely isolated from the primary VPC and prohibited from accessing cloud instance metadata.

### 3. [AI-GUARDIAN](https://github.com/anant720/AI-GUARDIAN) (Phishing Detection)
- **Sandbox Isolation:** When AI Guardian fetches an external scam link for NLP analysis, it is strictly sandboxed. Allowing the main application server to fetch the link directly would introduce a blind SSRF, enabling attackers to map internal Docker networks.

---

## 💥 The CTF Exploit Chain: SSRF to RCE
*Documenting an advanced, multi-stage exploit chain I executed during a CTF, utilizing SSRF as the critical foothold.*

```text
[ SSRF ] ──▶ [ JWT Alg Confusion ] ──▶ [ IDOR ] ──▶ [ XXE ] ──▶ [ RCE ]
```

1. **SSRF (The Foothold):** Identified a webhook testing endpoint vulnerable to SSRF. Bypassed simple regex filters using decimal IP encoding (`http://2130706433`). Coerced the server to query an internal metadata endpoint, successfully leaking a private/public RSA key pair intended for internal APIs.
2. **JWT Algorithm Confusion (Privilege Escalation):** Extracted the public key via the SSRF. Forged an administrator JWT by manipulating the header from `RS256` to `HS256`, forcing the backend to verify the signature symmetrically using the public key string as the HMAC secret.
3. **IDOR (Lateral Movement):** With administrative access, analyzed the user management API. Discovered an Insecure Direct Object Reference (IDOR) on an internal reporting feature by iterating sequential user IDs.
4. **XXE (File Exfiltration):** The reporting feature accepted XML input for custom formatting. Injected an Out-of-Band (OOB) XML External Entity payload to read the backend configuration files.
5. **RCE (System Compromise):** The extracted configuration files revealed a vulnerable deserialization endpoint, which was leveraged to achieve full Remote Code Execution.

---

## 🚨 Attacker Mindset & Evasion Tactics

- **What Attackers Look For:** Any parameter named `url`, `endpoint`, `callback`, `api`, `webhook`, `feed`, or `pdf_generator`.
- **Exploitation Goals:** 
  1. Map internal networks (port scanning via timing differences).
  2. Exploit unauthenticated internal services (Redis, Memcached, MongoDB).
  3. Exfiltrate Cloud IAM credentials via the Instance Metadata Service (IMDS).
- **Filter Evasion Tactics:** 
  - *Decimal IP:* `http://2130706433` (instead of 127.0.0.1)
  - *Hex IP:* `http://0x7F000001`
  - *DNS Rebinding:* Setting a custom domain's A record to `8.8.8.8` (to bypass the initial validation check), and then rapidly changing it to `127.0.0.1` right before the server actually fetches the resource (Time-of-Check to Time-of-Use flaw).

---

## 🛠️ Security Engineering Architecture (Defense in Depth)

### 1. Network Segmentation (Zero Trust)
SSRF is fundamentally a network issue. The application server should reside in a DMZ and its egress traffic must be heavily restricted via Security Groups or Kubernetes Network Policies.

### 2. DNS Resolution & Blocklisting
Never rely on regex to parse URLs. 
- *Secure Coding Pattern:* Extract the hostname, resolve the DNS record programmatically, verify the resulting IP address does not fall within private/internal ranges, and enforce HTTP/HTTPS schemas only. 

### 3. Enforce IMDSv2 (Cloud Hardening)
In AWS environments, IMDSv1 is vulnerable to simple GET-based SSRF. Always mandate **IMDSv2**, which requires a specific `PUT` request with a custom header to generate a session token, neutralizing standard SSRF attacks.

---

## 🎤 Interview Insights

**Q: How do you securely fetch an image from a user-provided URL in Node.js?**
*A:* I would not fetch it directly from the main application server. I would use a dedicated, highly restricted egress proxy (or serverless function) that has no access to the internal network or cloud metadata. I would programmatically resolve the domain, block private IPs (RFC 1918), disable HTTP redirects (to prevent the server from redirecting to localhost), and enforce a strict timeout.

---

## 🔗 References & My Repository Implementations
- **Strict Network Isolation & Threat Intel Fetching:** [Sentinel Security Platform](https://github.com/anant720/Sentinel)
- **Secure Webhook Integrations:** [GigFlow Source Code](https://github.com/anant720/GigFlow)
- **External Link Sandboxing:** [AI-GUARDIAN Source Code](https://github.com/anant720/AI-GUARDIAN)
- [OWASP: Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [AWS: Defense in Depth against SSRF & IMDSv2](https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/)
- [PortSwigger: SSRF Tutorial](https://portswigger.net/web-security/ssrf)