# Heroku HTTPS/SSL Issue Diagnosis

## The Problem

**Error**: "localchurches.org doesn't support a secure connection with HTTPS"

This is **NOT related to static files**. This is a **Heroku SSL certificate/HTTPS configuration issue**.

---

## Why It's NOT Static Files

✅ **Static files are fine:**
- S3 URLs use HTTPS: `https://lcstatic.s3.amazonaws.com/css/villareal-turquoise.css`
- All static file URLs are properly using HTTPS
- No mixed content issues

❌ **The problem is:**
- Heroku app SSL certificate expired or not configured
- Domain not properly set up for HTTPS
- Heroku SSL endpoint not enabled

---

## Common Causes

### 1. **SSL Certificate Expired**
- Heroku's free SSL certificates expire
- Need to renew or upgrade to paid SSL

### 2. **SSL Endpoint Not Enabled**
- Heroku apps need SSL endpoint configured
- Free tier: Automatic SSL (may have limitations)
- Paid tier: Custom SSL certificates

### 3. **Domain Configuration Issue**
- Custom domain not properly configured
- DNS not pointing correctly
- Domain not verified in Heroku

### 4. **Browser/Incognito Mode**
- Some browsers are stricter in incognito mode
- May show warnings even if SSL is valid

---

## How to Fix

### Step 1: Check Heroku SSL Status

1. Go to **Heroku Dashboard** → Your app → **Settings**
2. Scroll to **Domains & SSL**
3. Check if SSL certificate is active/valid
4. Look for any warnings or errors

### Step 2: Verify Domain Configuration

**In Heroku Dashboard:**
- Check if `www.localchurches.org` is listed under "Domains"
- Verify DNS settings match Heroku's requirements
- Ensure domain is verified

### Step 3: Enable/Update SSL

**Option A: Automatic SSL (Free)**
- Heroku provides free SSL for apps
- Should be enabled automatically
- May need to wait for certificate provisioning

**Option B: Custom SSL (Paid)**
- If using custom domain, may need paid SSL
- Upload your SSL certificate
- Configure certificate chain

### Step 4: Check DNS Settings

Verify your DNS records point to Heroku:
```
CNAME www → your-app.herokuapp.com
```

Or if using root domain:
```
ALIAS @ → your-app.herokuapp.com
```

### Step 5: Force HTTPS Redirect

Your Django settings already have:
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

This is correct! The issue is at the Heroku/domain level, not Django.

---

## Quick Diagnostic Commands

```bash
# Check if HTTPS works
curl -I https://www.localchurches.org

# Check SSL certificate
openssl s_client -connect www.localchurches.org:443 -servername www.localchurches.org

# Check DNS
dig www.localchurches.org
```

---

## What to Check in Heroku

1. **Dashboard → Settings → Domains & SSL**
   - Is SSL certificate active?
   - Any expiration warnings?
   - Domain properly configured?

2. **Dashboard → Settings → Config Vars**
   - Check if any SSL-related vars are set
   - Verify domain configuration

3. **Heroku CLI** (if you have it):
   ```bash
   heroku certs --app your-app-name
   heroku domains --app your-app-name
   ```

---

## If SSL Certificate Expired

1. **Automatic SSL**: Heroku should auto-renew, but may take time
2. **Manual Renewal**: 
   - Go to Settings → Domains & SSL
   - Click "Renew" or "Provision SSL"
   - Wait for certificate to be issued

---

## If Domain Not Configured

1. **Add Domain in Heroku:**
   - Settings → Domains & SSL
   - Click "Add domain"
   - Enter `www.localchurches.org`
   - Follow DNS setup instructions

2. **Update DNS Records:**
   - Go to your domain registrar
   - Add CNAME record pointing to Heroku
   - Wait for DNS propagation (can take 24-48 hours)

---

## Temporary Workaround

If you need immediate access:
- Use `http://` instead of `https://` (not recommended for production)
- Or wait for SSL certificate to be provisioned/renewed

---

## Summary

**This is NOT a static files issue:**
- ✅ Static files use HTTPS correctly
- ✅ S3 URLs are HTTPS
- ✅ Django settings are correct

**This IS a Heroku SSL issue:**
- ❌ SSL certificate expired/not configured
- ❌ Domain not properly set up for HTTPS
- ❌ Heroku SSL endpoint issue

**Action needed:**
- Check Heroku Dashboard → Settings → Domains & SSL
- Verify SSL certificate status
- Renew/provision SSL if needed
