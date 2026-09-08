# Google Identity Services (GIS) Setup Guide

This guide describes how to configure genuine Google Sign-In and account linking for **Breast Health Studio**.

---

## 1. Google Cloud Project Setup

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Select an existing project or click **New Project** (e.g., `breast-health-studio-dev`).
3. Ensure the project is active in your Google Cloud Console dashboard.

---

## 2. Configure Google Auth Platform / OAuth Consent Screen

1. In the navigation menu, go to **APIs & Services** > **OAuth consent screen** (or **Google Auth Platform**).
2. Choose **External** user type (unless using Google Workspace within an organization) and click **Create**.
3. **App Information**:
   - **App name**: `Breast Health Studio`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click **Save and Continue**.
5. **Scopes**: The default basic scopes (`openid`, `.../auth/userinfo.email`, `.../auth/userinfo.profile`) are automatically included. Click **Save and Continue**.

---

## 3. Audience / Test Users (Important for Development)

If your Google Cloud app publishing status is **Testing**:
1. Go to the **Test users** tab on the OAuth consent screen.
2. Click **+ ADD USERS**.
3. Add your personal Google email address (e.g. `yourname@gmail.com`).
4. Click **Save**.
> [!NOTE]
> Accounts not listed in **Test users** will receive an `access_denied` error (Error 403: org_internal / access_denied) until the app is published or the email is added as a test user.

---

## 4. Create OAuth Client ID

1. Navigate to **APIs & Services** > **Credentials**.
2. Click **+ CREATE CREDENTIALS** and select **OAuth client ID**.
3. In **Application type**, select **Web application**.
4. Set **Name**: e.g., `Breast Health Studio Web Client`.
5. Under **Authorized JavaScript origins**, click **+ ADD URI**:
   - For local development:
     ```text
     http://localhost
     ```
   - If running with standard port or alternate loopback:
     ```text
     http://127.0.0.1
     ```
   > [!IMPORTANT]
   > Do NOT include paths (e.g., do NOT put `http://localhost/login.html` or trailing slashes). GIS JavaScript origins only accept schema, hostname, and optional port.
   - For production environments later:
     ```text
     https://your-production-domain.com
     ```
6. Under **Authorized redirect URIs**: Leave empty (GIS button uses credential callback mode, not server-side authorization code redirect).
7. Click **CREATE**.
8. A modal will display your **Client ID** (format: `xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com`).
   *(Note: OAuth Client Secret is NOT required for GIS client-side token callback).*

---

## 5. Configure Application Environment

1. In your local repository root, edit `.env`:
   ```bash
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   ```
   > [!WARNING]
   > Never commit `.env` containing your real client ID to git. Ensure `.env` is listed in `.gitignore`.

2. Rebuild and recreate the Docker API container so Docker picks up the new environment variable:
   ```bash
   docker compose up -d --force-recreate api
   ```

---

## 6. Verify Configuration Endpoint

Check that the backend reports the configured client ID:
```bash
curl -s http://localhost/api/v1/auth/google/config/
```
Expected response:
```json
{"client_id":"your-client-id-here.apps.googleusercontent.com"}
```
If not configured or empty, it safely returns `{"client_id":null}`.

---

## 7. Test End-to-End Google Flows

1. Open `http://localhost/login.html` in your browser.
2. The **Continue with Google** button will be active.
3. Click **Continue with Google** and select your authorized test Gmail account.
4. **New user flow**: If the email does not exist yet, an account is created with `role=user`, linked in `oauth_accounts`, and an application session is created.
5. **Existing password account flow**: If an account already exists with that email but was created with a password, the system prevents auto-linking (HTTP 409) to prevent account hijacking. Sign in with your password first, navigate to **Profile**, and click **Connect Google** to safely link your account.
