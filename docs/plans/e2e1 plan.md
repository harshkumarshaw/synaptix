# Session E2E-1 — End-to-End Integration: Make Everything Work

**Target Agent:** 09-devops + 02-backend (combined scope)
**Estimated duration:** 5-7 hours
**Priority:** HIGHEST — nothing else matters until this works
**Goal:** Open browser → login → see real data → mark attendance → see percentage update. Then set up Playwright so this flow is automatically tested.

---

## Why This Session Exists

Current reality:
- Backend services: NOT RUNNING (`curl localhost:8001` → connection refused)
- Frontend: shows design with zero values, no backend connection
- Database: tables exist but no operational data (no students, no courses, no events)
- Auth: no working login flow
- CORS: not configured
- E2E testing: none

You've built 20+ sessions of backend services and frontend pages. None of it is connected. This session connects everything.

**After this session:** You open `http://localhost:3000`, log in as admin@jmn.edu.in, see a dashboard with real student counts, click "Mark Attendance", see students in a class, mark them present, and watch the percentage update. Then Playwright runs and verifies this flow automatically.

---

## Phase A — Get Services Running Reliably (60-90 min)

### A.1 Docker Compose for All Services

The services should start with ONE command and stay running. Create or update `docker-compose.yml` at root:

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ───────────────────────── Database ─────────────────────────
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: synaptix_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ───────────────────────── Auth Service ─────────────────────
  snx-auth:
    build:
      context: .
      dockerfile: services/snx-auth/Dockerfile
    ports:
      - "8001:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/synaptix_dev
      JWT_SECRET: dev-secret-change-in-production
      JWT_ALGORITHM: HS256
      JWT_EXPIRY_MINUTES: 1440
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy

  # ───────────────────────── Academic Service ─────────────────
  snx-academic:
    build:
      context: .
      dockerfile: services/snx-academic/Dockerfile
    ports:
      - "8002:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/synaptix_dev
      JWT_SECRET: dev-secret-change-in-production
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy

  # ───────────────────────── Logbook Service ──────────────────
  snx-logbook:
    build:
      context: .
      dockerfile: services/snx-logbook/Dockerfile
    ports:
      - "8006:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/synaptix_dev
      JWT_SECRET: dev-secret-change-in-production
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy

  # ───────────────────────── Institution Service ──────────────
  snx-institution:
    build:
      context: .
      dockerfile: services/snx-institution/Dockerfile
    ports:
      - "8007:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/synaptix_dev
      JWT_SECRET: dev-secret-change-in-production
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy

  # ───────────────────────── Workflow Service ─────────────────
  snx-workflow:
    build:
      context: .
      dockerfile: services/snx-workflow/Dockerfile
    ports:
      - "8010:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/synaptix_dev
      JWT_SECRET: dev-secret-change-in-production
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
```

### A.2 Dockerfiles (If Not Existing)

Each service needs a Dockerfile. Standard pattern:

```dockerfile
# services/snx-auth/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY services/snx-auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared packages
COPY packages/ /app/packages/

# Copy service code
COPY services/snx-auth/ /app/

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

If requirements.txt doesn't exist per service, create from the project's pyproject.toml or uv.lock.

**Alternative (simpler for dev):** Skip Docker for services, just run locally:

```powershell
# Terminal 1: Database only via Docker
docker compose up postgres -d

# Terminal 2-6: Services via uvicorn (one per terminal)
# Set environment variables first:
$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_dev"
$env:JWT_SECRET="dev-secret-change-in-production"
$env:JWT_ALGORITHM="HS256"
$env:JWT_EXPIRY_MINUTES="1440"

cd services/snx-auth && uvicorn app.main:app --reload --port 8001
cd services/snx-academic && uvicorn app.main:app --reload --port 8002
cd services/snx-logbook && uvicorn app.main:app --reload --port 8006
cd services/snx-institution && uvicorn app.main:app --reload --port 8007
cd services/snx-workflow && uvicorn app.main:app --reload --port 8010
```

**Or create a single start script** `scripts/dev-start.ps1`:

```powershell
# scripts/dev-start.ps1 — Start all services for local development

$ErrorActionPreference = "Stop"

# Environment
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_dev"
$env:JWT_SECRET = "dev-secret-change-in-production"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRY_MINUTES = "1440"
$env:PYTHONPATH = "."

Write-Host "Starting PostgreSQL..." -ForegroundColor Cyan
docker compose up postgres -d

Write-Host "Waiting for PostgreSQL..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "Running migrations..." -ForegroundColor Cyan
alembic upgrade head

Write-Host "Starting services..." -ForegroundColor Cyan

$services = @(
    @{ Name = "snx-auth";        Port = 8001; Path = "services/snx-auth" },
    @{ Name = "snx-academic";    Port = 8002; Path = "services/snx-academic" },
    @{ Name = "snx-logbook";     Port = 8006; Path = "services/snx-logbook" },
    @{ Name = "snx-institution"; Port = 8007; Path = "services/snx-institution" },
    @{ Name = "snx-workflow";    Port = 8010; Path = "services/snx-workflow" }
)

$jobs = @()
foreach ($svc in $services) {
    $job = Start-Job -ScriptBlock {
        param($path, $port, $dbUrl, $secret)
        $env:DATABASE_URL = $dbUrl
        $env:JWT_SECRET = $secret
        $env:JWT_ALGORITHM = "HS256"
        $env:PYTHONPATH = "."
        Set-Location $using:PWD
        uvicorn "$path/app/main:app" --reload --port $port
    } -ArgumentList $svc.Path, $svc.Port, $env:DATABASE_URL, $env:JWT_SECRET
    $jobs += $job
    Write-Host "  $($svc.Name) starting on port $($svc.Port)..." -ForegroundColor Green
}

Write-Host ""
Write-Host "All services starting. Press Ctrl+C to stop all." -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
foreach ($svc in $services) {
    Write-Host "  $($svc.Name): http://localhost:$($svc.Port)/docs"
}
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Yellow
Write-Host ""

# Wait for Ctrl+C
try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "Stopping services..." -ForegroundColor Red
    $jobs | Stop-Job -PassThru | Remove-Job
    docker compose stop postgres
}
```

### A.3 Verify All Services Running

```powershell
# Health checks
@(8001, 8002, 8006, 8007, 8010) | ForEach-Object {
    try {
        $r = Invoke-RestMethod "http://localhost:$_/health" -TimeoutSec 3
        Write-Host "Port $_`: OK" -ForegroundColor Green
    } catch {
        Write-Host "Port $_`: FAILED" -ForegroundColor Red
    }
}
```

All 5 must return OK before proceeding.

### A.4 CORS Configuration

Every FastAPI service must have CORS middleware. Add to EACH service's `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware
import os

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Verify CORS works:
```powershell
curl -I -X OPTIONS http://localhost:8001/health -H "Origin: http://localhost:3000"
# Should include: Access-Control-Allow-Origin: http://localhost:3000
```

---

## Phase B — Seed Operational Data (60-90 min)

### B.1 Create Comprehensive Seed Script

Create `scripts/admin/seed_jmn_operational.py`:

This script seeds everything needed for a working demo:

```python
"""
Seed JMN Medical College with operational data for development/demo.

Creates:
- 1 tenant (JMN Medical College)
- 5 users (1 admin, 2 faculty, 2 students) with hashed passwords
- 1 program (MBBS)
- 1 curriculum (CBME 2019)
- 5 courses (Anatomy, Physiology, Biochemistry, Community Med, Pharmacology)
- Faculty-course assignments
- Student enrollments
- 20 events (past 2 weeks, for attendance marking)
- 10 attendance records (so dashboards show data)
- 2 logbook entries (so logbook page has content)
"""
import asyncio
import os
from datetime import date, time, timedelta, datetime, timezone
from uuid import uuid4, UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_dev"
)

# ─── Fixed UUIDs for predictable references ───
TENANT_ID = UUID("10000000-0000-0000-0000-000000000001")
ADMIN_USER_ID = UUID("20000000-0000-0000-0000-000000000001")
FACULTY_1_ID = UUID("20000000-0000-0000-0000-000000000002")
FACULTY_2_ID = UUID("20000000-0000-0000-0000-000000000003")
STUDENT_1_ID = UUID("30000000-0000-0000-0000-000000000001")
STUDENT_2_ID = UUID("30000000-0000-0000-0000-000000000002")
PROGRAM_ID = UUID("40000000-0000-0000-0000-000000000001")
CURRICULUM_ID = UUID("50000000-0000-0000-0000-000000000001")

COURSES = {
    "ANAT": {"id": UUID("60000000-0000-0000-0000-000000000001"), "name": "Anatomy", "category": "theory"},
    "PHYS": {"id": UUID("60000000-0000-0000-0000-000000000002"), "name": "Physiology", "category": "theory"},
    "BIOC": {"id": UUID("60000000-0000-0000-0000-000000000003"), "name": "Biochemistry", "category": "theory"},
    "CMED": {"id": UUID("60000000-0000-0000-0000-000000000004"), "name": "Community Medicine", "category": "theory"},
    "PHAR": {"id": UUID("60000000-0000-0000-0000-000000000005"), "name": "Pharmacology", "category": "practical"},
}

DEFAULT_PASSWORD = "Synaptix@2026"  # Dev only — change for production


async def main():
    engine = create_async_engine(DATABASE_URL)
    Session = async_sessionmaker(engine)

    async with Session() as session:
        # ─── Tenant ───
        await session.execute(text("""
            INSERT INTO tenants (id, name, code, status, created_at, updated_at)
            VALUES (:id, :name, :code, 'active', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": TENANT_ID, "name": "JMN Medical College", "code": "JMN"})

        # ─── Users ───
        password_hash = pwd_context.hash(DEFAULT_PASSWORD)
        
        users = [
            {"id": ADMIN_USER_ID, "email": "admin@jmn.edu.in", "name": "Sila Singh Ghosh",
             "role": "admin", "student_id": None},
            {"id": FACULTY_1_ID, "email": "dr.ray@jmn.edu.in", "name": "Prof. Dr. Amita Ray",
             "role": "faculty", "student_id": None},
            {"id": FACULTY_2_ID, "email": "dr.mukherjee@jmn.edu.in", "name": "Prof. Dr. P.P. Mukherjee",
             "role": "faculty", "student_id": None},
            {"id": STUDENT_1_ID, "email": "student1@jmn.edu.in", "name": "Rahul Sharma",
             "role": "student", "student_id": str(UUID("30000000-0000-0000-0000-000000000011"))},
            {"id": STUDENT_2_ID, "email": "student2@jmn.edu.in", "name": "Priya Patel",
             "role": "student", "student_id": str(UUID("30000000-0000-0000-0000-000000000012"))},
        ]

        for u in users:
            await session.execute(text("""
                INSERT INTO users (id, tenant_id, email, name, password_hash, role, created_at, updated_at)
                VALUES (:id, :tenant_id, :email, :name, :pwd, :role, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {**u, "tenant_id": TENANT_ID, "pwd": password_hash})

        # ─── Students ───
        students = [
            {"id": UUID("30000000-0000-0000-0000-000000000011"),
             "user_id": STUDENT_1_ID, "enrollment_no": "JMN2023001",
             "name": "Rahul Sharma", "batch_year": 2023, "professional_phase": "Phase I"},
            {"id": UUID("30000000-0000-0000-0000-000000000012"),
             "user_id": STUDENT_2_ID, "enrollment_no": "JMN2023002",
             "name": "Priya Patel", "batch_year": 2023, "professional_phase": "Phase I"},
        ]

        for s in students:
            await session.execute(text("""
                INSERT INTO students (id, tenant_id, user_id, enrollment_number, name, 
                    batch_year, professional_phase, status, created_at, updated_at)
                VALUES (:id, :tenant_id, :user_id, :enrollment_no, :name, 
                    :batch_year, :professional_phase, 'active', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {**s, "tenant_id": TENANT_ID})

        # ─── Faculty ───
        faculty = [
            {"id": UUID("20000000-0000-0000-0000-000000000012"),
             "user_id": FACULTY_1_ID, "name": "Prof. Dr. Amita Ray", "department": "Anatomy"},
            {"id": UUID("20000000-0000-0000-0000-000000000013"),
             "user_id": FACULTY_2_ID, "name": "Prof. Dr. P.P. Mukherjee", "department": "Physiology"},
        ]

        for f in faculty:
            await session.execute(text("""
                INSERT INTO faculty (id, tenant_id, user_id, name, department, 
                    status, created_at, updated_at)
                VALUES (:id, :tenant_id, :user_id, :name, :department, 
                    'active', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {**f, "tenant_id": TENANT_ID})

        # ─── Program + Curriculum ───
        await session.execute(text("""
            INSERT INTO programs (id, tenant_id, name, code, created_at, updated_at)
            VALUES (:id, :tenant_id, 'MBBS', 'MBBS', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": PROGRAM_ID, "tenant_id": TENANT_ID})

        await session.execute(text("""
            INSERT INTO curricula (id, tenant_id, program_id, version, name, 
                status, created_at, updated_at)
            VALUES (:id, :tenant_id, :program_id, 'CBME 2019', 'NMC CBME 2019', 
                'active', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """), {"id": CURRICULUM_ID, "tenant_id": TENANT_ID, "program_id": PROGRAM_ID})

        # ─── Courses ───
        for code, info in COURSES.items():
            await session.execute(text("""
                INSERT INTO courses (id, tenant_id, curriculum_id, code, name, 
                    subject_code, default_attendance_category, created_at, updated_at)
                VALUES (:id, :tenant_id, :curriculum_id, :code, :name, 
                    :subject_code, :category, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": info["id"], "tenant_id": TENANT_ID,
                "curriculum_id": CURRICULUM_ID, "code": code,
                "name": info["name"], "subject_code": code,
                "category": info["category"],
            })

        # ─── Events (past 2 weeks of classes) ───
        today = date.today()
        event_count = 0
        for day_offset in range(14):
            event_date = today - timedelta(days=day_offset)
            if event_date.weekday() >= 5:  # skip weekends
                continue
            for code, info in list(COURSES.items())[:3]:  # ANAT, PHYS, BIOC
                event_id = uuid4()
                await session.execute(text("""
                    INSERT INTO events (id, tenant_id, course_id, event_date,
                        start_time, end_time, event_type, status,
                        attendance_category, professional_phase,
                        created_at, updated_at)
                    VALUES (:id, :tenant_id, :course_id, :event_date,
                        :start_time, :end_time, 'lecture', 'conducted',
                        :category, 'Phase I', NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """), {
                    "id": event_id, "tenant_id": TENANT_ID,
                    "course_id": info["id"], "event_date": event_date,
                    "start_time": time(9 + event_count % 3, 0),
                    "end_time": time(10 + event_count % 3, 0),
                    "category": info["category"],
                })
                event_count += 1

                # Mark attendance for both students (75-80% present rate)
                import random
                for student_id in [UUID("30000000-0000-0000-0000-000000000011"),
                                   UUID("30000000-0000-0000-0000-000000000012")]:
                    status = "present" if random.random() < 0.78 else "absent"
                    await session.execute(text("""
                        INSERT INTO attendance (id, tenant_id, student_id, event_id,
                            status, attendance_category, professional_phase,
                            method, marked_at, created_at, updated_at)
                        VALUES (:id, :tenant_id, :student_id, :event_id,
                            :status, :category, 'Phase I',
                            'manual', NOW(), NOW(), NOW())
                        ON CONFLICT DO NOTHING
                    """), {
                        "id": uuid4(), "tenant_id": TENANT_ID,
                        "student_id": student_id, "event_id": event_id,
                        "status": status, "category": info["category"],
                    })

        await session.commit()
        print(f"✅ Seeded JMN Medical College:")
        print(f"   Tenant: JMN Medical College")
        print(f"   Users: 5 (1 admin, 2 faculty, 2 students)")
        print(f"   Courses: {len(COURSES)}")
        print(f"   Events: {event_count}")
        print(f"   Attendance records: {event_count * 2}")
        print(f"")
        print(f"   Login credentials:")
        print(f"   Admin:    admin@jmn.edu.in / {DEFAULT_PASSWORD}")
        print(f"   Faculty:  dr.ray@jmn.edu.in / {DEFAULT_PASSWORD}")
        print(f"   Student:  student1@jmn.edu.in / {DEFAULT_PASSWORD}")

    await engine.dispose()


if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(main())
```

**Note:** This script uses raw SQL `text()` to be schema-agnostic. The actual column names may differ from what's shown — the agent must check the actual table schemas via `\d tablename` and adjust accordingly. This is CRITICAL — do not run the script blindly. Verify each INSERT matches the actual columns.

### B.2 Run the Seed Script

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_dev"
python scripts/admin/seed_jmn_operational.py
```

### B.3 Verify Seed Data

```powershell
psql -U postgres -d synaptix_dev -c "SELECT count(*) FROM users"
# Expected: 5

psql -U postgres -d synaptix_dev -c "SELECT email, role FROM users"
# Should show 5 rows

psql -U postgres -d synaptix_dev -c "SELECT count(*) FROM events"
# Expected: ~30

psql -U postgres -d synaptix_dev -c "SELECT count(*) FROM attendance"
# Expected: ~60
```

---

## Phase C — Fix Auth Flow (30-45 min)

### C.1 Verify Auth Login Endpoint

```powershell
curl -X POST http://localhost:8001/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"admin@jmn.edu.in","password":"Synaptix@2026"}'
```

**If it returns a JWT:** Auth works. Copy the token for testing other endpoints.

**If it returns 422/401/500:** The auth service needs fixing. Common issues:

1. **No `/auth/login` route exists:** Check `services/snx-auth/app/routers/`. If missing, create it:

```python
# services/snx-auth/app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    # Find user by email
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(401, detail="Invalid credentials")
    
    # Generate JWT
    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "student_id": str(user.student_id) if hasattr(user, 'student_id') and user.student_id else None,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm=os.getenv("JWT_ALGORITHM", "HS256"))
    
    return LoginResponse(access_token=token)
```

2. **Password hashing mismatch:** The seed script uses bcrypt. The auth service must use the same scheme.

3. **Database connection not configured:** The auth service needs `DATABASE_URL` environment variable.

### C.2 Test Authenticated Endpoint

```powershell
$token = (curl -s -X POST http://localhost:8001/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"admin@jmn.edu.in","password":"Synaptix@2026"}' | ConvertFrom-Json).access_token

# Test an authenticated endpoint
curl -H "Authorization: Bearer $token" http://localhost:8002/attendance/student/30000000-0000-0000-0000-000000000011/summary
```

### C.3 Update Frontend API URL Configuration

In `frontend-web/.env.local`, set the correct API URLs:

```
NEXT_PUBLIC_AUTH_URL=http://localhost:8001
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_LOGBOOK_URL=http://localhost:8006
NEXT_PUBLIC_INSTITUTION_URL=http://localhost:8007
NEXT_PUBLIC_APP_NAME=Synaptix
```

The frontend's `api.ts` needs to route to the correct service based on the endpoint:

```typescript
// src/lib/api.ts
import axios from "axios";
import { useAuthStore } from "@/stores/auth-store";

const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:8001";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";
const LOGBOOK_URL = process.env.NEXT_PUBLIC_LOGBOOK_URL || "http://localhost:8006";

// Create separate instances per service
export const authApi = axios.create({ baseURL: AUTH_URL });
export const academicApi = axios.create({ baseURL: API_URL });
export const logbookApi = axios.create({ baseURL: LOGBOOK_URL });

// Apply JWT interceptor to all
[authApi, academicApi, logbookApi].forEach(instance => {
  instance.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  instance.interceptors.response.use(
    (r) => r,
    (error) => {
      if (error.response?.status === 401) {
        useAuthStore.getState().logout();
        if (typeof window !== "undefined") window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );
});

// Default export for backward compatibility
export default academicApi;
```

Update hooks to use the correct API instance:
- `use-attendance.ts` → uses `academicApi`
- `use-logbook.ts`, `use-doap.ts`, `use-electives.ts` → uses `logbookApi`
- Login → uses `authApi`

---

## Phase D — End-to-End Smoke Test (30 min)

### D.1 Manual Walkthrough

Open `http://localhost:3000` in Chrome. Perform this exact sequence:

1. **Login as admin:**
   - Email: `admin@jmn.edu.in`
   - Password: `Synaptix@2026`
   - Expected: redirect to `/dashboard`

2. **Dashboard:**
   - Expected: stat cards show real numbers (Total Students: 2, etc.)
   - If still showing "—" → API call failing (check browser DevTools → Network tab)

3. **Attendance page (as admin/faculty):**
   - Expected: today's events listed (if events exist for today)
   - Click an event → student list appears
   - Mark both students present → submit
   - Expected: toast "Attendance Saved"

4. **Login as student:**
   - Logout → login as `student1@jmn.edu.in`
   - Dashboard: should show attendance percentage
   - Attendance page: per-subject percentages with colour coding

5. **Logbook page:**
   - Create a new entry → submit with initials
   - Expected: entry appears in list with "Submitted" badge

Document each step: PASS or FAIL with screenshot.

### D.2 Fix Any Failures

Common failures at this stage:
- **CORS blocked:** Check browser console for CORS errors → fix middleware
- **404 on endpoint:** Route not registered → check service main.py
- **500 on query:** Schema mismatch between ORM model and actual table → check column names
- **Empty data:** Seed script didn't run or inserted into wrong columns
- **JWT decode error:** Frontend token decode doesn't match backend token structure

Fix each failure immediately. Do not skip.

---

## Phase E — Playwright Setup + E2E Tests (60-90 min)

### E.1 Install Playwright

```powershell
cd frontend-web
npm install -D @playwright/test
npx playwright install chromium  # Only Chromium for now, fast
```

### E.2 Playwright Config

Create `frontend-web/playwright.config.ts`:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
});
```

### E.3 E2E Test: Login Flow

Create `frontend-web/tests/e2e/auth.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("login with valid credentials redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[type="email"]', "admin@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByText("Dashboard")).toBeVisible();
  });

  test("login with invalid credentials shows error", async ({ page }) => {
    await page.goto("/login");

    await page.fill('input[type="email"]', "wrong@jmn.edu.in");
    await page.fill('input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    await expect(page.getByText(/invalid|failed/i)).toBeVisible();
    await expect(page).toHaveURL(/login/);
  });

  test("accessing dashboard without login redirects to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/login/);
  });
});
```

### E.4 E2E Test: Attendance Flow

Create `frontend-web/tests/e2e/attendance.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

// Reusable login helper
async function loginAs(page, email: string, password: string) {
  await page.goto("/login");
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
}

test.describe("Attendance", () => {
  test("faculty can view attendance page", async ({ page }) => {
    await loginAs(page, "dr.ray@jmn.edu.in", "Synaptix@2026");

    await page.click('text=Mark Attendance');
    await expect(page).toHaveURL(/attendance/);
    await expect(page.getByText("Mark Attendance")).toBeVisible();
  });

  test("student can view attendance summary", async ({ page }) => {
    await loginAs(page, "student1@jmn.edu.in", "Synaptix@2026");

    await page.click('text=My Attendance');
    await expect(page).toHaveURL(/attendance/);
    // Should show at least one subject
    await expect(page.getByText(/Anatomy|Physiology|Biochemistry/)).toBeVisible();
  });

  test("student dashboard shows attendance percentage", async ({ page }) => {
    await loginAs(page, "student1@jmn.edu.in", "Synaptix@2026");
    // Dashboard should show some percentage (not "—")
    await expect(page.getByText(/%/)).toBeVisible();
  });
});
```

### E.5 E2E Test: Navigation

Create `frontend-web/tests/e2e/navigation.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@jmn.edu.in");
    await page.fill('input[type="password"]', "Synaptix@2026");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/dashboard/);
  });

  const pages = [
    { nav: "Attendance", url: /attendance/ },
    { nav: "Logbook", url: /logbook/ },
    { nav: "DOAP Skills", url: /doap/ },
    { nav: "Electives", url: /electives/ },
    { nav: "Leave Requests", url: /leave/ },
  ];

  for (const p of pages) {
    test(`navigate to ${p.nav}`, async ({ page }) => {
      await page.click(`text=${p.nav}`);
      await expect(page).toHaveURL(p.url);
    });
  }
});
```

### E.6 Run Playwright

```powershell
cd frontend-web
npx playwright test
```

Expected: all tests pass (green). If services aren't running, tests will timeout.

### E.7 Add to CI

Add Playwright to the project's test commands:

```json
// package.json (frontend-web)
{
  "scripts": {
    "test": "next lint",
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug"
  }
}
```

---

## Phase F — Commit + Handoff (15 min)

```powershell
git add .
git commit -m "feat: Session E2E-1 — End-to-end integration + Playwright

- Docker Compose for all services + PostgreSQL
- dev-start.ps1 script for one-command local dev
- CORS middleware on all services
- Auth login endpoint (JWT issuance)
- JMN operational seed data (5 users, 5 courses, 30+ events, 60+ attendance records)
- Frontend API routing to correct service URLs
- Playwright setup with 8 E2E tests (auth, attendance, navigation)
- End-to-end flow verified: login → dashboard → attendance → logbook

Login credentials for dev:
  admin@jmn.edu.in / Synaptix@2026
  dr.ray@jmn.edu.in / Synaptix@2026
  student1@jmn.edu.in / Synaptix@2026
"
```

### Session End

```
SESSION END — Agent: 09-devops + 02-backend (Session E2E-1)
Duration: ~X hours

Services: 5/5 running and healthy
CORS: configured on all services
Auth: login endpoint working, JWT issued correctly
Seed data: 5 users, 5 courses, 30+ events, 60+ attendance records
Frontend: connected to backend, showing real data
Playwright: 8 E2E tests, all passing

End-to-end flow: LOGIN → DASHBOARD (real stats) → MARK ATTENDANCE → VIEW PERCENTAGE ✓

Next sessions resume normal roadmap:
  Session F4: Electives + Leave UI
  Sessions 20-21: Phase 3 R1-R3 (exam schema + migrations)
```

---

## After This Session

Everything works end-to-end. You can:
- Open the browser and USE the application
- Demo it to JMN faculty
- Run Playwright tests to verify UI doesn't break
- Continue building with confidence that new features integrate into a working system

The roadmap resumes from where it paused:
- **Frontend F4:** Electives + Leave UI (you already have the plan)
- **Backend 20-21:** Phase 3 schema + migrations (you already have the plan)
- Both run in parallel as before, but now with a WORKING baseline to build on