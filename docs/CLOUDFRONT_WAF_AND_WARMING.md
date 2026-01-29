# WAF and Cache Warming for CloudFront (lcstatic)

This guide covers (1) attaching AWS WAF to the CloudFront distribution that serves the `lcstatic` S3 bucket, and (2) warming CloudFront edge caches after deploy or invalidation so the first user request in each region is a cache hit.

---

## Part 1: WAF for CloudFront

### Prerequisites

- A **CloudFront distribution** whose origin is `lcstatic.s3.amazonaws.com` (e.g. `d24pmr7604s8mt.cloudfront.net`; see [FIX_HEROKU_CLOUDFRONT.md](FIX_HEROKU_CLOUDFRONT.md)).
- **Distribution ID** (starts with `E`):
  ```bash
  aws cloudfront list-distributions \
    --query "DistributionList.Items[?Origins.Items[0].DomainName=='lcstatic.s3.amazonaws.com'].[Id,DomainName]" \
    --output table
  ```
- **IAM**: `wafv2:*` (or at least `CreateWebACL`, `GetWebACL`, `AssociateWebACL`, `ListResourcesForWebACL`) and `cloudfront:GetDistribution`, `cloudfront:UpdateDistribution` (or use the WAF/CloudFront console with an equivalent role).

> **Note:** For WAF to protect static traffic, requests must go through CloudFront. [lampstands/settings/production.py](lampstands/settings/production.py) currently sets `STATIC_URL` to the S3 domain. To have WAF (and CloudFront caching) apply to static files, set `STATIC_URL` to your CloudFront distribution URL. That change is independent of attaching WAF.

---

### Step 1: Create a Web ACL (WAF console)

1. Open **AWS WAF & Shield** in **US East (N. Virginia) / `us-east-1`** (required for CloudFront).
   - Console: **AWS WAF & Shield** → **Web ACLs** → ensure region is **Global (CloudFront)** or **us-east-1**.

2. **Create Web ACL**:
   - **Name:** e.g. `lcstatic-cloudfront-waf`
   - **Description:** e.g. "WAF for lcstatic CloudFront"
   - **Resource type:** **CloudFront distributions**
   - **Associated AWS resources:** Leave empty; we attach in Step 4.

3. **Add rules** (start in **Count** so you can verify before blocking):
   - **AWS Managed – Common rule set** (`AWSManagedRulesCommonRuleSet`) – injection, XSS, etc.
   - **AWS Managed – Known bad inputs** (optional) – `AWSManagedRulesKnownBadInputsRuleSet`
   - **AWS Managed – IP reputation** (optional) – `AWSManagedRulesAmazonIpReputationList`
   - **Rate-based rule** (optional, recommended):
     - **Name:** e.g. `lcstatic-rate-limit`
     - **Rate limit:** e.g. `2000` requests per 5 minutes per IP
     - **Scope:** IP
     - **Action:** **Count** initially.

4. **Default web ACL action:** **Allow**.

5. **Create Web ACL**.

---

### Step 2: (Optional) Tune rule actions

- For a static-only origin, you can switch managed rules from **Count** to **Block** after checking logs for false positives.
- Keep the rate-based rule in **Count** at first; switch to **Block** when the limit is right for your traffic.

---

### Step 3: Note the Web ACL ARN

- In the Web ACL details, copy the **ARN** (e.g. `arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/lcstatic-cloudfront-waf/ID`). You need it when associating with CloudFront.

---

### Step 4: Associate the Web ACL with your CloudFront distribution

**Option A – CloudFront console**

1. **CloudFront** → **Distributions** → select the distribution for `lcstatic`.
2. Open the **Security** tab.
3. Under **Web Application Firewall (WAF)**:
   - **Edit** → **Enable security protections**
   - **Use existing WAF configuration** → choose `lcstatic-cloudfront-waf` (or your Web ACL name).
4. **Save changes**. Propagation can take several minutes.

**Option B – AWS CLI**

```bash
# Get current config and ETag
aws cloudfront get-distribution-config --id YOUR_DISTRIBUTION_ID > /tmp/cf-config.json

# Edit /tmp/cf-config.json: set DistributionConfig.WebACLId to your Web ACL ARN.
# Remove "ETag" from the JSON (it is returned separately).

# Apply (use the ETag from get-distribution-config)
aws cloudfront update-distribution --id YOUR_DISTRIBUTION_ID --if-match ETAG --distribution-config file:///tmp/cf-config.json
```

---

### Step 5: Verify and switch from Count to Block

1. **Verify:** Request your CloudFront URL (e.g. `https://d24pmr7604s8mt.cloudfront.net/wagtailadmin/css/core.css`). In **WAF** → **Web ACLs** → **Your ACL** → **Sampled requests**, confirm requests are evaluated and Count rules increment.
2. **Logging (optional):** Enable WAF logs to S3 or CloudWatch for troubleshooting.
3. **Block:** When satisfied, change the managed rules and rate-based rule from **Count** to **Block** as needed.

---

### WAF – Summary checklist

| Step | Action |
|------|--------|
| 1 | Create Web ACL in **us-east-1** with `AWSManagedRulesCommonRuleSet` (+ optional managed rules and rate-based rule), all in **Count** |
| 2 | Associate Web ACL with the lcstatic distribution via **Security** → **Enable security protections** → **Use existing WAF configuration** |
| 3 | Verify in Sampled requests / logs, then switch rules to **Block** as appropriate |

---

## Part 2: Cache warming

### One distribution, one URL; “per endpoint” = per edge location (POP)

- You have **one** CloudFront distribution and **one** public URL (e.g. `https://d24pmr7604s8mt.cloudfront.net`).
- There are **many edge locations (POPs)** behind that URL. You do **not** create one distribution per continent.
- The **first request** at a given POP is a **cache miss** (fetch from S3, then cached). POPs do **not** share cache.
- To avoid users in a region seeing that first miss, **send requests that are routed to that region’s POP(s)** — i.e. from machines in different geographies.

---

### Minimal: Post-deploy / post-invalidation warming from one place

Run [scripts/warm_cloudfront.sh](scripts/warm_cloudfront.sh) to `curl` a list of critical static URLs. This warms the POP(s) nearest to the machine (e.g. your laptop or a single Render/CI job).

**Get your CloudFront base URL**

- From `aws cloudfront list-distributions` (field `DomainName`), or [find_heroku_cloudfront.sh](find_heroku_cloudfront.sh) / [FIX_HEROKU_CLOUDFRONT.md](FIX_HEROKU_CLOUDFRONT.md). Example: `https://d24pmr7604s8mt.cloudfront.net`.

**Usage**

```bash
export CLOUDFRONT_STATIC_URL=https://d24pmr7604s8mt.cloudfront.net
./scripts/warm_cloudfront.sh
```

- Run **after** `collectstatic`/upload and **after** any CloudFront invalidation.
- This only warms the POP(s) for the region where the script runs.

---

### Better: Warm from multiple regions

To reduce first-request misses in **Americas, Europe, and Asia-Pacific**, run the same requests from **2–3 AWS regions** (e.g. `us-east-1`, `eu-west-1`, `ap-southeast-1`):

- **Lambda** in 2–3 regions, triggered by EventBridge or manually; use `urllib`/`requests` to GET each URL.
- **EC2 or ECS** in each region on a schedule or after deploy.
- **Third-party** HTTP checks from multiple geos.
- **AWS CloudFront Extensions** [Pre-warming](https://github.com/awslabs/aws-cloudfront-extensions) construct.

---

### Optional: Origin Shield

- **Origin Shield** adds a cache layer between all POPs and S3. It can reduce S3 fetches and make warming more effective.
- **CloudFront** → **Origins** → edit the `lcstatic` origin → **Origin Shield** → **Enable** (e.g. `us-east-1`). Extra cost applies.

---

### When to run warming

- **After deploy:** Once `collectstatic` has finished and, if you invalidate, **after** invalidation.
- **After targeted invalidations:** e.g. `/wagtailadmin/*` — warm those paths so the new objects are in cache before users request them.

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `CLOUDFRONT_DISTRIBUTION_ID` | Used by [invalidate_cloudfront.py](invalidate_cloudfront.py). Set in Render or locally for invalidation. |
| `CLOUDFRONT_STATIC_URL` | Base URL for the lcstatic CloudFront distribution (e.g. `https://d24pmr7604s8mt.cloudfront.net`). Used by [scripts/warm_cloudfront.sh](scripts/warm_cloudfront.sh) and, if you switch `STATIC_URL` to CloudFront, can align with it. |

---

## See also

- [CLOUDFRONT_CACHE_INVALIDATION.md](CLOUDFRONT_CACHE_INVALIDATION.md) – invalidation methods
- [FIX_HEROKU_CLOUDFRONT.md](FIX_HEROKU_CLOUDFRONT.md) – CloudFront domain and distribution ID
