# Manual Database Migration (Heroku → Render)

**Use this if migration during Render deploy never works.** Render's build servers often cannot reach Heroku Postgres, so we run the migration from your machine instead.

---

## 1. Install PostgreSQL client tools

**macOS (Homebrew):**
```bash
brew install libpq
brew link --force libpq
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-client
```

---

## 2. Get connection strings

### Heroku

- **Heroku Dashboard** → Your app → **Settings** → **Reveal Config Vars** → `DATABASE_URL`
- Or: `heroku config:get DATABASE_URL -a YOUR_APP_NAME`

### Render (external URL)

- **Render Dashboard** → Your **Postgres** service (e.g. `localchurches_db_opmg`)
- Open **Connect** / **Info** → copy **External Database URL** (not Internal)
- If you use “Restrict access by IP”, add your current IP in **Networking** / **Allow IP**

---

## 3. Run the migration script

```bash
cd /path/to/localchurches

export HEROKU_DATABASE_URL='postgres://user:pass@host:port/dbname'
export RENDER_DATABASE_URL='postgresql://user:pass@host:port/dbname'

./migrate_manual.sh
```

The script will:

1. **Dump** Heroku (full schema + data) to a temp file  
2. Ask you to **confirm** (it will wipe the Render DB)  
3. **Drop** the `public` schema on Render and recreate it  
4. **Restore** the Heroku dump into Render  

---

## 4. After migration

1. **Redeploy** your Render web service (or trigger a new deploy).
2. Open **https://localchurches.onrender.com/diagnostic/** and confirm:
   - HomePage instances > 0  
   - Root page type = `lampstands.homepage`  
3. Optionally **remove** `HEROKU_DATABASE_URL` from Render env vars.

---

## Troubleshooting

| Problem | What to do |
|--------|------------|
| `pg_dump` / `psql` not found | Install Postgres client tools (step 1). On macOS, ensure `libpq` is on your `PATH` after `brew link --force libpq`. |
| Connection refused to Heroku | Check `HEROKU_DATABASE_URL`, VPN, and firewall. |
| Connection refused to Render | Use the **External** URL, and add your IP in the DB’s **Networking** / **Allow IP** if enabled. |
| Dump file empty | Verify Heroku URL and that the DB has data. |
| Restore errors | Some notices are OK. If restore fails, check that you’re using the External Render URL and that the DB is not being used by another process. |

---

## Why manual migration?

- Render **build** runs in Render’s network; it often **cannot** connect to Heroku Postgres.
- Running `pg_dump` / `psql` **on your machine** uses your network, which can reach both Heroku and Render (when using the external URL and IP allowlist).
- A full dump + restore replaces the Render DB with a copy of Heroku’s, so you get all tables and data in one go.
