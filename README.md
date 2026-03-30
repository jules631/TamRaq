# Tamarac FSC Connector

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jules631/TamRaq)

> Move client data from Tamarac into Salesforce Financial Services Cloud — no coding, no manual entry, no expensive middleware.

---

## The Problem in Plain English

Wealth management firms typically run **two separate systems that don't talk to each other**:

| System | What it does |
|---|---|
| **Tamarac** | Tracks client portfolios — households, accounts, positions, performance |
| **Salesforce FSC** | Manages client relationships — contacts, households, service activity |

Every time a new client is onboarded in Tamarac, someone has to **manually re-enter the same data** into Salesforce. That means:

- Advisors waste hours on copy-paste data entry
- Records go stale and out of sync
- Compliance teams can't trust the CRM reflects reality
- Reporting across both systems is unreliable

The people who feel this most are **operations staff and financial advisors** at small-to-mid-sized RIAs (Registered Investment Advisors) who can't justify a six-figure enterprise integration contract.

---

## What This Does

Tamarac FSC Connector is a **secure, multi-tenant web application** that lets your ops team:

1. **Upload a combined CSV export** from Tamarac (the kind you already get out of the system today)
2. **Watch in real time** as it syncs into your Salesforce FSC sandbox
3. **See exactly what worked, what was skipped, and what failed** — without any raw data stored on our servers

One upload. One sync. Your Salesforce CRM reflects your book of business.

```
Upload CSV  →  Parse & Validate  →  Sync Households
                                  →  Sync Contacts
                                  →  Link Relationships
                                  →  Sync Financial Accounts
                                  →  Sync Positions
                                  →  Done ✓
```

---

## Who This Is For

### Primary User: RIA Operations Manager
- Works at a wealth management firm with 50–500 advisors
- Responsible for keeping Salesforce FSC accurate
- Gets Tamarac data exports regularly (daily, weekly, or at onboarding)
- **Does not want to write code** — wants a button to push
- Currently doing this manually or not at all

### Secondary User: Salesforce Admin / IT
- Needs to configure the Salesforce connection once
- Wants assurance that sensitive data (PII, private keys) is handled securely
- Needs an audit trail of what synced and when

### Firm Profile
- Uses **Tamarac** as their portfolio management platform
- Uses **Salesforce Financial Services Cloud** as their CRM
- Has 1–10 tenants (firms or business units) who each need their own isolated configuration

---

## Why This Approach

### What we chose **not** to do

| Alternative | Why we rejected it |
|---|---|
| Real-time API sync | Tamarac doesn't offer a real-time webhook API accessible to most firms |
| Storing the CSV | PII storage creates compliance liability; we process in-memory and discard immediately |
| One-size config | Different firms have different Salesforce field mappings; multi-tenant design lets each firm own its config |
| All-or-nothing sync | A single bad record shouldn't kill 500 good ones; we continue on errors and report partial success |

### What makes this different
- **Zero PII stored** — the CSV is read into memory, processed, and discarded. No S3, no database rows, no logs with names or emails.
- **Duplicate-safe** — re-running the same file is safe. Existing records are updated, not duplicated. AccountContactRelations that already exist are silently skipped.
- **Live progress** — you can watch each stage complete in real time via Server-Sent Events. You don't have to wait and wonder.
- **Encrypted credentials** — your Salesforce private key is encrypted at rest using envelope encryption. The key never appears in logs.

---

## Key Features

### For Operations Users
- **Drag-and-drop CSV upload** — the same export format you already use
- **Live sync progress** with stage-by-stage status (Parsing → Households → Contacts → etc.)
- **Error table** showing which records failed and why (with record IDs hashed, never raw names)
- **Sync history** — full log of every run with success/failure counts

### For Salesforce Admins
- **Connection test** — verify your Salesforce credentials before running a sync
- **Auto-discovery** — the app reads your Salesforce org to show available Account Record Types and FinancialAccount lookup fields. You pick from a dropdown — no field API names to memorize.
- **Toggle positions** — enable or disable syncing of investment positions (Assets) per run

### For IT / Security
- Auth0-based authentication with JWT validation on every API call
- Per-tenant data isolation — no tenant can see another's configuration or run history
- Salesforce private keys encrypted with Fernet (AES-128-CBC) at rest; structure is ready to swap to AWS KMS or Azure Key Vault
- All error messages are sanitized before storage — only a SHA-256 hash of the record's external ID is stored, never the name or email

---

## Data Flow

```
User uploads CSV
      │
      ▼
API reads body into memory (never written to disk or DB)
      │
      ▼
Parse & deduplicate rows by external ID
      │
      ▼
┌─────────────────────────────────────────────────┐
│              Salesforce FSC Sandbox              │
│                                                  │
│  Upsert Accounts (Household record type)         │
│  Upsert Contacts                                 │
│  Resolve Salesforce IDs via SOQL                 │
│  Insert AccountContactRelations (skip dupes)     │
│  Upsert FinancialAccounts                        │
│  Upsert Assets / Positions  (if enabled)         │
└─────────────────────────────────────────────────┘
      │
      ▼
SSE stream sends stage events to browser in real time
      │
      ▼
SyncRun record saved to DB (counts + hashed errors only)
      │
      ▼
CSV discarded from memory
```

---

## Salesforce Object Mapping

| CSV Concept | Salesforce Object | External ID Field |
|---|---|---|
| Household | `Account` (Household RT) | `TamaracHouseholdId__c` |
| Contact | `Contact` | `TamaracContactId__c` |
| Household ↔ Contact | `AccountContactRelation` | (insert only) |
| Financial Account | `FinancialAccount` | `TamaracAccountId__c` |
| Position | `Asset` | `TamaracPositionId__c` |

> **Important:** The external ID fields must be created in your Salesforce org before running a sync. The app validates they exist but does not create metadata.

---

## CSV Format

The app expects a combined CSV with one row per position (households and contacts repeat across rows — deduplication is handled automatically):

```
HouseholdExternalId, HouseholdName,
ContactExternalId, ContactFirstName, ContactLastName, ContactEmail, ContactPhone, ContactRole, IsPrimaryContact,
FinancialAccountExternalId, FinancialAccountName, FinancialAccountNumber, Custodian, AccountType,
PositionExternalId, Symbol, CUSIP, Quantity, Price, MarketValue, PositionAsOfDate
```

Extra columns (e.g. transaction data) are ignored safely.

---

## Getting Started

### Prerequisites
- Docker + Docker Compose
- An Auth0 account (free tier works)
- A Salesforce FSC sandbox with a Connected App configured for JWT bearer flow
- The custom external ID fields created in your Salesforce org (see [Salesforce Object Mapping](#salesforce-object-mapping))

### 1. Clone and configure

```bash
git clone https://github.com/jules631/TamRaq.git
cd TamRaq
cp .env.example .env
```

Edit `.env` and fill in:

```bash
# Auth0 — create an Application (SPA) and an API in your Auth0 dashboard
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://tamarac-fsc-connector/api
VITE_AUTH0_DOMAIN=your-tenant.us.auth0.com
VITE_AUTH0_CLIENT_ID=<your-spa-client-id>
VITE_AUTH0_AUDIENCE=https://tamarac-fsc-connector/api

# Generate an encryption key for Salesforce private keys at rest:
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
APP_ENCRYPTION_KEY=<fernet-key>

# Any long random string — signs the short-lived SSE access tokens
SSE_TOKEN_SIGNING_KEY=<random-secret-32-chars+>
```

### 2. Boot the stack

```bash
docker compose up
```

This starts Postgres, runs database migrations automatically, then starts the API (port 8000) and web app (port 5173).

### 3. First login

Open **http://localhost:5173** and log in with Auth0. A tenant is automatically created for you on first login.

### 4. Configure Salesforce

Go to **SF Connection** and paste your:
- Salesforce sandbox login URL (`https://test.salesforce.com`)
- Connected App Client ID (Consumer Key)
- Integration username
- RSA private key (PEM format) — encrypted immediately on save

Click **Test Connection** to confirm it works.

### 5. Set up field mapping

Go to **Mapping** → click **Load from Salesforce** to auto-discover:
- Which Account Record Type to use for Households
- Which FinancialAccount field links back to the Household Account

Save, then go to **Run Sync** and upload your first CSV.

---

## Architecture

```
tamarac-fsc-connector/
├── docker-compose.yml
└── apps/
    ├── api/                        # FastAPI (Python 3.11)
    │   └── app/
    │       ├── auth/               # Auth0 JWT validation, tenant membership
    │       ├── db/                 # SQLAlchemy models, Alembic migrations
    │       ├── tenants/            # Tenant CRUD, SF config, sync config
    │       ├── salesforce/         # JWT bearer auth, REST client, discovery
    │       ├── sync/               # 7-stage orchestrator, SSE streaming
    │       └── utils/              # Encryption, hashing, PII redaction
    └── web/                        # React 18 + Vite + TypeScript + MUI
        └── src/
            ├── context/            # Auth, Tenant, SyncRunning contexts
            ├── components/         # Layout, StageStepper, ErrorTable, etc.
            └── pages/              # Connection, Mapping, RunSync, History
```

**Tech stack:**

| Layer | Technology |
|---|---|
| API | FastAPI, Python 3.11 |
| Database | PostgreSQL 16 via SQLAlchemy 2 + psycopg3 |
| Auth | Auth0 (JWT RS256) |
| Encryption | Fernet (envelope encryption, KMS-ready) |
| Streaming | Server-Sent Events via asyncio.Queue |
| Frontend | React 18, Vite, TypeScript, MUI v5 |
| Infra | Docker Compose |

---

## Environment Variables Reference

### API

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (set automatically in docker-compose) |
| `AUTH0_DOMAIN` | Your Auth0 tenant domain |
| `AUTH0_AUDIENCE` | Auth0 API audience identifier |
| `APP_ENCRYPTION_KEY` | Fernet base64 key for encrypting Salesforce private keys |
| `SSE_TOKEN_SIGNING_KEY` | HMAC secret for signing short-lived SSE tokens |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `http://localhost:5173`) |

### Web (Vite)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the API (e.g. `http://localhost:8000`) |
| `VITE_AUTH0_DOMAIN` | Auth0 tenant domain |
| `VITE_AUTH0_CLIENT_ID` | Auth0 SPA application client ID |
| `VITE_AUTH0_AUDIENCE` | Auth0 API audience (must match API side) |

---

## Seed Script (optional)

To manually create a tenant and add a user without going through the UI:

```bash
docker compose exec api python seed.py \
  --tenant-name "Acme Wealth Management" \
  --slug acme \
  --auth0-user-id auth0|YOUR_USER_ID
```

Find your Auth0 user ID in the Auth0 dashboard under **Users**.

---

## Roadmap / Not in MVP

| Feature | Status |
|---|---|
| Transaction sync | Intentionally excluded — columns present in CSV are ignored |
| Scheduled / automatic sync | Planned — currently manual upload only |
| Salesforce metadata creation | Not included — external ID fields must be pre-created in org |
| KMS-backed encryption | Architecture is ready; swap `utils/crypto.py` implementation |
| Multi-worker SSE | Single worker only in MVP; Redis pub/sub needed for scale |
| Salesforce production orgs | Sandbox only recommended for initial rollout |

---

## Deploying the Frontend to Vercel

The React frontend deploys to Vercel with one click. The `vercel.json` at the repo root handles the build configuration automatically.

**One-click deploy:**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/jules631/TamRaq)

**Environment variables to set in Vercel dashboard:**

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | URL of your deployed API (e.g. `https://api.yourdomain.com`) |
| `VITE_AUTH0_DOMAIN` | Your Auth0 tenant domain |
| `VITE_AUTH0_CLIENT_ID` | Auth0 SPA application client ID |
| `VITE_AUTH0_AUDIENCE` | Auth0 API audience identifier |

> The backend (FastAPI + Postgres) is not Vercel-deployable and should be deployed via Docker Compose on a VPS, Railway, Render, or similar. See `docker-compose.yml`.

---

## Contributing

1. Fork → branch off `main` → PR
2. API: `cd apps/api && pip install -e . && uvicorn app.main:app --reload`
3. Web: `cd apps/web && npm install && npm run dev`
4. Migrations: `cd apps/api && alembic revision --autogenerate -m "description"`

---

*Built to give RIA ops teams their Friday afternoons back.*
