# 🛡️ API Security Architecture & Research Notes

*Author: Anant | GitHub: [anant720](https://github.com/anant720)*

---

## 📌 Overview
In modern decentralized architectures, APIs form the connective tissue between frontend clients (React/Vite), backend services (Node.js/Express), and third-party integrations (Razorpay, Google Gemini). Because APIs bypass traditional web application firewalls and directly expose backend business logic, they are the primary target for attackers.

This document serves as my personal engineering notebook, detailing how I analyze API vulnerabilities from an offensive perspective and engineer resilient, secure systems to defend against them.

---

## 🏗️ Real-World Engineering Context (My Projects)

Security is not theoretical. Here is how I apply API security principles across my production-grade applications:

### 1. [Peblo-AI-Notes](https://github.com/anant720/Peblo-AI-Notes) (Next.js, NextAuth, Upstash, Gemini 2.0)
- **Rate Limiting:** APIs powering AI models (like Gemini) are highly susceptible to cost-exhaustion (Denial of Wallet) attacks. I integrated **Upstash Redis** to enforce strict sliding-window rate limits on the AI generation endpoints.
- **Authentication:** Utilized **NextAuth** to securely manage stateless sessions, ensuring that action-item generation endpoints cryptographically verify the user's identity before processing requests.

### 2. [GigFlow](https://github.com/anant720/GigFlow) (React, Node.js, Express, MongoDB, Razorpay)
- **Payment Security:** Integrating Razorpay required exposing public webhook endpoints. To prevent attackers from spoofing "payment successful" events, I implemented strict **HMAC-SHA256 signature verification** on the webhook payloads.
- **Input Validation:** Enforced strict schema validation on the Express API routes to prevent Mass Assignment attacks when freelancers update their portfolios or clients post new gigs.

### 3. [AI-GUARDIAN](https://github.com/anant720/AI-GUARDIAN) & Sentinel Security Platform
- **Zero Trust Routing:** Designed the API layer to drop unexpected JSON keys silently, preventing NoSQL injection and prototype pollution before it hits the database engine in my AI-powered scam detection systems.

---

## 🚨 Core Vulnerabilities & Defensive Strategies

### 1. Broken Object Level Authorization (BOLA / IDOR)
**The Flaw:** The API fails to validate if the authenticated user has the explicit right to access the specific requested resource ID.
**Attacker Mindset:** I look for sequential IDs (`/api/gigs/1055`) and simply increment them (`/api/gigs/1056`) using a standard user's session token.
**Engineering Defense ([GigFlow implementation](https://github.com/anant720/GigFlow)):**
- Never trust the client-provided ID alone.
- *Insecure:* `Gig.findById(req.params.id)`
- *Secure:* `Gig.findOne({ _id: req.params.id, clientId: req.user.id })`
- Use cryptographically random UUIDv4s to mitigate enumeration.

### 2. Mass Assignment (Auto-Binding)
**The Flaw:** Modern frameworks (like Express or Spring) easily bind incoming JSON payloads directly to database objects.
**Attacker Mindset:** If I intercept a profile update request (`PUT /api/user/profile`), I will append hidden fields like `{"role": "admin", "wallet_balance": 9999, "isVerified": true}`. If the backend uses a generic update function, it will save these fields.
**Engineering Defense:**
- Implement strict Data Transfer Objects (DTOs).
- Use validation libraries (like Zod or Joi) to strip unknown keys.
```javascript
// GigFlow Safe Update Pattern
const safeData = {
    bio: req.body.bio,
    skills: req.body.skills
};
// 'role' and 'balance' are implicitly ignored
await User.findByIdAndUpdate(req.user.id, safeData);
```

### 3. Excessive Data Exposure
**The Flaw:** The API returns the entire database row, relying on the frontend (React/Vite) to filter what the user sees.
**Attacker Mindset:** I ignore the web UI and intercept the raw JSON response in Burp Suite. I look for exposed password hashes, reset tokens, or internal notes (e.g., finding hidden admin comments on a GigFlow proposal).
**Engineering Defense:**
- Implement strict response serialization.
- GraphQL APIs are particularly vulnerable to this if field-level authorization isn't strictly defined.

### 4. API Exhaustion & Rate Limiting Failures
**The Flaw:** APIs lacking rate limits can be brute-forced for passwords, OTPs, or used to rack up massive cloud bills (Denial of Wallet).
**Engineering Defense ([Peblo-AI-Notes implementation](https://github.com/anant720/Peblo-AI-Notes)):**
- Standard IP-based rate limiting is insufficient due to distributed botnets.
- Implement token-bucket or sliding-window rate limiting in a fast, in-memory store like **Upstash Redis**.
- Limit by `IP Address` for unauthenticated routes (login/signup), and limit by `User ID` for authenticated routes (AI generation).

### 5. Webhook & Third-Party API Spoofing
**The Flaw:** Applications rely on external APIs (like Razorpay/Stripe) to confirm state changes (e.g., successful payment), but fail to verify the origin of the webhook.
**Attacker Mindset:** If I find the webhook endpoint (`/api/payments/webhook`), I will send a forged POST request claiming my transaction was successful.
**Engineering Defense ([GigFlow implementation](https://github.com/anant720/GigFlow)):**
- Webhooks must verify the cryptographic signature sent in the headers (e.g., `X-Razorpay-Signature`).
```javascript
// Validating Razorpay Signature
const crypto = require('crypto');
const expectedSignature = crypto.createHmac('sha256', process.env.RAZORPAY_WEBHOOK_SECRET)
                                .update(JSON.stringify(req.body))
                                .digest('hex');

if (req.headers['x-razorpay-signature'] !== expectedSignature) {
    throw new Error('Invalid signature. Potential spoofing attack.');
}
```

---

## 🛠️ Security Engineering Architecture

When designing a new API, I adhere to these core principles:
1. **API Gateway Termination:** Terminate SSL, enforce global rate limits, and validate the structural integrity of JWTs at the edge before traffic ever touches the Node.js backend.
2. **Fail Closed:** If an authorization check encounters an error (e.g., Redis is down, DB connection fails), the API must return `500 Internal Server Error` or `403 Forbidden`, never defaulting to granting access.
3. **Stateless but Revocable:** While JWTs are stateless, I utilize Redis to maintain a blocklist of compromised or logged-out token IDs (JTI) to enable immediate session termination.
4. **CORS Configuration:** Explicitly define `Access-Control-Allow-Origin`. Never use wildcards (`*`) on authenticated endpoints.

---

## 🎤 Interview Insights

**Q: How do you secure a public-facing API that handles payments?**
*A:* Security must be layered (Defense in Depth). 
1. **Edge Layer:** WAF to block common injection payloads and Upstash Redis rate limiting to prevent brute force.
2. **Auth Layer:** Secure, short-lived JWTs stored in HttpOnly cookies (to prevent XSS exfiltration).
3. **Application Layer:** Strict Zod/Joi schema validation to prevent Mass Assignment and NoSQL injection.
4. **Logic Layer:** Verifying authorization (IDOR checks) for every database interaction.
5. **Integration Layer:** Cryptographically verifying all incoming webhooks (e.g., Razorpay HMAC signatures) to prevent state spoofing.

---

## 🔗 References & My Repository Implementations
- **My Rate Limiting & Auth implementation:** [Peblo-AI-Notes Source Code](https://github.com/anant720/Peblo-AI-Notes)
- **My Payment Webhook Security & Schema Validation:** [GigFlow Source Code](https://github.com/anant720/GigFlow)
- **My AI Sandbox Analysis:** [AI-GUARDIAN Source Code](https://github.com/anant720/AI-GUARDIAN)
- [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [Upstash Redis Rate Limiting](https://upstash.com/docs/redis/overall/getstarted)
- [NextAuth Security Documentation](https://next-auth.js.org/configuration/options#security)
- [Razorpay Webhook Verification](https://razorpay.com/docs/webhooks/validate-test/)