@echo off
REM =============================================================
REM CareerPilot AI — Start Backend (Windows)
REM Run this from: careerpilot-ai\backend\
REM =============================================================

echo.
echo ============================================
echo   CareerPilot AI - Starting Backend
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Copy .env.example to .env and fill in your API keys.
    pause
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist ".venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    echo [SETUP] Virtual environment created.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo [SETUP] Installing dependencies...
pip install -q -r requirements.txt

REM Check if Ollama is running
echo.
echo [CHECK] Testing Ollama connection...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is NOT running!
    echo   Start it first: Open a NEW terminal and run: ollama serve
    echo   Or start it from your Start Menu.
    echo.
    echo   The backend will start anyway, but AI features won't work.
    echo.
) else (
    echo [OK] Ollama is running!
)

REM Ensure data directories exist
if not exist "data" mkdir data
if not exist "data\chroma" mkdir data\chroma
if not exist "data\resumes" mkdir data\resumes
if not exist "data\cover_letters" mkdir data\cover_letters
if not exist "data\exports" mkdir data\exports

REM Start the server
echo.
echo [START] Launching CareerPilot AI backend...
echo   API:     http://localhost:8000
echo   Docs:    http://localhost:8000/docs
echo   Health:  http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server.
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
