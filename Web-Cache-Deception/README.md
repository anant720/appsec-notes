# Web Cache Deception (WCD)

## Overview
Web Cache Deception is a vulnerability where an attacker tricks a caching server (like a CDN, reverse proxy, or load balancer) into storing sensitive, user-specific content (such as a profile page, API response, or dashboard) which the attacker can subsequently access. This occurs due to discrepancies in how the cache server and the origin server parse and route the requested URI.

## Core Mechanism
The vulnerability manifests when three architectural conditions are met:
1. **Aggressive Edge Caching:** The edge server is configured to cache files based purely on static extensions (e.g., `.js`, `.css`, `.png`, `.jpg`).
2. **Permissive Origin Routing:** The origin server employs a routing mechanism that ignores unknown or trailing path extensions and resolves to the base endpoint (e.g., `/api/user/settings/nonexistent.css` maps to `/api/user/settings`).
3. **Session-Dependent Responses:** The origin server returns private data based on the authentication state (cookies, session tokens) of the requester.

## Attack Flow

```text
[ Attacker ]                               [ Victim ]
    │                                          │
    │ 1. Identifies permissive routing         │
    │    Target: /api/v1/profile               │
    │                                          │
    │ 2. Crafts malicious link                 │
    │    Link: /api/v1/profile/x.css           │
    │                                          │
    │ 3. Distributes link to Victim ───────────▶
    │                                          │ 4. Victim clicks link
    │                                          ▼
    │                                  [ CDN / Cache Node ]
    │                                          │
    │                                          │ 5. Cache miss. Forwards request
    │                                          │    (with Victim's cookies)
    │                                          ▼
    │                                  [ Origin Server ]
    │                                          │ 6. Ignores '/x.css'. 
    │                                          │    Returns Victim's private JSON
    │                                          │
    │                                  [ CDN / Cache Node ]
    │                                          │ 7. Sees '.css'. Caches response!
    │                                          │    Delivers to Victim.
    │                                          │
    │ 8. Requests cached file                  │
    │    GET /api/v1/profile/x.css             │
    ▼                                          │
[ CDN / Cache Node ] ◀─────────────────────────┘
    │
    │ 9. Cache HIT! Returns Victim's
    │    private JSON to Attacker
    ▼
[ Attacker ] (Data Exfiltrated)
```

## HTTP Request/Response Examples

**Victim's Request (Induced by Attacker):**
```http
GET /api/v1/profile/dummy.js HTTP/1.1
Host: target.com
Cookie: session_id=victim_secure_token
```

**Origin Response (Cached by CDN):**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=3600
X-Cache: MISS

{
  "user_id": 9942,
  "email": "victim@company.com",
  "pii": {
    "phone": "+1-555-0199",
    "credit_card_last4": "4242"
  }
}
```

## Lab Completion Notes: PortSwigger WCD
- **Objective:** Exploit WCD to expose a victim's API key.
- **Methodology:**
  1. Mapped cache behavior using Param Miner to identify cached extensions. Discovered `.js` was aggressively cached.
  2. Tested path mapping on `/my-account`. Found that `/my-account/test.js` loaded the account dashboard while maintaining a `200 OK` status.
  3. Delivered the payload `https://vulnerable.com/my-account/x.js` to the victim via a stored XSS/CSRF vector (or exploit server in the lab).
  4. Quickly polled `https://vulnerable.com/my-account/x.js` from my IP to retrieve the cached dashboard containing the API key.

## Defensive Engineering Insights
- **Strict Cache Keys:** Cache configurations must factor in the `Content-Type` header returned by the origin, not rely solely on the URL extension.
- **Cache-Control Headers:** Ensure all sensitive endpoints explicitly return `Cache-Control: private, no-store, must-revalidate`.
- **Strict Routing Enforcement:** Origin servers should return a `404 Not Found` for invalid paths instead of gracefully degrading to a base endpoint. Frameworks like Fastify should have `ignoreTrailingSlash` configured carefully.