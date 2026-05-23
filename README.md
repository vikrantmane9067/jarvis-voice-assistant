# JARVIS — AI Voice Assistant v3.0

> **Just A Rather Very Intelligent System** — Production-grade AI voice assistant powered by FastAPI, rule-based NLP, SQLite, and a retro-futuristic HUD dashboard interface.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-green?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/SQLite-3-lightblue?style=for-the-badge&logo=sqlite" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              Browser (Frontend)                      │
│   HTML5 + CSS3 + Vanilla JS — Retro HUD Dashboard   │
└───────────────────┬──────────────────────────────────┘
                    │ HTTP REST API
        ┌───────────▼────────────┐
        │   FastAPI Backend      │
        │   - JWT Auth           │
        │   - Rule-based NLP     │
        │   - System Automation  │
        │   - Request Logging    │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │   SQLite Database      │
        │   - users              │
        │   - command_sessions   │
        │   - command_logs       │
        └────────────────────────┘
```

### Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Frontend   | HTML5, CSS3, Vanilla JS       |
| Backend    | FastAPI (Python 3.12)         |
| NLP Engine | Rule-based regex classifier   |
| Database   | SQLite + SQLAlchemy ORM       |
| Auth       | JWT (python-jose + bcrypt)    |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Clone & Install
```bash
git clone https://github.com/vikrantmane9067/jarvis-voice-assistant.git
cd jarvis-voice-assistant
pip install -r requirements.txt
```

### 2. Run the Server
```bash
uvicorn main:app --reload --port 8000
```

### 3. Open in Browser
```
http://localhost:8000
```

### 4. Register & Use
1. Register a new account
2. Click the JARVIS orb to activate voice input
3. Speak or type a command like *"What's the weather in Mumbai?"*
4. JARVIS classifies intent and responds instantly

---

## 🎤 Supported Commands (35+ Intents)

| Category | Example Commands |
|----------|-----------------|
| **Weather** | "weather in Mumbai", "weather in Delhi" |
| **Web Search** | "search for Python tutorials", "google AI news" |
| **Open Apps** | "open YouTube", "open Notepad", "open GitHub" |
| **Media** | "play Shape of You", "play Blinding Lights" |
| **Volume** | "volume up", "turn volume down", "mute" |
| **Screenshot** | "take a screenshot" |
| **System Info** | "system info", "battery status", "disk usage", "my IP" |
| **Time & Date** | "what is the time", "today's date" |
| **Translate** | "translate hello to Spanish", "translate to Hindi" |
| **Define** | "define serendipity", "what does ephemeral mean" |
| **Convert** | "convert 100 km to miles", "37 celsius to fahrenheit" |
| **Calculator** | "what is 25 times 4", "144 divided by 12" |
| **Reminders** | "remind me to call mom at 5pm" |
| **Timers** | "set a timer for 10 minutes" |
| **Notes** | "create a note about my meeting", "add a todo" |
| **Files** | "list files", "create a file called notes.txt" |
| **Clipboard** | "copy hello to clipboard", "read my clipboard" |
| **Git** | "git status", "check git" |
| **Power** | "shutdown", "restart", "sleep", "lock screen" |
| **Fun** | "tell me a joke", "flip a coin", "roll a d20" |

---

## 📡 API Reference

Base URL: `http://localhost:8000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token |
| GET | `/auth/me` | Current user info |
| POST | `/commands/process` | Process a voice/text command |
| GET | `/commands/history` | Fetch command history |
| GET | `/commands/stats` | Intent analytics |
| GET | `/commands/export` | Export history as JSON |
| GET | `/commands/system-stats` | Live CPU/RAM/battery |
| GET | `/health` | Health check |

Interactive API docs: `http://localhost:8000/api/docs`

---

## 📁 Project Structure

```
jarvis-voice-assistant/
├── main.py                          # FastAPI entry point
├── requirements.txt
├── app/
│   ├── config.py                    # Settings (Pydantic)
│   ├── database.py                  # SQLAlchemy + SQLite setup
│   ├── models.py                    # ORM models
│   ├── middleware/
│   │   └── logging.py               # Request/response logging
│   ├── routers/
│   │   ├── auth.py                  # /auth endpoints
│   │   └── commands.py              # /commands endpoints
│   ├── schemas/
│   │   ├── auth.py                  # Pydantic auth schemas
│   │   └── command.py               # Pydantic command schemas
│   └── services/
│       ├── auth_service.py          # JWT + bcrypt
│       ├── nlp_service.py           # Rule-based intent classifier (35+ intents)
│       └── automation_service.py    # System automation (volume, screenshot, etc.)
├── index.html                       # Retro-futuristic HUD dashboard
├── style.css                        # Dark glassmorphic design system
└── app.js                           # Auth + voice + API + analytics logic
```

---

## 🔒 Security Features

- **Password Hashing**: bcrypt via passlib
- **JWT Tokens**: HS256, configurable expiry
- **SQL Injection Protection**: SQLAlchemy ORM (parameterized queries)
- **CORS**: Configurable allowed origins
- **Input Validation**: Pydantic schemas on all endpoints
- **Auth Guards**: Every command endpoint requires a valid JWT

---

## 📊 Database Schema

```sql
users
  id, username, email, hashed_password, is_active, is_admin, created_at

command_sessions
  id, user_id (FK), session_token, started_at, ended_at

command_logs
  id, session_id (FK), raw_input, detected_intent,
  confidence_score, response_text, status, latency_ms, created_at
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `change-this-secret` |
| `DATABASE_URL` | SQLite DB path | `sqlite:///./jarvis.db` |
| `DEBUG` | Debug mode | `false` |

Create a `.env` file in the project root:
```env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///./jarvis.db
DEBUG=false
```

---

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --port 8000

# Open browser
start http://localhost:8000
```

---

## 🔮 Future Enhancements

- [ ] WebSocket for real-time streaming responses
- [ ] Redis token blacklist for secure logout
- [ ] Rate limiting middleware (slowapi)
- [ ] OAuth2 (Google/GitHub login)
- [ ] Wake word detection ("Hey JARVIS")
- [ ] Plugin system for custom command handlers
- [ ] Admin analytics dashboard

---

## 📝 Test Results

All 35+ commands tested and verified:
- ✅ **78 automated tests** — 100% pass rate after fixes
- ✅ Auth (register, login, JWT validation, /auth/me)
- ✅ All NLP intents (weather, translate, convert, calc, dice, clipboard, etc.)
- ✅ System automation (volume, screenshot, power, files)
- ✅ Analytics endpoints (stats, history, export)
- ✅ Security (401 on invalid/missing tokens)

---

*Built with ⚡ FastAPI + Python 3.12 — MNC-grade architecture*
