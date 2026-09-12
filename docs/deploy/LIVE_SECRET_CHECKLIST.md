# Production Live Secrets & Credentials Checklist

This checklist guides the operator through configuring live production credentials in `.env` on the production host.

> [!CAUTION]
> **NEVER** commit live production secrets, private keys, or API credentials to Git or public repositories. This file outlines what must be configured securely on the production host itself.

---

## 1. Credentials Inventory

### 1.1 Core Production Settings
- [ ] **`APP_ENV`**: Must be set to `production`.
- [ ] **`APP_FRONTEND_URL`**: Canonical HTTPS URL (e.g. `https://bcai.hospital.org`). Must use `https://` with no trailing slash.
- [ ] **`APP_CORS_ORIGINS`**: Explicit comma-separated allowed origins (e.g. `https://bcai.hospital.org`). No wildcards (`*`) or `localhost`.
- [ ] **`APP_ENABLE_API_DOCS`**: Set to `false` to disable Swagger/ReDoc docs exposure.

### 1.2 Google Identity Services (GIS) OAuth
- [ ] In [Google Cloud Console](https://console.cloud.google.com/):
  - [ ] Configure OAuth Consent Screen (Internal or External, App Name, Support Email).
  - [ ] Create Credentials -> OAuth client ID -> **Web application**.
  - [ ] Under **Authorized JavaScript origins**, add your exact HTTPS origin:
    - `https://bcai.hospital.org`
  - [ ] Copy the generated **Client ID** (format: `123456789-abcdef.apps.googleusercontent.com`).
- [ ] In `.env`:
  - Set `GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com`.
  - Note: **No Client Secret is needed**. The GIS client-side flow verifies the ID token on the backend directly.

### 1.3 Transactional SMTP Email (Password Resets)
- [ ] In your transactional email provider (AWS SES, SendGrid, Postmark, Mailgun):
  - [ ] Verify sender domain (`hospital.org`) with SPF, DKIM, and DMARC DNS records.
  - [ ] Generate an SMTP API Key or SMTP credentials.
- [ ] In `.env`:
  - [ ] `APP_MAIL_MODE=smtp` (Mandatory in production; suppresses token output in responses).
  - [ ] `SMTP_HOST`: e.g. `smtp.sendgrid.net` or `email-smtp.us-east-1.amazonaws.com`.
  - [ ] `SMTP_PORT`: `587` (STARTTLS) or `465` (SSL).
  - [ ] `SMTP_USERNAME`: e.g. `apikey`.
  - [ ] `SMTP_PASSWORD`: Secret SMTP password or API token.
  - [ ] `SMTP_FROM_EMAIL`: Authorized sender address (e.g. `noreply@hospital.org`).
  - [ ] `SMTP_FROM_NAME`: Display name (e.g. `Breast Cancer AI Research Prototype`).
- [ ] Verify delivery via diagnostic test script:
  ```bash
  python3 scripts/test_smtp_delivery.py --send-to operator@hospital.org
  ```

### 1.4 Doctor Workspace Access Control
- [ ] Generate a high-entropy random invite code (minimum 24 characters):
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] In `.env`:
  - [ ] `DOCTOR_REGISTRATION_MODE=invite` (or `disabled` to close doctor registration entirely).
  - [ ] `DOCTOR_INVITE_CODE=<generated-token>`.
- [ ] Distribute the code confidentially to authorized medical investigators only.

### 1.5 AI Advisor / Clinical LLM (Optional)
- [ ] If using local heuristic advice (recommended for strict offline compliance):
  - [ ] `AI_ADVISOR_PROVIDER=local`
- [ ] If using cloud LLM:
  - [ ] `AI_ADVISOR_PROVIDER=gemini` and `GEMINI_API_KEY=<secret>`
  - [ ] Or `AI_ADVISOR_PROVIDER=openai` and `OPENAI_API_KEY=<secret>`

---

## 2. Environment Pre-Flight Verification

After populating `.env` on the target production server, execute the pre-flight validator:

```bash
python3 scripts/verify_deploy_environment.py --env-file .env
```

The script will confirm that:
- `APP_ENV=production` is active.
- CORS origins are HTTPS and non-wildcard.
- SMTP credentials and invite codes are non-placeholder.
- Returns exit code `0` on total compliance.
