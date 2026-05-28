# JSON Web Token (JWT) Security

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