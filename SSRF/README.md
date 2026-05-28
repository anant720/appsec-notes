# Server-Side Request Forgery (SSRF)

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