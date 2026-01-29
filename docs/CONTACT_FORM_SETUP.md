# Contact Form Setup: reCAPTCHA + Resend

This guide gets https://localchurches.onrender.com/contact/ working: fixing the captcha "Invalid domain for site key" and sending submission emails via Resend (name, email, message).

---

## 1. Fix reCAPTCHA "Invalid domain for site key"

The error means your **reCAPTCHA site key** is not allowed for `localchurches.onrender.com`.

### What to do

1. Open **Google reCAPTCHA Admin**: https://www.google.com/recaptcha/admin  
2. Select the **site key** you use for `GOOGLE_RECAPTCHA_SITE_KEY` (or create one).
3. Under **Domains**, add:
   - `localchurches.onrender.com`
   - `www.localchurches.onrender.com` (if you use it)
   - `localhost` (for local testing)
4. Save.

Your Render env vars `GOOGLE_RECAPTCHA_SITE_KEY` and `GOOGLE_RECAPTCHA_SECRET_KEY` do not need to change; only the domain list in the reCAPTCHA admin must include the live domain.

---

## 2. Set up Resend for contact form emails

The contact form sends an email on each submission with: **Name**, **Email**, **Message**.

### 2.1 Create a Resend account and API key

1. Sign up: https://resend.com  
2. **API Keys**: https://resend.com/api-keys → **Create API Key**.  
3. Copy the key (starts with `re_`). You will set it as `RESEND_API_KEY` in Render.

### 2.2 Verify a domain (required for "From" address)

Resend only allows sending **from** addresses on domains you verify.

**Option A – Use Resend’s test address (quick test only)**  
- You can send **to** `onboarding@resend.dev` for testing.  
- For **from**, you still need a verified domain. Resend does not allow arbitrary from-addresses.

**Option B – Verify your own domain (recommended for production)**  
1. In Resend: **Domains** → **Add Domain** → e.g. `localchurches.com` (or the domain you use).  
2. Add the DNS records (MX, TXT, etc.) Resend shows.  
3. After verification, you can use e.g. `Contact <noreply@localchurches.com>` as `RESEND_FROM_EMAIL`.

**Option C – Use Resend’s sandbox domain (for quick tests)**  
- If Resend gives you a sandbox domain like `something@resend.dev`, you can use that as `RESEND_FROM_EMAIL` only if it’s explicitly allowed. Check the Resend dashboard for your allowed “from” addresses.  
- In most cases, verifying your own domain is required.

### 2.3 Set environment variables in Render

In **Render Dashboard** → your **localchurches** web service → **Environment**:

| Variable | Value | Notes |
|----------|-------|--------|
| `RESEND_API_KEY` | `re_xxxx...` | From https://resend.com/api-keys |
| `RESEND_FROM_EMAIL` | `Contact <noreply@yourdomain.com>` | Must be from a **verified** domain in Resend |

- Use the **exact** “from” address you are allowed to use in Resend (e.g. after verifying `yourdomain.com`).  
- Redeploy the service after changing env vars.

---

## 3. Contact form fields in Wagtail

For the email to show **Name**, **Email**, and **Message** clearly, the Contact page form in Wagtail should have three fields whose labels (or `clean_name`s) map as follows:

- **Name** – e.g. label `"Name"` or `"Your name"` → `name` / `your_name`  
- **Email** – e.g. label `"Email"` or `"Your email"` → `email` / `your_email`  
- **Message** – e.g. label `"Message"` or `"Your message"` → `message` / `your_message`  

The `send_mail` logic also matches other common names (`full_name`, `email_address`, `body`, `comment`, etc.), so small label changes usually still work.

In **Wagtail Admin** → **Pages** → **Contact** → **Form fields**, ensure you have three fields of the right types (e.g. single line, email, multiline) and that **To address** (and optionally **From address** and **Subject**) are set under the **Email** panel. **From** in Wagtail is only used when Resend is not configured; when `RESEND_API_KEY` and `RESEND_FROM_EMAIL` are set, Resend and `RESEND_FROM_EMAIL` are used.

---

## 4. Behaviour summary

| Situation | Behaviour |
|-----------|-----------|
| `RESEND_API_KEY` **and** `RESEND_FROM_EMAIL` set | Sends via **Resend** with body: Name, Email, Message. |
| `RESEND_API_KEY` or `RESEND_FROM_EMAIL` missing | Falls back to **Django email backend** (e.g. SendGrid if configured in production). |
| Resend send fails (e.g. bad from/domain) | Logs the error and falls back to Django `send_mail`. |

---

## 5. Checklist

- [ ] In **Google reCAPTCHA Admin**: add `localchurches.onrender.com` (and `www.` if used) to the site key’s domains.  
- [ ] **Resend**: create API key, verify a domain, decide the “from” address.  
- [ ] **Render** → **Environment**: set `RESEND_API_KEY` and `RESEND_FROM_EMAIL`.  
- [ ] **Wagtail** → Contact page: form fields for name, email, message; **To address** (and optionally subject/from) in the Email panel.  
- [ ] **Redeploy** the Render service after changing env vars.  
- [ ] Submit a test on https://localchurches.onrender.com/contact/ and confirm the email and that the captcha no longer shows “Invalid domain for site key”.

---

## 6. What you need to do (short)

1. **reCAPTCHA**: https://www.google.com/recaptcha/admin → your key → Domains → add `localchurches.onrender.com` → Save.  
2. **Resend**: Sign up → API Keys → create key; Domains → verify your domain.  
3. **Render**: `RESEND_API_KEY` = Resend API key; `RESEND_FROM_EMAIL` = e.g. `Contact <noreply@yourdomain.com>`.  
4. **Wagtail**: Contact page has name, email, message fields and a To address.  
5. **Redeploy** on Render and test the form.
