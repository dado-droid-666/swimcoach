# SwimCoach PWA

Competition-focused periodization PWA for swimmers. Generates integrated Swim + Strength (calisthenics/bands) macrocycles from race date.

## Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL + Alembic migrations
- **Frontend**: Vanilla JS + Pico.css + Workbox PWA
- **Auth**: JWT in HttpOnly cookies
- **Payments**: MercadoPago (preapproval/subscriptions)
- **Ads**: Google AdSense (auto-ads for free tier)
- **Analytics**: Umami/Plausible (privacy-friendly)
- **Error Tracking**: Sentry

## Quick Start (Development)

```bash
# Backend
cd swimcoach
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env with your values (generate SECRET_KEY: openssl rand -hex 32)
uvicorn backend.main:app --reload

# Test at http://localhost:8000/docs
```

## Project Structure

```
swimcoach/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # DB engine + session + pooling
│   ├── models.py            # SQLAlchemy models (7 tables)
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT + bcrypt + cookie auth
│   ├── routes/              # API routes
│   │   ├── auth.py          # Register/login/logout/me
│   │   ├── profile.py       # Athlete profile CRUD
│   │   ├── competition.py   # Competition goal + macrocycle generation
│   │   ├── plan.py          # Weekly/today plans (swim+strength)
│   │   ├── feedback.py      # Daily feedback (swim+strength)
│   │   ├── stats.py         # Summary + readiness (Pro)
│   │   └── subscription.py  # MercadoPago + tier gating
│   ├── services/            # Business logic
│   │   ├── macrocycle_calculator.py  # Periodization engine
│   │   ├── swim_generator.py         # Swim session generator
│   │   ├── strength_generator.py     # Bodyweight+bands generator
│   │   ├── mercadopago_service.py    # Payment integration
│   │   └── ads_service.py            # AdSense config
│   └── jobs/                # Background jobs (APScheduler)
├── frontend/                # PWA (Vanilla JS + Pico.css)
│   ├── index.html           # PWA entry point
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service Worker (offline-first)
│   ├── css/                 # Pico.css + custom styles
│   ├── js/                  # Vanilla JS modules
│   └── assets/icons/        # PWA icons (72-512px)
├── data/                    # Template libraries
│   ├── swim_templates/      # 7 JSON templates (pool/OW)
│   └── strength_templates/  # 7 JSON templates (bodyweight+bands)
├── migrations/              # Alembic database migrations
├── tests/                   # Test scripts
├── .env.example / .env      # Environment config
├── railway.toml / render.yaml  # Deploy configs
├── Dockerfile               # Production Docker image
├── alembic.ini             # Migration config
└── .env.production.example # Production env template
```

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login (sets HttpOnly cookie) |
| POST | `/api/auth/logout` | Logout (clears cookie) |
| GET | `/api/auth/me` | Current user |

### Profile
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/profile` | Create profile |
| GET | `/api/profile` | Get profile |
| PUT | `/api/profile` | Update profile |

### Competition & Plan
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/competition` | Create competition goal |
| GET | `/api/competition` | Get competition goal |
| PUT | `/api/competition` | Update competition goal |
| DELETE | `/api/competition` | Delete competition goal |
| POST | `/api/competition/generate` | Generate macrocycle |
| GET | `/api/plan/macrocycle` | Full macrocycle overview |
| GET | `/api/plan/week` | Week plan (swim + strength) |
| GET | `/api/plan/today` | Today's sessions |

### Feedback
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/feedback` | Submit feedback (swim+strength) |
| GET | `/api/feedback/history` | Paginated history |

### Stats (Pro features gated)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats/summary` | Weekly volume, compliance |
| GET | `/api/stats/readiness` | Readiness score (Pro) |
| GET | `/api/stats/progress` | Charts data (Pro) |

### Subscription (MercadoPago)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/subscription/checkout` | Create Pro checkout |
| GET | `/api/subscription/status` | Current tier + features |
| GET | `/api/subscription/portal` | Billing portal URL |
| POST | `/api/subscription/cancel` | Cancel subscription |
| POST | `/api/subscription/webhook` | MercadoPago webhook |

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT secret (generate: `openssl rand -hex 32`) | Yes |
| `DATABASE_URL` | SQLite (dev) or PostgreSQL (prod) | Yes |
| `MP_ACCESS_TOKEN` | MercadoPago access token | Yes |
| `MP_PUBLIC_KEY` | MercadoPago public key | Yes |
| `MP_WEBHOOK_SECRET` | Webhook signature secret | Yes |
| `MP_PREAPPROVAL_PLAN_ID` | Preapproval plan ID from MP dashboard | Yes |
| `ADSENSE_CLIENT_ID` | AdSense publisher ID | No (dev) |
| `ADSENSE_SLOT_BANNER` | Banner ad slot ID | No |
| `ADSENSE_SLOT_INTERSTITIAL` | Interstitial ad slot ID | No |
| `UMAMI_WEBSITE_ID` | Umami analytics ID | No |
| `SENTRY_DSN` | Sentry DSN for error tracking | No |
| `FRONTEND_URL` | Frontend URL for CORS | Yes |

## Database Migrations (Alembic)

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1

# Show history
alembic history
```

## Production Deployment

### Option 1: Railway (Recommended)

1. **Connect Repository**
   - Go to [railway.app](https://railway.app)
   - New Project → Deploy from GitHub
   - Select this repository

2. **Add PostgreSQL Database**
   - New → Database → PostgreSQL
   - Railway auto-sets `DATABASE_URL` env var

3. **Configure Environment Variables**
   - Go to Variables tab
   - Add all required env vars from `.env.production.example`
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - MercadoPago: Use production credentials from dashboard
   - AdSense: Use production ad unit IDs

4. **Deploy**
   - Railway auto-detects `railway.toml`
   - Deploys on every push to main

5. **Custom Domain** (Optional)
   - Settings → Domains → Add Custom Domain
   - Configure DNS records

### Option 2: Render

1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - New → Web Service → Connect GitHub

2. **Create PostgreSQL Database**
   - New → PostgreSQL → Create
   - Note the connection string

3. **Configure Web Service**
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 4`
   - Add environment variables (same as Railway)

4. **Deploy**
   - Render auto-deploys on push

### Option 3: Docker (Any Platform)

```bash
# Build
docker build -t swimcoach .

# Run locally
docker run -p 8000:8000 --env-file .env swimcoach

# Deploy to any container platform (Fly.io, DigitalOcean, AWS ECS, etc.)
```

### Docker Compose (Local Production-like)

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/swimcoach
      - ENVIRONMENT=production
      - FRONTEND_URL=http://localhost:3000
      - SECRET_KEY=your-secret-key
      # ... other env vars
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=swimcoach
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## Post-Deploy Checklist

- [ ] Run migrations: `alembic upgrade head` (or via Railway/Render shell)
- [ ] Verify health endpoint: `GET /api/health`
- [ ] Test auth flow: Register → Login → Profile → Competition
- [ ] Test MercadoPago webhook: Configure in MP dashboard → `https://your-domain.com/api/subscription/webhook`
- [ ] Verify AdSense ads render on free tier
- [ ] Test PWA install: "Add to Home Screen" works on mobile
- [ ] Configure custom domain + HTTPS
- [ ] Set up Sentry error tracking
- [ ] Configure Umami/Plausible analytics
- [ ] Set up uptime monitoring (UptimeRobot, BetterUptime)

## Database Backup (Production)

```bash
# Railway/Render: Use built-in backups
# Manual pg_dump:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore:
psql $DATABASE_URL < backup_20260916.sql
```

## Monitoring

- **Health Check**: `GET /api/health` (used by Railway/Render)
- **Sentry**: Automatic error capture + performance monitoring
- **Uptime**: Configure external monitoring (30s interval)
- **Logs**: Railway/Render provide log streaming

## Scaling Considerations

- **Workers**: 4 uvicorn workers (adjust based on CPU cores)
- **Database**: Connection pooling (5 base + 10 overflow)
- **Cache**: Add Redis for session caching (future)
- **CDN**: Use Cloudflare for static assets
- **Rate Limiting**: Add slowapi for API protection (future)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 500 on checkout | Check MP credentials + webhook URL |
| Ads not showing | Verify AdSense client ID + ad slots |
| PWA not installing | Check manifest.json + HTTPS |
| DB connection fails | Verify DATABASE_URL + SSL mode |
| Cookie not set | Check SameSite + Secure flags |
| Webhook fails | Check signature + MP dashboard logs |

## Security

- JWT in HttpOnly, Secure, SameSite=Lax cookies
- Bcrypt password hashing
- CORS restricted to FRONTEND_URL
- SQL injection protection via SQLAlchemy ORM
- Webhook signature verification
- Input validation via Pydantic

## License

MIT License - See LICENSE file for details.