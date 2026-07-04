# CareerPilot AI — How to Run the Project

> **Your Machine:** Lenovo ThinkBook 14, i7, 16GB RAM, Windows 11
> **Date:** 2026-07-05

---

## Quick Start (5 Minutes)

### Step 1: Open Terminal in the Project Folder

Open **PowerShell** or **Command Prompt** and navigate to your project:

```cmd
cd C:\Users\Lenovo\Projects\careerpilot-ai\backend
```

(Adjust the path if you cloned it somewhere else)

### Step 2: Create Virtual Environment (ONE-TIME ONLY)

```cmd
python -m venv .venv
```

This creates a `.venv` folder with an isolated Python environment. Do this **once** — skip it next time.

### Step 3: Activate Virtual Environment

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

You should see `(.venv)` appear at the start of your prompt:
```
(.venv) C:\Users\Lenovo\Projects\careerpilot-ai\backend>
```

> ⚠️ If PowerShell says "cannot be loaded because running scripts is disabled":
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then try the activation command again.

### Step 4: Install Dependencies (ONE-TIME ONLY)

```cmd
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, httpx, etc. Takes 1-2 minutes. **Skip next time** unless requirements.txt changes.

### Step 5: Start Ollama

Open a **NEW** terminal window and run:

```cmd
ollama serve
```

Leave this window open — Ollama runs as a background service.

> If you see "ollama is already running" — it's already started, you're good.

### Step 6: Start the Backend

Go back to your **first** terminal (with `.venv` activated) and run:

```cmd
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:

```
🚀 CareerPilot AI backend running at http://localhost:8000
   Environment: development
   Database: ...\data\careerpilot.db
   Ollama: http://localhost:11434
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 7: Open in Browser

Open your browser and go to:

| URL | What |
|-----|------|
| **http://localhost:8000/docs** | 📖 Interactive API docs (try all endpoints!) |
| **http://localhost:8000/health** | 🏥 Health check (DB + Ollama + Gemini status) |
| **http://localhost:8000/api/profile/** | 👤 Your profile |
| **http://localhost:8000/api/jobs/** | 💼 Job listings |
| **http://localhost:8000/api/company/aem-hirers** | 🏢 AEM hiring companies |

---

## Or: Use the One-Click Start Script

Instead of Steps 2-6, you can just double-click:

```
start.bat
```

This will automatically:
- Create `.venv` if it doesn't exist
- Install dependencies
- Check if Ollama is running
- Start the server

---

## Testing Your API Keys

After the server is running, test each key:

### Test JSearch (Job Search)
```
http://localhost:8000/docs
```
→ Find **POST /api/jobs/search** → Click "Try it out" → Enter:
- query: `AEM developer`
- location: `Hyderabad`
- country: `in`
→ Click **Execute**

### Test Gemini (Company Research)
```
http://localhost:8000/docs
```
→ Find **GET /api/company/research** → Click "Try it out" → Enter:
- company_name: `Accenture`
- role: `AEM Architect`
→ Click **Execute**

### Test Telegram (Notifications)
In your browser:
```
http://localhost:8000/api/company/aem-hirers
```
(Just to verify the server responds. Telegram notifications work in Phase 4.)

### Test Ollama (Local AI)
In a **new** terminal:
```cmd
ollama run qwen3:8b "What are 3 key skills for an AEM architect?"
```
Should respond in 10-20 seconds.

---

## Daily Workflow (After First Setup)

Every time you want to work on the project:

```cmd
cd C:\Users\Lenovo\Projects\careerpilot-ai\backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```

That's it — 3 commands. (Ollama should already be running from system tray.)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Install Python 3.12, check "Add to PATH" during install |
| `pip` not found | Same — reinstall Python with PATH |
| `.venv\Scripts\activate` fails in PowerShell | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `ModuleNotFoundError: No module named 'fastapi'` | You forgot to activate .venv, or forgot `pip install -r requirements.txt` |
| `ollama: command not found` | Install Ollama from https://ollama.com/download |
| Ollama says "model not found" | Run: `ollama pull qwen3:8b` and `ollama pull nomic-embed-text` |
| Port 8000 already in use | Something else is using it. Kill it: `netstat -ano \| findstr :8000` then `taskkill /PID <pid> /F` |
| Database errors | Delete `data\careerpilot.db` — it will be recreated on next start |
| API returns empty results | Check your .env file — make sure JSEARCH_API_KEY is filled in |

---

## Stopping the Server

Press **Ctrl+C** in the terminal where uvicorn is running.

To stop Ollama: right-click the 🦙 icon in system tray → Quit.
