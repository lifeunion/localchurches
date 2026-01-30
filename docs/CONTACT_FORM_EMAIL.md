# Sending Contact Us Form Submissions to Email (on Render)

The Contact Us form (homepage and /contact/ page) can send submissions to an email address. You can set the **recipient(s)** in the Wagtail admin; delivery is configured via environment variables on Render.

---

## Option 1: Resend (recommended on Render)

The app already uses **Resend** when configured: no SMTP, just an API key.

### 1. Get a Resend API key

1. Sign up at [resend.com](https://resend.com).
2. In the dashboard: **API Keys** → **Create API Key**.
3. Copy the key (starts with `re_`).
4. (Optional) Add and verify a domain so you can send from `contact@yourdomain.com`. Until then you can use Resend’s sandbox domain (see step 3).

### 2. Set environment variables on Render

In your Render service: **Environment** → **Environment Variables**. Add:

| Variable | Value | Required |
|----------|--------|----------|
| `RESEND_API_KEY` | Your Resend API key (e.g. `re_xxxx`) | Yes |
| `RESEND_FROM_EMAIL` | Sender address (e.g. `onboarding@resend.dev` for sandbox, or `contact@yourdomain.com` after verifying a domain) | Yes |

Resend’s sandbox allows sending to your own email; for production you typically verify your domain and set `RESEND_FROM_EMAIL` to an address on that domain.

### 3. Set the recipient in Wagtail admin

1. **Wagtail Admin** → **Pages**.
2. Open the **Contact** page (e.g. under “Contact” or the page used for the contact form).
3. In the **Email** section:
   - **To address:** the address(es) that should receive submissions, e.g. `you@example.com` or `team@example.com, support@example.com` (comma-separated).
   - **From address:** optional; if blank, `RESEND_FROM_EMAIL` is used.
   - **Subject:** optional; default is “Contact form submission”.

Save the page. New submissions will be sent to the **To address** via Resend.

---

## Option 2: Django SMTP (e.g. SendGrid)

Production settings already support SendGrid SMTP. If you prefer SMTP instead of Resend:

### 1. Set environment variables on Render

| Variable | Value |
|----------|--------|
| `SENDGRID_USERNAME` | Your SendGrid username (often `apikey`) |
| `SENDGRID_PASSWORD` | Your SendGrid API key |

### 2. Set the recipient in Wagtail admin

Same as above: **Pages** → **Contact** → **Email** → **To address**. Optionally set **From address** and **Subject**.

When `RESEND_API_KEY` is **not** set, the app uses Django’s email backend (SendGrid SMTP when the variables above are set).

---

## Summary

| Goal | What to do |
|------|-------------|
| **Recipient address** | Wagtail Admin → Pages → Contact → **Email** → **To address** (or use a predetermined address there). |
| **Send via Resend** | Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` on Render; ensure **To address** is set on the Contact page. |
| **Send via SendGrid SMTP** | Set `SENDGRID_USERNAME` and `SENDGRID_PASSWORD` on Render; leave `RESEND_API_KEY` unset; set **To address** on the Contact page. |

The `resend` package is already in `requirements.txt`. No code changes are required; configure env vars and the Contact page in admin.
