# Web Cache Deception (WCD)

## Overview
Web Cache Deception is a vulnerability where an attacker tricks a caching server (like a CDN, reverse proxy, or load balancer) into storing sensitive, user-specific content (such as a profile page, API response, or dashboard) which the attacker can subsequently access. This occurs due to discrepancies in how the cache server and the origin server parse and route the requested URI.

## Core Mechanism
The vulnerability manifests when three architectural conditions are met:
1. **Aggressive Edge Caching:** The edge server is configured to cache files based purely on static extensions (e.g., `.js`, `.css`, `.png`, `.jpg`).
2. **Permissive Origin Routing:** The origin server employs a routing mechanism that ignores unknown or trailing path extensions and resolves to the base endpoint (e.g., `/api/user/settings/nonexistent.css` maps to `/api/user/settings`).
3. **Session-Dependent Responses:** The origin server returns private data based on the authentication state (cookies, session tokens) of the requester.

## Real-World Usage
- **Where it appears:** Heavily utilized REST APIs sitting behind Cloudflare, Akamai, or AWS CloudFront.
- **Commonly affected systems:** SPAs (Single Page Applications) where routing is handled on the client-side, causing the backend to permissively return the `index.html` or base JSON response regardless of the URL path.
- **Why developers introduce it:** Misunderstanding the separation of concerns between edge caching rules (regex matching on `.js`/`.css`) and backend routing frameworks (like Express or Fastify ignoring trailing extensions).
- **Architectural Causes:** Monolithic architectures shifting to CDN-backed microservices without updating legacy routing fallbacks.

## Where I Used / Observed This Concept
- **PortSwigger Web Cache Deception Lab:** Exploited WCD to expose a victim's API key by manipulating path parameters and understanding cache rules via Param Miner.
- **Sentinel Security Platform:** While developing the telemetry API, I ensured our Nginx reverse proxy explicitly ignores path extensions for dynamic `/api/*` routes, preventing caching of sensitive SOC metrics.

## Attacker Mindset
- **What they look for:** Discrepancies between load balancers and backend servers. An attacker will append `.js`, `;x.css`, or `%0a.png` to sensitive endpoints and observe the `X-Cache` header for `HIT` or `MISS`.
- **Exploitation Goals:** Steal PII, API keys, CSRF tokens, or session identifiers that are embedded in the victim's cached page.
- **Trust Boundary Failures:** The cache implicitly trusts that if a URL ends in `.css`, the origin actually served a public CSS file, failing to validate the `Content-Type`.

## Engineering Perspective
- **Defensive Architecture:** Cache configurations must factor in the `Content-Type` header returned by the origin, not rely solely on the URL extension.
- **Secure Coding:** Origin servers must strictly enforce routing. A request for `/api/profile/x.js` should return a `404 Not Found`, not gracefully degrade to the `/api/profile` endpoint.

## Security Engineering Notes
- **Cache-Control Headers:** Ensure all sensitive endpoints explicitly return `Cache-Control: private, no-store, must-revalidate`.
- **Vary Headers:** Use `Vary: Cookie` or `Vary: Authorization` so caches separate entries based on the user session.
- **API Gateway Hardening:** Ensure your API Gateway strictly drops requests with file extensions targeting dynamic endpoints.

## Detection Opportunities
- **Log Indicators:** Monitor origin access logs for an unusually high volume of `404` or `200` requests to sensitive API endpoints appended with static extensions (`/api/settings/styles.css`).
- **Telemetry:** Alert on caching of endpoints explicitly defined as dynamic in the OpenAPI spec.

## Related Vulnerabilities
- **Web Cache Poisoning:** WCD steals user data (attacker accesses victim's cache); Web Cache Poisoning serves malicious payloads (victim accesses attacker's cached payload).
- **HTTP Request Smuggling:** Often relies on similar proxy-vs-origin parsing discrepancies.

## Interview Insights
- **Common Question:** "What is the difference between Web Cache Deception and Web Cache Poisoning?"
  - *Answer:* Deception tricks the cache into saving the *victim's* sensitive data so the attacker can read it. Poisoning tricks the cache into saving the *attacker's* malicious payload (like XSS) so it's served to victims.
- **Architecture Tradeoff:** Balancing CDN performance (caching everything static) versus security (ensuring no dynamic data is accidentally cached).

## Project Connections
- **Sentinel Security Platform:** Uses strict `Cache-Control` headers for all dashboard routes to prevent SOC telemetry from lingering in intermediate caches.

## References
- [PortSwigger: Web Cache Deception](https://portswigger.net/web-security/web-cache-deception)
- [MDN: HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [RFC 7234 - HTTP/1.1 Caching](https://datatracker.ietf.org/doc/html/rfc7234)