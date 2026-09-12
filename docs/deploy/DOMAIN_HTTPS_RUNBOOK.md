# Production Domain, DNS & HTTPS Runbook

This runbook guides operators through configuring DNS records, provisioning TLS certificates via Let's Encrypt / Certbot, setting up automatic certificate renewals, and configuring the production Nginx reverse proxy.

---

## 1. DNS Configuration

Configure DNS records with your registrar or DNS provider (Cloudflare, Route53, etc.) pointing to the static public IPv4/IPv6 address of your deployment host:

| Type | Name | Content / Target | TTL | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **A** | `bcai.example.com` | `203.0.113.10` (Your host IPv4) | 300s | Primary web & API endpoint |
| **AAAA** | `bcai.example.com` | `2001:db8::10` (Your host IPv6) | 300s | IPv6 endpoint (if available) |
| **CAA** | `bcai.example.com` | `0 issue "letsencrypt.org"` | 3600s | Certificate Authority Authorization |

Verify DNS propagation before attempting TLS issuance:
```bash
dig +short A bcai.example.com
```

---

## 2. Initial TLS Certificate Issuance (Certbot Standalone / Webroot)

On the production host (Ubuntu/Debian example):

### Step 1: Install Certbot
```bash
sudo apt-get update
sudo apt-get install -y certbot
```

### Step 2: Issue Certificate via Webroot or Standalone
If Nginx is not yet running on port 80:
```bash
sudo certbot certonly \
  --standalone \
  --preferred-challenges http \
  --agree-tos \
  --no-eff-email \
  -m admin@example.com \
  -d bcai.example.com
```

Certificates will be saved to:
- Full chain: `/etc/letsencrypt/live/bcai.example.com/fullchain.pem`
- Private key: `/etc/letsencrypt/live/bcai.example.com/privkey.pem`

---

## 3. Nginx Production Configuration

Generate the active configuration from `deploy/nginx.production.conf.template`:

```bash
sed -e 's|\${SERVER_NAME}|bcai.example.com|g' \
    -e 's|\${SSL_CERT_PATH}|/etc/letsencrypt/live/bcai.example.com/fullchain.pem|g' \
    -e 's|\${SSL_KEY_PATH}|/etc/letsencrypt/live/bcai.example.com/privkey.pem|g' \
    deploy/nginx.production.conf.template > deploy/nginx.production.conf
```

Validate Nginx syntax inside the web container:
```bash
docker compose -f docker-compose.production.yml exec web nginx -t
```

Reload Nginx:
```bash
docker compose -f docker-compose.production.yml exec web nginx -s reload
```

---

## 4. Automated Certificate Renewal Cron

Let's Encrypt certificates expire every 90 days. Configure an automated renewal cron job:

```bash
# Open crontab
sudo crontab -e

# Add renewal entry checking twice daily, reloading the Nginx container upon renewal
0 3,15 * * * certbot renew --post-hook "docker compose -f /opt/breast-cancer-ai/docker-compose.production.yml exec -T web nginx -s reload" >> /var/log/certbot_renew.log 2>&1
```

Test the renewal flow in dry-run mode:
```bash
sudo certbot renew --dry-run
```

---

## 5. Security Verification

After deploying, verify your HTTPS configuration using external tools:
1. **SSL Labs**: Check for **A+** grade at `https://www.ssllabs.com/ssltest/analyze.html?d=bcai.example.com`
2. **Security Headers**: Inspect security headers via curl:
   ```bash
   curl -I https://bcai.example.com
   ```
   Confirm presence of:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
   - `X-Frame-Options: SAMEORIGIN`
   - `X-Content-Type-Options: nosniff`
   - `Content-Security-Policy: ...`
   - `Server` banner is suppressed (no Nginx version leak).
