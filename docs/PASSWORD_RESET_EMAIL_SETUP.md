# Password Reset Email Setup Guide

This document describes how password reset email delivery is configured and tested in **Breast Health Studio**.

---

## 1. Operating Modes Overview

The application supports two email delivery modes via the `APP_MAIL_MODE` environment variable:

| Mode | `APP_MAIL_MODE` | Description |
| :--- | :--- | :--- |
| **Development (Default)** | `file` | Writes outgoing reset emails and tokens to the local file outbox (`backend/data/outbox/`). Does not send network emails. Safe for deterministic local testing. |
| **Production / Live Delivery** | `smtp` | Connects to an external SMTP server (e.g. Gmail SMTP, SendGrid, Amazon SES) using STARTTLS to deliver real emails to users' mailboxes. |

---

## 2. Development Mode (`APP_MAIL_MODE=file`)

By default, when `APP_MAIL_MODE=file`:
1. When a user requests a password reset on `http://localhost/forgot-password.html`, the backend creates an entry in `password_reset_tokens`.
2. A JSON record is written to `backend/data/outbox/reset_<token_prefix>_<timestamp>.json` containing the recipient email, token, expiration, and full rendered reset URL.
3. The API response in file mode includes the `reset_token` so local developers can immediately navigate to the reset page without checking filesystem logs.
4. The generated direct reset link format:
   ```text
   http://localhost/reset-password.html?token=<SECURE_TOKEN>&v=auth-v3
   ```

---

## 3. Real SMTP Delivery (`APP_MAIL_MODE=smtp`)

To send real emails to recipient mailboxes:

1. In `.env`, set:
   ```bash
   APP_MAIL_MODE=smtp
   APP_FRONTEND_URL=http://localhost
   
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-sender@gmail.com
   SMTP_PASSWORD=<GOOGLE_APP_PASSWORD>
   SMTP_FROM_EMAIL=your-sender@gmail.com
   SMTP_FROM_NAME=Breast Health Studio
   ```

   > [!IMPORTANT]
   > For Gmail SMTP, `SMTP_PASSWORD` **MUST** be a **Google App Password** (16 characters, generated from [Google Account Security > 2-Step Verification > App passwords](https://myaccount.google.com/apppasswords)), **NOT** your regular personal Google account password. Regular passwords will fail authentication.
   > 
   > Never commit `.env` or SMTP passwords to git!

2. Recreate the API container:
   ```bash
   docker compose up -d --force-recreate api
   ```

3. When a reset is requested:
   - The email is sent via STARTTLS to the recipient's address.
   - The API response returns only a safe generic message:
     `"If an account exists for this email, a password reset link has been sent."`
     (The `reset_token` is NOT returned in the API response in SMTP mode).
   - Account enumeration is prevented.

---

## 4. Troubleshooting & Safety

- **SMTP connection failure**:
  If the SMTP server refuses authentication or times out, the backend logs a secure server-side error with connection diagnostics, without leaking credentials or raw tracebacks to the frontend client. The client continues to see the safe generic message.
- **Token URL security**:
  The reset link contains a high-entropy URL-safe token with an expiration window (2 hours by default). Once used, the token is permanently invalidated in `password_reset_tokens` (`used_at IS NOT NULL`).
