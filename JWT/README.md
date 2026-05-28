# JSON Web Token (JWT) Security

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