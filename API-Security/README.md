# API Security & Architecture

## Overview
Modern web applications are heavily decentralized, relying on REST, GraphQL, and gRPC APIs. Securing these interfaces requires strict input validation, robust authentication, and meticulous control over data exposure, as APIs often bypass traditional web application firewalls.

## Key Vulnerability Patterns

### 1. Mass Assignment (Auto-Binding)
- **Context:** Many modern frameworks (like Spring Boot or Express) allow developers to automatically bind incoming HTTP request parameters directly to backend database objects.
- **The Attack:** An attacker intercepts a legitimate request (like a profile update) and injects unauthorized fields, such as `{"is_admin": true}` or `{"wallet_balance": 9999}`.
- **Mitigation:** Implement strict Data Transfer Objects (DTOs) and allowlists. Never blindly map user input to internal models.

### 2. Excessive Data Exposure
- **Context:** Developers often build generic APIs that return full database records (e.g., `SELECT * FROM users`), relying on the frontend client (React/Vue) to filter out sensitive data before rendering.
- **The Attack:** An attacker intercepts the raw API JSON response using Burp Suite and extracts hidden fields like `ssn`, `password_hash`, or `internal_notes`.
- **Mitigation:** Implement strict response serialization at the backend. Only transmit the exact fields required by the UI component.

### 3. Improper Assets Management (Shadow APIs)
- **Context:** Outdated API versions (e.g., `/api/v1/`) are left operational alongside newer versions (`/api/v2/`) for backward compatibility, but lack the security patches applied to the newer infrastructure.
- **The Attack:** Bypassing WAFs, rate limits, or enhanced authorization checks by targeting the deprecated v1 endpoints.

## Engineering Context: Secure API Design
In building microservices with Node.js and Fastify, I enforce defense-in-depth API security:
1. **Schema Validation:** Utilizing libraries like `Ajv` or `Zod` to strictly validate the structure, type, and length of all incoming request bodies, headers, and query parameters before they reach business logic.
2. **Rate Limiting Architecture:** Implementing granular rate limiting backed by Redis. Different endpoints have different limits (e.g., `/login` allows 5 req/min, `/search` allows 100 req/min) to prevent brute-forcing and API exhaustion.