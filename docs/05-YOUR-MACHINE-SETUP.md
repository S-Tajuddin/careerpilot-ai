# CareerPilot AI — Your Machine Setup Guide (Windows)

> **Target Machine:** Lenovo ThinkBook 14, i7, 16GB RAM, 512GB SSD
> **OS:** Windows 11 (most likely)
> **Date:** 2026-07-04

---

## Overview — What You'll Install

| # | Software | Why | Size | Time |
|---|---------|-----|------|:----:|
| 1 | **Python 3.12** | Backend language | ~30 MB | 5 min |
| 2 | **Node.js 20 LTS** | Frontend framework | ~30 MB | 5 min |
| 3 | **Git** | Version control | ~60 MB | 5 min |
| 4 | **Ollama** | Local AI (free LLM) | ~200 MB + 5.5 GB models | 15 min |
| 5 | **VS Code** (optional) | Code editor | ~100 MB | 5 min |
| 6 | **Docker Desktop** (optional) | Run services | ~500 MB | 10 min |
| | | **TOTAL** | **~6.4 GB** | **~45 min** |

---

## STEP 0: Check What You Already Have

Open **PowerShell** or **Command Prompt** and run these commands one by one:

```powershell
# Check Windows version
winver

# Check Python
python --version

# Check Node.js
node --version

# Check npm
npm --version

# Check Git
git --version

# Check if Ollama is installed
ollama --version

# Check VS Code
code --version

# Check Docker
docker --version

# Check available disk space
Get-PSDrive C | Select-Object Used, Free

# Check RAM
(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB

# Check CPU
(Get-CimInstance Win32_Processor).Name
```

### Expected output for your machine:

```
Windows 11 Pro (or Home) — Version 23H2 or newer
Python:  NOT FOUND (or some version)
Node.js: NOT FOUND (or some version)
Git:     NOT FOUND (or some version)
Ollama:  NOT FOUND
RAM:     ~16 GB
CPU:     Intel Core i7-1xxx (12th or 13th gen)
Free:    100+ GB
```

**Write down which ones say "NOT FOUND" — those are the ones you'll install below.**

---

## STEP 1: Install Git

### Check first:
```powershell
git --version
```
If you see `git version 2.x.x`, **skip to Step 2.**

### Install:

**Option A — Download from website (easiest):**

1. Go to: **https://git-scm.com/download/win**
2. Click **"Click here to download"** (auto-detects 64-bit)
3. Run the downloaded `.exe` file
4. Click **Next** on every screen (default settings are fine)
5. When you see "Adjusting your PATH environment", make sure **"Git from the command line and also from 3rd-party software"** is selected
6. Click **Install**
7. Click **Finish**

**Option B — Via winget (faster):**
```powershell
winget install Git.Git
```

### Verify:
```powershell
# Close and reopen PowerShell first!
git --version
# Should output: git version 2.47.x or similar
```

---

## STEP 2: Install Python 3.12

### Check first:
```powershell
python --version
```
If you see `Python 3.12.x`, **skip to Step 3.**
If you see Python 3.11 or 3.13, it will also work — you can skip.
If you see `Python 3.9` or lower, you need to upgrade.

### Install:

**Option A — Download from website (recommended):**

1. Go to: **https://www.python.org/downloads/**
2. Click the button that says **"Download Python 3.12.x"** (the latest 3.12)
3. Run the downloaded `.exe` file
4. ⚠️ **CRITICAL:** Check the box that says **"Add python.exe to PATH"** at the BOTTOM of the first screen!
5. Click **"Install Now"**
6. Wait for installation to complete
7. Click **Close**

**Option B — Via winget:**
```powershell
winget install Python.Python.3.12
```

### Verify:
```powershell
# Close and reopen PowerShell first!
python --version
# Should output: Python 3.12.x

pip --version
# Should output: pip 2x.x.x from ... (python 3.12)
```

### ⚠️ If `python` command doesn't work but `python3` does:
This is normal on some Windows setups. Just use `python3` instead, or:
1. Search "Environment Variables" in Windows Start menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "User variables", find "Path"
5. Add these paths (adjust version number):
   ```
   C:\Users\YourName\AppData\Local\Programs\Python\Python312\
   C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts\
   ```
6. Click OK, restart PowerShell

---

## STEP 3: Install Node.js 20 LTS

### Check first:
```powershell
node --version
```
If you see `v20.x.x` or `v22.x.x`, **skip to Step 4.**

### Install:

**Option A — Download from website (easiest):**

1. Go to: **https://nodejs.org**
2. Click the **LTS** button (Long Term Support — usually v20 or v22)
3. Run the downloaded `.msi` file
4. Click **Next** on every screen (accept all defaults)
5. Click **Install**
6. Click **Finish**

**Option B — Via winget:**
```powershell
winget install OpenJS.NodeJS.20
```

### Verify:
```powershell
# Close and reopen PowerShell first!
node --version
# Should output: v20.x.x or v22.x.x

npm --version
# Should output: 10.x.x or similar
```

---

## STEP 4: Install Ollama (The Most Important One)

### Check first:
```powershell
ollama --version
```
If you see a version number, **skip to "Pull Models" below.**

### Install:

1. Go to: **https://ollama.com/download**
2. Click **"Download for Windows"**
3. Run the downloaded `OllamaSetup.exe`
4. ⚠️ If Windows Defender pops up: Click **"More info"** → **"Run anyway"**
5. The installer will:
   - Install Ollama to `C:\Users\YourName\AppData\Local\Programs\Ollama`
   - Add `ollama` to your PATH
   - Start the Ollama background service (you'll see a 🦙 icon in system tray)
6. Click **Finish**

### Verify:
```powershell
# Close and reopen PowerShell first!
ollama --version
# Should output: ollama version 0.31.x or similar
```

### Pull the AI models:

```powershell
# Embedding model (274 MB — needed for job matching)
ollama pull nomic-embed-text

# Main scoring model (5.2 GB — the brain for job analysis)
ollama pull qwen3:8b
```

**Each model download will take 2-10 minutes depending on your internet speed.**

### Verify models:
```powershell
ollama list
```

You should see:
```
NAME                       ID              SIZE
qwen3:8b                   xxxxxxxxxxxx    5.2 GB
nomic-embed-text:latest    xxxxxxxxxxxx    274 MB
```

### Test the embedding model:
```powershell
ollama run nomic-embed-text
```
If it says "Error: embedding models don't support chat" — that's **correct**, it means it's installed properly!

### Test the main model:
```powershell
ollama run qwen3:8b "What are the top 3 skills for an AEM developer? Be brief."
```

**⏳ This will take 10-20 seconds on your CPU.** You should see a response about AEM, Java, Sling, OSGi.

Type `/bye` to exit the chat.

### ⚠️ Speed expectations on your ThinkBook (no GPU, CPU only):

| Model | Task | Expected Speed |
|-------|------|---------------|
| nomic-embed-text | Generate embedding | < 1 second ✅ |
| qwen3:8b | Score a job | 10-20 seconds ✅ (runs in background) |
| qwen3:8b | Tailor resume | 30-60 seconds ⚠️ (use Gemini Flash instead for this) |

---

## STEP 5: Install VS Code (Optional but Recommended)

### Check first:
```powershell
code --version
```
If you see a version, **skip to Step 6.**

### Install:

**Option A — Download:**
1. Go to: **https://code.visualstudio.com**
2. Click **"Download for Windows"**
3. Run the installer
4. Check **"Add to PATH"** during installation
5. Click **Install**

**Option B — Via winget:**
```powershell
winget install Microsoft.VisualStudioCode
```

### Install recommended extensions:
After VS Code is installed, open it and install these extensions:

1. **Python** (by Microsoft) — Python support
2. **Pylance** (by Microsoft) — Better Python IntelliSense
3. **ES7+ React/Redux/React-Native snippets** — React snippets
4. **Tailwind CSS IntelliSense** — Tailwind autocomplete
5. **Thunder Client** — API testing (like Postman but in VS Code)
6. **GitLens** — Better Git integration
7. **Continue** (by Continue Dev) — AI code assistant that connects to Ollama!

---

## STEP 6: Install Docker Desktop (Optional)

Docker makes it easy to run the whole stack with one command. But it's **optional** — you can also run Python and Node.js directly.

### Check first:
```powershell
docker --version
```
If you see a version, **skip to Step 7.**

### Install:

1. Go to: **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"**
3. Run the installer
4. Make sure **"Use WSL 2 instead of Hyper-V"** is checked
5. Click **OK** and wait for installation
6. Restart your computer
7. Open Docker Desktop from Start menu
8. Accept the terms

### ⚠️ Docker Desktop requirements:
- **WSL 2** must be enabled (Docker installer enables it automatically)
- **4 GB RAM minimum** for Docker (leaves 12 GB for your apps + Ollama)
- Your laptop has 16 GB total — this is fine

---

## STEP 7: Create the Project

Open PowerShell and run:

```powershell
# Go to your preferred workspace folder
cd C:\Users\YourName\Projects
# Or: cd D:\Projects  (if you use D: drive)

# Create project folder
mkdir careerpilot-ai
cd careerpilot-ai

# Initialize git
git init
git config user.name "Your Name"
git config user.email "your.email@gmail.com"
```

---

## STEP 8: Create Your API Keys (Free Accounts)

These are the online accounts you need. Do them in this order:

### 8A. JSearch (OpenWeb Ninja Direct) — Job Search ⭐ PRIMARY

> **Why direct instead of RapidAPI?** Same API, same data, but no middleman.
> Simpler auth, no RapidAPI data limits, cleaner integration.

1. Open: **https://app.openwebninja.com/api/jsearch**
2. Click **"Sign Up"** → Use Google or email login (no credit card)
3. Click **"Subscribe"** on the **Free** plan ($0.00/month, 200 requests)
4. After subscribing, you'll see your **API Key** on the dashboard → **Copy it**

Save it somewhere:
```
JSEARCH_API_KEY=your-key-here
```

#### Test it works (PowerShell):

```powershell
$headers = @{
    "x-api-key" = "YOUR_KEY_HERE"
}

Invoke-RestMethod -Uri "https://api.openwebninja.com/jsearch/search-v2?query=AEM+developer+in+Hyderabad&country=in&num_pages=1&enrich=true" -Headers $headers
```

You should see JSON with job listings from LinkedIn, Indeed, Naukri, etc.

> ⚠️ If you already have a RapidAPI key, it will still work as fallback.
> But going forward, use the direct key — it's better.

### 8B. Google Gemini — LLM for Resume/Cover Letters

1. Open: **https://aistudio.google.com**
2. Sign in with your **Gmail account**
3. Accept Terms of Service
4. Click **"Get API Key"** or **"API Keys"** in left sidebar
5. Click **"Create API Key"**
6. Select **"Create new project"** → Name it "careerpilot-ai"
7. **Copy the key** (starts with `AIza...`)

Save it somewhere:
```
GOOGLE_API_KEY=AIzaSy...
```

### 8C. Serper.dev — Company Research

1. Open: **https://serper.dev**
2. Click **"Sign Up"** → Use Google login
3. Your API key is on the dashboard → **Copy it**

Save it somewhere:
```
SERPER_API_KEY=your-key-here
```

### 8D. Adzuna — Additional India Jobs

1. Open: **https://developer.adzuna.com**
2. Click **"Sign Up"** → Create account
3. Verify email
4. Click **"Create a new application"**
5. Name: "careerpilot-ai" → Click **"Create"**
6. Copy **App ID** and **App Key**

Save them:
```
ADZUNA_APP_ID=12345
ADZUNA_APP_KEY=abc123...
```

### 8E. Telegram Bot — Job Alerts on Phone

1. Open Telegram on your phone or computer
2. Search for **@BotFather** and open the chat
3. Send: `/newbot`
4. BotFather asks for a name → Type: **CareerPilot AI**
5. BotFather asks for a username → Type: **careerpilot_yourname_bot** (must end in "bot")
6. BotFather gives you a token → **Copy it**

Save it:
```
TELEGRAM_BOT_TOKEN=7123456789:AAH...
```

To get your Chat ID:
1. Send any message to your new bot
2. Open in browser: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Look for `"chat":{"id": 123456789}` → **Copy the number**

Save it:
```
TELEGRAM_CHAT_ID=123456789
```

---

## STEP 9: Final Verification Checklist

Open PowerShell and run every command. Write ✅ or ❌ next to each:

```powershell
# 1. Python
python --version
# Expected: Python 3.12.x  → [ ]

# 2. pip
pip --version
# Expected: pip 2x.x  → [ ]

# 3. Node.js
node --version
# Expected: v20.x.x or v22.x.x  → [ ]

# 4. npm
npm --version
# Expected: 10.x.x  → [ ]

# 5. Git
git --version
# Expected: git version 2.x.x  → [ ]

# 6. Ollama
ollama --version
# Expected: ollama version 0.31.x  → [ ]

# 7. Ollama models
ollama list
# Expected: qwen3:8b + nomic-embed-text  → [ ]

# 8. Ollama test (should respond)
ollama run qwen3:8b "Say hello in one sentence"
# Expected: A response from the AI  → [ ]

# 9. VS Code
code --version
# Expected: 1.9x.x  → [ ]  (optional)

# 10. Docker
docker --version
# Expected: Docker version 2x.x  → [ ]  (optional)
```

---

## STEP 10: Quick Functional Tests

### Test Ollama Embedding (job matching brain):
```powershell
curl http://localhost:11434/api/embed -d "{""model"":""nomic-embed-text"",""input"":""AEM Developer Hyderabad""}"
```
If you see a long JSON with numbers, ✅ **it works!**

### Test JSearch API (job search):
```powershell
curl -X GET "https://jsearch.p.rapidapi.com/search?query=AEM+developer+in+Hyderabad&country=in&num_pages=1" -H "X-RapidAPI-Key: YOUR_KEY_HERE" -H "X-RapidAPI-Host: jsearch.p.rapidapi.com"
```
If you see JSON with job listings, ✅ **it works!**

### Test Gemini API (resume tailoring):
```powershell
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" -H "x-goog-api-key: YOUR_KEY_HERE" -H "Content-Type: application/json" -X POST -d "{""contents"":[{""parts"":[{""text"":""Say hello""}]}]}"
```
If you see JSON with a response, ✅ **it works!**

### Test Telegram Bot:
Open in browser:
```
https://api.telegram.org/botYOUR_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=CareerPilot%20is%20alive!
```
If you get a message on Telegram, ✅ **it works!**

---

## Summary — Your Complete Checklist

```
SOFTWARE TO INSTALL ON YOUR THINKBOOK:
═════════════════════════════════════════════════
[ ] Python 3.12     → python.org/downloads
[ ] Node.js 20 LTS  → nodejs.org
[ ] Git              → git-scm.com/download/win
[ ] Ollama           → ollama.com/download
[ ] Ollama models    → ollama pull qwen3:8b + nomic-embed-text
[ ] VS Code          → code.visualstudio.com (optional)
[ ] Docker Desktop   → docker.com (optional)

FREE ACCOUNTS TO CREATE:
═════════════════════════════════════════════════
[ ] JSearch (RapidAPI)     → rapidapi.com → key
[ ] Google Gemini          → aistudio.google.com → key
[ ] Serper.dev             → serper.dev → key
[ ] Adzuna                 → developer.adzuna.com → app_id + key
[ ] Telegram Bot           → @BotFather → token + chat_id

AFTER EVERYTHING IS DONE:
═════════════════════════════════════════════════
[ ] python --version works
[ ] node --version works
[ ] git --version works
[ ] ollama list shows qwen3:8b + nomic-embed-text
[ ] ollama run qwen3:8b "hello" gives a response
[ ] JSearch API returns AEM jobs
[ ] Gemini API returns text
[ ] Telegram bot sends you a message

TOTAL DOWNLOAD SIZE: ~6.4 GB
TOTAL TIME: ~45-60 minutes
TOTAL COST: ₹0
```

---

**Once you've checked everything off, tell me which items are done and I'll start writing the actual backend code.**
