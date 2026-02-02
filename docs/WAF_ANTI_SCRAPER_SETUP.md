# Step-by-Step: AWS WAF Setup for CloudFront to Prevent Scrapers/Bots

This guide provides a comprehensive, step-by-step approach to setting up AWS WAF on your CloudFront distribution (serving the `lcstatic` S3 bucket) to prevent scrapers, bots, and automated data harvesting.

---

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ **CloudFront distribution** already created and serving your S3 bucket (`lcstatic`)
- ✅ **Distribution ID** (starts with `E`) - find it via:
  ```bash
  aws cloudfront list-distributions \
    --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName]" \
    --output table
  ```
- ✅ **AWS Console access** with permissions for:
  - `wafv2:*` (or at minimum: `CreateWebACL`, `GetWebACL`, `AssociateWebACL`, `ListResourcesForWebACL`)
  - `cloudfront:GetDistribution`, `cloudfront:UpdateDistribution`
- ✅ **CloudFront distribution URL** (e.g., `https://d24pmr7604s8mt.cloudfront.net`)

> **Important:** WAF must be created in **US East (N. Virginia) / `us-east-1`** region for CloudFront distributions.

---

## SEO and Good Bots: Will This Affect Google / Search?

**Yes, it can.** If your WAF blocks or heavily challenges **all** bots, it will block search engine crawlers (Googlebot, Bingbot, etc.). That leads to:

- Pages not being indexed or re-crawled
- Drops in search visibility and traffic

**What to do:** Allow verified search engine crawlers and only block bad bots/scrapers.

- **Add an Allow rule first** (see below) so requests with known good crawler user-agents are **allowed** before any block rules run.
- **AWS Managed Bot Control** classifies bots; use **Count** at first and review which labels are “Verified search engine” or “Legitimate” so you don’t block them when you switch to Block.
- **Rule 5** in this doc blocks user-agents containing `crawler`; that can catch some legitimate crawlers. Either keep that rule in **Count** only, or add the “Allow good crawlers” rule below and place it **above** the block rules so good bots are never blocked.

---

## Step 1: Access AWS WAF Console

1. **Log in to AWS Console**
   - Go to: https://console.aws.amazon.com/
   - Ensure you're in the correct AWS account

2. **Navigate to WAF & Shield**
   - Click **Services** → Search for **"WAF"** → Select **"WAF & Shield"**
   - **OR** direct link: https://console.aws.amazon.com/wafv2/

3. **Select Correct Region**
   - In the top-right corner, ensure the region dropdown shows:
     - **"Global (CloudFront)"** ← **This is required for CloudFront**
   - If you see a regular region (e.g., "US East (N. Virginia)"), click it and select **"Global (CloudFront)"**

---

## Step 2: Create Web ACL

1. **Click "Create web ACL"** button (top right)

2. **Step 2.1: Specify web ACL details**
   - **Name:** `lcstatic-anti-scraper-waf` (or your preferred name)
   - **Description:** `WAF for lcstatic CloudFront to prevent scrapers and bots`
   - **CloudWatch metric name:** Auto-filled (or customize: `lcstaticAntiScraperWAF`)
   - **Resource type:** Select **"CloudFront distributions"** ← **Critical: Must be CloudFront**
   - **Click "Next"**

3. **Step 2.2: Associate AWS resources**
   - **Leave empty for now** - we'll attach the distribution in Step 6
   - **Click "Next"**

---

## Step 3: Add Rules - Anti-Bot Protection

### Rule 0: Allow Search Engine Crawlers (SEO – add this first)

Add this rule **first** so it is evaluated before any block rules. Requests that match are **allowed** and never blocked by later rules.

1. **Click "Add rules"** → **"Add my own rules and rule groups"** → **"Rule"**
2. **Configure:**
   - **Name:** `allow-search-engine-crawlers`
   - **Type:** **"Regular rule"**
   - **Statement:** **"Or"** (match any of the following):
     - **Statement 1:** Single header → `user-agent` → **Starts with string** → `Googlebot`
     - **Statement 2:** Single header → `user-agent` → **Starts with string** → `Bingbot`
     - **Statement 3:** Single header → `user-agent` → **Starts with string** → `Slurp` (Yahoo)
     - **Statement 4:** Single header → `user-agent` → **Contains string** → `Googlebot`
     - (Add more as needed for other verified crawlers.)
   - **Action:** **"Allow"**
3. **Click "Add rule"**, then **move this rule to the top** of the rule list (highest priority) in the Web ACL.

> **Result:** Googlebot, Bingbot, and other listed crawlers are always allowed; your WAF will not hurt SEO for these crawlers. Block rules below still apply to scrapers and other bots.

### Rule 1: AWS Managed Bot Control Rule (Recommended)

1. **Click "Add rules"** → **"Add managed rule groups"**

2. **Select "AWSManagedRulesBotControlRuleSet"**
   - ✅ Check the box for **"AWSManagedRulesBotControlRuleSet"**
   - **Rule action:** Select **"Count"** initially (we'll switch to Block after testing)
   - **Click "Add rule"**

   > **What this does:** Detects and blocks common bots, scrapers, and automated tools based on behavioral patterns, user-agent analysis, and request characteristics.

### Rule 2: AWS Managed IP Reputation List

1. **Still in "Add managed rule groups"**

2. **Select "AWSManagedRulesAmazonIpReputationList"**
   - ✅ Check the box
   - **Rule action:** **"Count"** initially
   - **Click "Add rule"**

   > **What this does:** Blocks requests from IP addresses known for hosting malicious bots, scrapers, or being part of botnets.

### Rule 3: AWS Managed Common Rule Set

1. **Still in "Add managed rule groups"**

2. **Select "AWSManagedRulesCommonRuleSet"**
   - ✅ Check the box
   - **Rule action:** **"Count"** initially
   - **Click "Add rule"**

   > **What this does:** Protects against common web exploits (SQL injection, XSS, etc.) that scrapers might use.

### Rule 4: Rate-Based Rule (Critical for Scraper Prevention)

1. **Click "Add rules"** → **"Add my own rules and rule groups"** → **"Rate-based rule"**

2. **Configure rate limit:**
   - **Name:** `lcstatic-rate-limit-anti-scraper`
   - **Rate limit:** `1000` requests per 5 minutes per IP
     - **Adjust based on your traffic:**
       - **Conservative (strict):** 500 requests/5min
       - **Moderate:** 1000 requests/5min (recommended starting point)
       - **Lenient:** 2000 requests/5min
   - **IP address to use for rate limiting:** Select **"Source IP address"**
   - **Scope-down statement:** Leave empty (applies to all requests)
   - **Action:** Select **"Count"** initially
   - **Click "Add rule"**

   > **What this does:** Limits how many requests a single IP can make within a time window. Scrapers typically make hundreds/thousands of requests quickly, so this catches them.

### Rule 5: Custom Rule - Block Common Scraper User-Agents

1. **Click "Add rules"** → **"Add my own rules and rule groups"** → **"Rule"**

2. **Configure rule:**
   - **Name:** `block-scraper-user-agents`
   - **Type:** **"Regular rule"**
   - **Statement:** 
     - **Inspect:** Select **"Single header"**
     - **Header field name:** `user-agent`
     - **Match type:** **"Contains string"**
     - **String to match:** Add these one by one (click "+" to add more):
       - `scrapy`
       - `curl`
       - `wget`
       - `python-requests`
       - `go-http-client`
       - `java/`
       - `apache-httpclient`
       - `okhttp`
       - `scraper`
       - `crawler`
   - **Action:** **"Count"** initially
   - **Click "Add rule"**

   > **Note:** This is aggressive and may block legitimate tools. Consider making this more specific or using it in "Count" mode only for monitoring.

### Rule 6: Custom Rule - Block Requests Without User-Agent

1. **Click "Add rules"** → **"Add my own rules and rule groups"** → **"Rule"**

2. **Configure rule:**
   - **Name:** `block-no-user-agent`
   - **Type:** **"Regular rule"**
   - **Statement:**
     - **Inspect:** Select **"Single header"**
     - **Header field name:** `user-agent`
     - **Match type:** **"Does not exist"**
   - **Action:** **"Block"** (safe to block - legitimate browsers always send User-Agent)
   - **Click "Add rule"**

### Rule 7: Custom Rule - Block Requests with Suspicious Headers

1. **Click "Add rules"** → **"Add my own rules and rule groups"** → **"Rule"**

2. **Configure rule:**
   - **Name:** `block-suspicious-headers`
   - **Type:** **"Regular rule"**
   - **Statement:** Use **"And statement"** (combine multiple conditions):
     - **Condition 1:**
       - **Inspect:** **"Single header"**
       - **Header:** `x-forwarded-for`
       - **Match:** **"Does not exist"** (CloudFront should add this)
     - **Condition 2:** (Optional - only if you want to be very strict)
       - **Inspect:** **"Single header"**
       - **Header:** `accept`
       - **Match:** **"Does not contain"** → `text/html` (scrapers often don't request HTML)
   - **Action:** **"Count"** initially
   - **Click "Add rule"**

---

## Step 4: Configure Default Action

1. **Scroll to "Default web ACL action for requests that don't match any rules"**

2. **Select:** **"Allow"**
   - This means: if a request doesn't match any blocking rules, it's allowed through.
   - Rules with "Block" action will still block matching requests.

3. **Click "Next"**

---

## Step 5: Configure Request Sampling and Logging (Optional but Recommended)

1. **Request sampling:**
   - **Sampling rate:** `100` (sample 100% of requests for monitoring)
   - This helps you see what's being blocked/allowed

2. **CloudWatch metrics:**
   - ✅ **Enable CloudWatch metrics** (default: enabled)
   - This creates metrics you can monitor in CloudWatch

3. **Logging (Optional but Recommended):**
   - ✅ **Enable logging** if you want detailed logs
   - **Destination:** Choose:
     - **CloudWatch Logs** (easier, but costs more)
     - **S3 bucket** (cheaper for high volume)
   - If using S3, create a bucket first and grant WAF permissions

4. **Click "Next"**

---

## Step 6: Review and Create

1. **Review all settings:**
   - Web ACL name
   - Associated resources (should be empty for now)
   - Rules (should show all 7 rules you added)
   - Default action (Allow)
   - Sampling/logging settings

2. **Click "Create web ACL"**

3. **Note the Web ACL ARN** (shown in success message or details page)
   - Format: `arn:aws:wafv2:us-east-1:ACCOUNT_ID:global/webacl/lcstatic-anti-scraper-waf/WEBACL_ID`
   - **Copy this ARN** - you'll need it in the next step

---

## Step 7: Associate Web ACL with CloudFront Distribution

### Option A: Via CloudFront Console (Easiest)

1. **Go to CloudFront Console**
   - Navigate to: https://console.aws.amazon.com/cloudfront/
   - **OR** Services → CloudFront

2. **Select Your Distribution**
   - Find the distribution serving `lcstatic` (check origin domain)
   - Click on the **Distribution ID**

3. **Open Security Tab**
   - Click the **"Security"** tab

4. **Enable WAF**
   - Scroll to **"Web Application Firewall (WAF)"**
   - Click **"Edit"**
   - **Enable security protections:** ✅ Check the box
   - **Use existing WAF configuration:** Select your Web ACL name (`lcstatic-anti-scraper-waf`)
   - **Click "Save changes"**

5. **Wait for Propagation**
   - Status will show "In Progress" → "Deployed"
   - This can take **5-15 minutes**

### Option B: Via AWS CLI

```bash
# 1. Get current distribution config
aws cloudfront get-distribution-config \
  --id YOUR_DISTRIBUTION_ID > /tmp/cf-config.json

# 2. Extract ETag (needed for update)
ETAG=$(jq -r '.ETag' /tmp/cf-config.json)

# 3. Edit config: Add WebACLId to DistributionConfig
# Set DistributionConfig.WebACLId to your Web ACL ARN
# Remove "ETag" field from JSON (it's returned separately)

# Example edit (using jq):
jq '.DistributionConfig.WebACLId = "arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/lcstatic-anti-scraper-waf/ID"' \
  /tmp/cf-config.json | jq 'del(.ETag)' > /tmp/cf-config-updated.json

# 4. Update distribution
aws cloudfront update-distribution \
  --id YOUR_DISTRIBUTION_ID \
  --if-match "$ETAG" \
  --distribution-config file:///tmp/cf-config-updated.json
```

---

## Step 8: Monitor and Verify (Start in "Count" Mode)

### Initial Verification (Rules in "Count" Mode)

1. **Wait 5-15 minutes** for CloudFront changes to propagate

2. **Test Your Site**
   - Visit your CloudFront URL: `https://YOUR_DISTRIBUTION.cloudfront.net/static/css/villareal-turquoise.css`
   - Should load normally (rules are counting, not blocking yet)

3. **Check WAF Metrics**
   - Go to **WAF Console** → **Web ACLs** → Your ACL
   - Click **"Metrics"** tab
   - You should see:
     - **AllowedRequests** (should be high)
     - **CountedRequests** (rules in Count mode incrementing)
     - **BlockedRequests** (should be 0 if all rules are Count)

4. **View Sampled Requests**
   - Click **"Sampled requests"** tab
   - You'll see actual requests being evaluated
   - Check if rules are matching correctly

### Test Scraper Detection

1. **Simulate Scraper Behavior** (from a test machine):
   ```bash
   # Rapid requests (should trigger rate limit)
   for i in {1..100}; do
     curl -s https://YOUR_DISTRIBUTION.cloudfront.net/static/css/villareal-turquoise.css > /dev/null
   done
   
   # Request without User-Agent (should be blocked)
   curl -H "User-Agent:" https://YOUR_DISTRIBUTION.cloudfront.net/static/css/villareal-turquoise.css
   ```

2. **Check WAF Metrics Again**
   - **CountedRequests** should increase for rate-limit rule
   - **BlockedRequests** should increase for no-user-agent rule

---

## Step 9: Switch Rules from "Count" to "Block"

**After monitoring for 24-48 hours** and confirming no false positives:

### Switch Each Rule to Block Mode

1. **Go to WAF Console** → **Web ACLs** → Your ACL

2. **Click "Edit"** (top right)

3. **For each rule in "Count" mode:**
   - Click the rule name
   - Change **Action** from **"Count"** to **"Block"**
   - **Save**

4. **Rules to switch:**
   - ✅ **AWS Managed Bot Control** → **Block**
   - ✅ **AWS Managed IP Reputation** → **Block**
   - ✅ **Rate-based rule** → **Block** (when limit exceeded)
   - ✅ **Block scraper user-agents** → **Block** (if you want strict enforcement)
   - ✅ **Block suspicious headers** → **Block** (if configured)

5. **Rules already blocking:**
   - ✅ **Block no user-agent** (already set to Block)

6. **Click "Save"** at the bottom

---

## Step 10: Fine-Tune Rate Limits

### Adjust Based on Your Traffic Patterns

1. **Monitor WAF Metrics** for 1-2 weeks:
   - **CloudWatch** → **Metrics** → **AWS/WAFV2**
   - Look for:
     - **BlockedRequests** (should catch scrapers)
     - **AllowedRequests** (legitimate traffic)
     - **CountedRequests** (if any rules still in Count mode)

2. **Check for False Positives:**
   - If legitimate users are being blocked, increase rate limits
   - If scrapers are getting through, decrease rate limits

3. **Adjust Rate Limit:**
   - Go to your Web ACL → **Edit** → **Rate-based rule**
   - Modify **Rate limit** value:
     - **Too many false positives?** Increase (e.g., 1000 → 2000)
     - **Scrapers still getting through?** Decrease (e.g., 1000 → 500)

---

## Step 11: Enable WAF Logging (Optional but Recommended)

### For Detailed Analysis

1. **Create S3 Bucket for Logs** (if using S3):
   ```bash
   aws s3 mb s3://lcstatic-waf-logs --region us-east-1
   ```

2. **Set Bucket Policy** (grants WAF permission to write):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AWSLogDeliveryWrite",
         "Effect": "Allow",
         "Principal": {
           "Service": "delivery.logs.amazonaws.com"
         },
         "Action": "s3:PutObject",
         "Resource": "arn:aws:s3:::lcstatic-waf-logs/*",
         "Condition": {
           "StringEquals": {
             "s3:x-amz-acl": "bucket-owner-full-control"
           }
         }
       }
     ]
   }
   ```

3. **Enable Logging in WAF Console:**
   - Web ACL → **Logging and metrics** tab
   - **Enable logging** → Choose S3 bucket → **Save**

---

## Step 12: Monitor and Maintain

### Regular Monitoring Tasks

1. **Weekly Review:**
   - Check **WAF Metrics** for blocked requests
   - Review **Sampled requests** for patterns
   - Adjust rate limits if needed

2. **Monthly Review:**
   - Analyze **WAF logs** (if enabled) for:
     - New scraper patterns
     - False positives
     - Effectiveness of rules

3. **Update Rules as Needed:**
   - Add new user-agent patterns if scrapers evolve
   - Adjust rate limits based on traffic growth
   - Add custom rules for specific threats

---

## Cost Considerations

### WAF Pricing (as of 2024)

- **Web ACL:** $5/month per Web ACL
- **Requests:** $1.00 per million requests
- **Rules:** 
  - **Managed rule groups:** $1.00 per rule group per month
  - **Custom rules:** $1.00 per rule per month
- **Rate-based rules:** $1.00 per rule per month

### Estimated Monthly Cost (Example)

- 1 Web ACL: $5
- 3 Managed rule groups: $3
- 3 Custom rules: $3
- 1 Rate-based rule: $1
- 10 million requests: $10
- **Total:** ~$22/month (plus request costs)

---

## Troubleshooting

### Legitimate Users Being Blocked

1. **Check WAF Metrics** → **BlockedRequests**
2. **Review Sampled Requests** → Find blocked requests
3. **Identify rule** causing the block
4. **Options:**
   - Increase rate limit
   - Add exception rule for specific IPs
   - Switch rule from Block to Count

### Scrapers Still Getting Through

1. **Check if rate limit is too high**
2. **Review Bot Control rule** → Ensure it's set to Block
3. **Add more specific custom rules** for your use case
4. **Enable logging** to analyze scraper patterns

### WAF Not Attached to CloudFront

1. **Verify region:** WAF must be in **Global (CloudFront)** region
2. **Check CloudFront Security tab:** Ensure WAF is enabled
3. **Wait 15 minutes** for propagation

---

## Quick Reference: Key Settings Summary

| Setting | Recommended Value |
|---------|-------------------|
| **Region** | Global (CloudFront) / us-east-1 |
| **Rate Limit** | 1000 requests per 5 minutes per IP |
| **Bot Control** | Enabled (Block mode) |
| **IP Reputation** | Enabled (Block mode) |
| **Common Rule Set** | Enabled (Block mode) |
| **No User-Agent** | Block |
| **Default Action** | Allow |

---

## Next Steps

1. ✅ **Deploy and monitor** for 24-48 hours in Count mode
2. ✅ **Switch to Block mode** after verification
3. ✅ **Fine-tune rate limits** based on traffic
4. ✅ **Enable logging** for detailed analysis
5. ✅ **Regular monitoring** and rule updates

---

## Additional Resources

- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/)
- [CloudFront WAF Best Practices](https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-features.html)
- [WAF Pricing](https://aws.amazon.com/waf/pricing/)
- Related docs in this repo:
  - [CLOUDFRONT_WAF_AND_WARMING.md](CLOUDFRONT_WAF_AND_WARMING.md) - General WAF setup
  - [CLOUDFRONT_CACHE_INVALIDATION.md](CLOUDFRONT_CACHE_INVALIDATION.md) - Cache management

---

## Summary Checklist

- [ ] Created Web ACL in Global (CloudFront) region
- [ ] Added AWS Managed Bot Control rule
- [ ] Added AWS Managed IP Reputation rule
- [ ] Added AWS Managed Common Rule Set
- [ ] Created rate-based rule (1000 req/5min)
- [ ] Created custom rule to block no user-agent
- [ ] Created custom rules for scraper user-agents (optional)
- [ ] Set default action to Allow
- [ ] Associated Web ACL with CloudFront distribution
- [ ] Verified in Count mode for 24-48 hours
- [ ] Switched rules to Block mode
- [ ] Enabled logging (optional)
- [ ] Set up monitoring and alerts

---

**Last Updated:** 2025-01-26  
**Author:** AI Assistant  
**Status:** Ready for implementation
