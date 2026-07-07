@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Synaptix One-Click System Launcher (Windows)
echo ===================================================
echo.

:: 1. Check if Docker is running, if not start Docker Desktop
echo [1/5] Checking Docker daemon status...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Launching Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    echo Waiting for Docker daemon to initialize...
    :wait_docker
    timeout /t 5 /nobreak >nul
    docker ps >nul 2>&1
    if %errorlevel% neq 0 (
        echo Still waiting for Docker...
        goto wait_docker
    )
    echo Docker daemon is ready.
) else (
    echo [OK] Docker daemon is already running.
)

:: 2. Start PostgreSQL and Backend services
echo.
echo [2/5] Starting PostgreSQL and Backend services via Docker Compose...
docker compose --profile services up -d

:: 3. Wait for PostgreSQL to be fully healthy
echo.
echo [3/5] Waiting for PostgreSQL database to be healthy...
:wait_postgres
docker inspect --format="{{json .State.Health.Status}}" snx-postgres | findstr "healthy" >nul
if %errorlevel% neq 0 (
    echo Waiting for PostgreSQL healthcheck...
    timeout /t 2 /nobreak >nul
    goto wait_postgres
)
echo [OK] PostgreSQL is healthy.

:: 4. Run database migrations on the host
echo.
echo [4/5] Running database migrations...
set PYTHONPATH=.
call .venv\Scripts\alembic upgrade head
if %errorlevel% neq 0 (
    echo [WARNING] Alembic migrations failed or were already applied.
) else (
    echo [OK] Database migrations applied successfully.
)

:: 5. Launch the frontend Next.js development server
echo.
echo [5/5] Launching Next.js frontend development server...
cd frontend-web
start cmd /k "echo Starting Next.js frontend... && npm run dev"

echo.
echo ===================================================
echo   Synaptix system is UP and RUNNING!
echo.
echo   - Web Frontend: http://localhost:3000
echo   - Auth Service: http://localhost:8001
echo   - Academic Service: http://localhost:8002
echo   - Logbook/Electives Service: http://localhost:8006
echo   - Institution Service: http://localhost:8007
echo   - Workflow/Asset Service: http://localhost:8010
echo ===================================================
echo.
echo Press any key to stop all services and exit...
pause >nul

echo Stopping services...
cd ..
docker compose --profile services down
echo Done!
pause
