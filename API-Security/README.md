# API Security & Architecture

## Overview
Modern web applications are heavily decentralized, relying on REST, GraphQL, and gRPC APIs. Securing these interfaces requires strict input validation, robust authentication, and meticulous control over data exposure, as APIs often bypass traditional web application firewalls.

## Core Concepts: Mass Assignment & Excessive Data Exposure
- **Mass Assignment:** When frameworks automatically bind incoming HTTP parameters to database objects. Attackers inject unauthorized fields (e.g., `"is_admin": true`).
- **Excessive Data Exposure:** When APIs return full database records, relying on the frontend UI to filter sensitive data.

## Real-World Usage
- **Where it appears:** Frameworks like Express, Spring Boot, or Ruby on Rails that offer "magic" data binding features.
- **Commonly affected systems:** Mobile backends and modern SPAs (React/Vue) where APIs are designed to be overly generic to support multiple views.
- **Architectural Causes:** Lack of strict Data Transfer Objects (DTOs) and failing to define explicit data serialization contracts between the backend and frontend.
- **Why developers introduce it:** Prioritizing rapid feature development by reusing the same database query for multiple different UI views, over-fetching data.

## Where I Used / Observed This Concept
- **Sentinel Security Platform:** Built the API layer utilizing Node.js and Fastify. I heavily utilized JSON Schema validation to explicitly reject any undocumented parameters, preventing mass assignment.
- **SecurePass Analyzer:** Designed the API to return strictly the entropy score and boolean exposure flags, never echoing back the user's input password in the response to prevent excessive data exposure and caching leaks.

## Attacker Mindset
- **What they look for:** API responses containing fields that aren't rendered in the UI (e.g., finding a `password_hash` or `role` in a profile response via Burp Suite).
- **Exploitation Goals:** Elevate privileges, modify internal accounting balances, or exfiltrate PII.
- **Evasion Tactics:** Utilizing GraphQL introspection to map hidden endpoints, or appending old API versions (e.g., `/api/v1/profile`) to bypass modern WAF rules (Shadow APIs).

## Engineering Perspective
- **Defensive Architecture:** Enforce strict request validation at the edge. Implement response serialization to guarantee that sensitive internal fields are stripped before JSON serialization occurs.
- **Secure Coding:** Never blindly pass `req.body` into an ORM update function (e.g., `User.update(req.body)`).

## Security Engineering Notes
- **API Gateway Hardening:** Terminate SSL, enforce global rate limits, and validate JWT structures at the API Gateway level before traffic reaches microservices.
- **Rate Limiting Strategies:** Implement sliding window rate limits backed by Redis, keyed by IP and User-ID, to mitigate credential stuffing and enumeration.

## Detection Opportunities
- **Log Indicators:** API requests containing undocumented JSON keys, or requests targeting deprecated API versions (`/v1/`, `/beta/`).
- **Telemetry:** Spikes in 400 Bad Request errors often indicate automated parameter fuzzing.

## Related Vulnerabilities
- **Business Logic Flaws:** Mass assignment is essentially a business logic bypass.
- **Insecure Direct Object Reference (IDOR / BOLA):** Often chained with API flaws.

## Interview Insights
- **Architecture Level Reasoning:** Be prepared to explain how to secure a public-facing API. Discuss rate limiting, WAFs, API gateways, strict schema validation, DTOs, and short-lived stateless authentication.
- **Tradeoff Analysis:** Discussing the flexibility of GraphQL vs the strictness and predictability of REST APIs.

## Project Connections
- **Sentinel Security Platform:** Employs Fastify's highly performant JSON schema validation to act as an internal firewall, strictly defining what data enters and exits the API boundaries.

## References
- [OWASP API Security Project](https://owasp.org/www-project-api-security/)
- [MDN: HTTP CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [REST API Security Essentials](https://restfulapi.net/security-essentials/)