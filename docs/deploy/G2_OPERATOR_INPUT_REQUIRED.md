# Phase G2 Operator Staging Input Guide

This document lists the exact configuration parameters required from the operator to perform live staging integration and verification.

> [!CAUTION]
> **DO NOT PASTE SENSITIVE SECRETS INTO CHAT.**
> Sensitive credentials (such as `SMTP_PASSWORD`, `DOCTOR_INVITE_CODE`, or API keys) must **never** be transmitted in chat or committed to Git.
> Insert them directly into the `.env` file on the staging host as described below.

---

## 1. Safe Host Configuration Method

On the target staging host, initialize and restrict permissions on `.env` directly:

```bash
# 1. Copy production template
cp .env.production.example .env

# 2. Restrict file permissions so only root/appuser can read
chmod 600 .env

# 3. Edit directly on host
nano .env
```

Non-secret parameters (such as `STAGING_FQDN`, `GOOGLE_CLIENT_ID`, and `SMTP_HOST`) can be safely communicated in chat to allow deployment automation.

---

## 2. Parameter Matrix

| Variable / Parameter | Required / Optional | Where to Get It | What It Is Used For |
| :--- | :--- | :--- | :--- |
| **`STAGING_FQDN`** | **Required** | Domain Registrar / DNS Provider (e.g. Cloudflare, Route53, Namecheap). Point an `A` or `AAAA` record to the staging server public IP. | The fully-qualified domain name (e.g. `staging.breasthealth.org`) for Let's Encrypt TLS issuance, CORS fail-closed validation, and Nginx routing. |
| **Server SSH Access Target** | **Required** | Staging Host Provider (e.g. DigitalOcean, AWS EC2, Hetzner, GCP). Target host IP/hostname and SSH key/user. | Remote execution of Docker Compose, Certbot certificate issuance, and staging validation scripts. |
| **`GOOGLE_CLIENT_ID`** | **Required** (for Google Auth) | [Google Cloud Console](https://console.cloud.google.com/) -> APIs & Services -> Credentials -> Create Credentials -> **OAuth client ID** (Type: **Web application**). | Client-side Google Identity Services (GIS) One-Tap and Sign-In button verification on the staging domain. |
| **`SMTP_HOST`** | **Required** (for Email) | Transactional email provider (e.g. SendGrid, Amazon SES, Postmark, Mailgun, or self-hosted SMTP). | Outbound mail server hostname (e.g. `smtp.sendgrid.net`, `email-smtp.us-east-1.amazonaws.com`). |
| **`SMTP_PORT`** | **Required** (for Email) | SMTP Provider documentation. Standard values: `587` (STARTTLS) or `465` (SSL). | Port for outbound transactional email delivery. |
| **`SMTP_SECURITY`** | **Required** (for Email) | Match with port: `starttls` for port 587; `ssl` for port 465. | Transport layer encryption protocol for SMTP handshake. |
| **`SMTP_USERNAME`** | **Required** (for Email) | SMTP provider credential management. | Authenticated SMTP username or API key identifier. |
| **`SMTP_PASSWORD`** | **Required** (for Email) | SMTP provider secret management (**insert directly on server**). | Password or secret API key for SMTP delivery. |
| **`SMTP_FROM_EMAIL`** | **Required** (for Email) | Verified domain email address in your email provider (e.g. `noreply@staging.breasthealth.org`). | Sender address header on password reset and notification emails. |
| **`SMTP_FROM_NAME`** | Optional | Custom display string (default: `"Breast Health Studio"`). | Friendly sender name displayed in email client inbox. |
| **`DOCTOR_INVITE_CODE`** | Optional | Generate on server: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. Default is disabled. | Protects Doctor workspace account creation if testing doctor self-registration in staging. |
| **`AI_ADVISOR_PROVIDER`** | Optional | Set to `local` (default, zero keys required), or `gemini` / `openai`. | Provider for rule-based or LLM-assisted clinical guideline summaries. |
| **`GEMINI_API_KEY` / `OPENAI_API_KEY`** | Optional | Cloud LLM provider console (**insert directly on server** if used). | Only needed if `AI_ADVISOR_PROVIDER` is set to `gemini` or `openai`. |

---

## 3. Google Identity Services Setup Guide

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project (e.g., `Breast Health Studio Staging`).
3. Under **APIs & Services** > **OAuth consent screen**:
   - User Type: **External** (or Internal for Google Workspace organizations).
   - App Name: `Breast Health Studio Staging`.
   - User support email & developer contact email: Operator contact.
4. Under **APIs & Services** > **Credentials**:
   - Click **+ Create Credentials** > **OAuth client ID**.
   - Application type: **Web application**.
   - Name: `Breast Health Studio Staging Client`.
   - Under **Authorized JavaScript origins**, click **+ Add URI**:
     - Enter exact HTTPS staging URL: `https://<STAGING_FQDN>` (no trailing slash).
   - Note: **Do NOT configure Authorized redirect URIs**. The GIS popup/One-Tap library does not use redirect URIs.
5. Click **Create**.
6. Copy the **Client ID** (format: `1234567890-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`).
   - Note: **No Client Secret is needed**. The frontend GIS library transmits verified ID tokens to the backend.
7. Configure `GOOGLE_CLIENT_ID` in `.env`.

---

## 4. SMTP Provider-Neutral Setup Guide

1. Verify sender domain (SPF, DKIM, DMARC) in your transactional email provider.
2. Generate an SMTP credential or API key.
3. In `.env`:
   - For STARTTLS (Port 587):
     ```env
     APP_MAIL_MODE=smtp
     SMTP_HOST=smtp.yourprovider.com
     SMTP_PORT=587
     SMTP_SECURITY=starttls
     SMTP_USERNAME=your_username
     SMTP_PASSWORD=your_secret_password_inserted_directly
     SMTP_FROM_EMAIL=noreply@<STAGING_FQDN>
     ```
   - For SSL (Port 465):
     ```env
     APP_MAIL_MODE=smtp
     SMTP_HOST=smtp.yourprovider.com
     SMTP_PORT=465
     SMTP_SECURITY=ssl
     SMTP_USERNAME=your_username
     SMTP_PASSWORD=your_secret_password_inserted_directly
     SMTP_FROM_EMAIL=noreply@<STAGING_FQDN>
     ```
4. Verify connectivity without exposing passwords:
   ```bash
   python3 scripts/test_smtp_delivery.py --send-to operator@yourdomain.com
   ```
