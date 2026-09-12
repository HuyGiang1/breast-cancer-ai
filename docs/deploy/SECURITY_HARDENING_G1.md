# Phase G1 Pre-Deploy Security Hardening Summary

**Document Version**: 1.0.0  
**Phase**: Phase G1 — Pre-Deploy Hardening  
**Target Status**: `READY FOR LIVE INTEGRATION`  
**Date**: 2026-09-12

This document provides technical documentation of the security, privacy, and architectural hardening controls implemented during Phase G1.

---

## 1. Authentication & Cryptographic Storage Hardening

### 1.1 PBKDF2-HMAC-SHA256 Upgrade (OWASP Compliant)
- **Algorithm**: `PBKDF2-HMAC-SHA256`
- **Work Factor**: 600,000 iterations (conforms to OWASP Password Storage Guidelines).
- **Salt**: 16 bytes of cryptographically secure randomness generated via `os.urandom(16)`.
- **Digest Length**: 32 bytes (256 bits).
- **Format**: `pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>`
- **Benchmark Performance**: 129.32 ms per verification on 600,000 rounds. This is high enough to resist offline GPU brute-force attacks while maintaining fast sub-second interactive logins.

### 1.2 Backward Compatibility & Transparent Rehash Migration
- `backend/app/core/security.py` maintains backward compatibility for legacy 2-part `<salt>$<digest>` hashes (120,000 iterations).
- `needs_rehash(password_hash)` evaluates whether a stored hash is legacy format or below the current 600,000 iteration threshold.
- Upon successful login in `/auth/login/`, if `needs_rehash()` returns true, the hash is automatically recomputed with 600,000 rounds and updated in SQLite without user disruption.

### 1.3 Error Sanitization & Information Leakage Prevention
- Google OAuth endpoints (`/auth/google/`, `/auth/google/link/`) catch internal token verification exceptions and log them via `logger.error()`, returning generic user-facing error messages:
  - 401: `"Invalid or expired Google credential."`
  - 502: `"Google authentication could not be completed."`
- The `/auth/forgot-password/` endpoint never returns `reset_token` in production (`APP_MAIL_MODE=smtp` or `APP_ENV=production`), returning only a generic confirmation message.

---

## 2. API Security & Fail-Closed Controls

### 2.1 Fail-Closed CORS Configuration
- In production (`APP_ENV=production`), the application refuses to start if `APP_CORS_ORIGINS` is missing, empty, or set to `*`.
- Every configured CORS origin must use `https://` and cannot target `localhost` or `127.0.0.1`.
- CORS HTTP methods are restricted to `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`.
- CORS headers are restricted to `["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"]`.

### 2.2 API Documentation Lockdown
- Interactive Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI specification schema (`/openapi.json`) are disabled by default in production via `APP_ENABLE_API_DOCS=false`.

### 2.3 Health & Readiness Probes
- `/healthz`: Lightweight container liveness check.
- `/readyz`: Deep readiness probe verifying:
  - Database responsiveness (`SELECT 1` on SQLite).
  - ML runtime model health (`artifact_verified` and status).
  - DL runtime model health (`artifact_verified` and status).
  - Returns HTTP 503 if any subsystem is unavailable.

---

## 3. Database Reliability & High Availability

### 3.1 SQLite WAL Concurrency
- Configured `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = NORMAL`.
- Set `PRAGMA busy_timeout = 5000` on every connection.
- Set connection timeout to 30.0s.
- Eliminates `database is locked` operational errors under concurrent read/write workloads.

### 3.2 Online Hot Backup & Recovery
- Python SQLite Online Backup API (`source_conn.backup(dest_conn)`) runs without locking or downtime.
- Automated SHA-256 verification and `PRAGMA integrity_check`.
- Non-destructive test drill utility (`scripts/verify_database_restore.py`) for automated disaster recovery testing.

---

## 4. Production Nginx & Defense-in-Depth

### 4.1 Production Security Headers
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
- `Content-Security-Policy`: Explicit whitelist allowing only self, Google Fonts, and Google GIS OAuth scripts/iframes.

### 4.2 Rate Limiting & Access Restrictions
- Authentication endpoints: 5 requests/sec with burst 10 (`limit_req zone=auth_limit`).
- General API: 30 requests/sec with burst 50 (`limit_req zone=api_limit`).
- Block hidden files and directories (`location ~ /\. { deny all; }`).
- Client body limit: 20 MB max.
