# 📋 TEAM GUIDE — Career Exploration Platform
## How to Write Code That Works Together

**Version:** 2.0.0 | **Project:** Career Exploration Platform

---

## 🗂️ File Ownership Map

| File | Role | Emoji | Owns |
|------|------|-------|------|
| `config.py` | CEO / Product Lead | 👑 | All constants, colours, fonts, quiz data |
| `database.py` | Data Engineer | 🗄️ | DB schema, CRUD functions, seed data |
| `validator.py` | QA Engineer | 🧪 | Validation, sanitation, regex, unit tests |
| `logic.py` | Lead Developer | ⚙️ | Flask routes, Groq AI, career matching |
| `ui.py` | Front-End Developer | 🎨 | CustomTkinter GUI, charts, frames |
| `career_app.py` | All (Entry Point) | 🚀 | Startup only — nobody edits business logic here |

---

## 👑 CEO / Product Lead — `config.py`

### Your Role
You define the **single source of truth** for every constant in the project.
No other team member should hardcode a colour, font, port number, or
quiz question — they import it from `config.py`.

### What You Write
```python
# Colours
COL = { "primary": "#7B2FBE", "accent": "#FF6B35", ... }

# Fonts (tuples consumed by ui.py)
FONTS = { "title": ("Arial", 28, "bold"), ... }

# App metadata
APP_NAME    = "Career Exploration Platform"
APP_VERSION = "2.0.0"

# API / server settings
FLASK_PORT  = 5050
GROQ_MODEL  = "llama3-8b-8192"

# Quiz content (owned here, imported everywhere)
QUIZ_QUESTIONS = [ { "q": "...", "options": [...] }, ... ]

# Career matching weights (consumed by logic.py)
CAREER_WEIGHTS = { "Software Engineer": {"Building & coding": 3, ...}, ... }
```

### Rules You Must Follow
- ✅ Only define constants — no functions, no classes, no logic.
- ✅ Every value that could ever change goes here.
- ✅ Group related constants with clear section comments.
- ❌ Never import from `database.py`, `logic.py`, `validator.py`, or `ui.py`.
- ❌ Never write `import flask`, `import customtkinter`, or `import sqlite3`.
- ❌ Never put business logic or conditions inside this file.

### How Others Import From You
```python
# Any file can do:
from config import COL, FONTS, APP_NAME, QUIZ_QUESTIONS, CAREER_WEIGHTS
```

---

## 🗄️ Data Engineer — `database.py`

### Your Role
You own the **entire database layer**. You write the schema, seed data,
and every function that reads or writes to SQLite. The rest of the team
calls your functions — they never write raw SQL themselves.

### What You Write
```python
from config import DB_PATH   # <-- only import from config

def get_db() -> sqlite3.Connection:
    """Always return a connection with Row factory ON."""
    ...

def init_db():
    """Create tables if not exist. Call seed helpers."""
    ...

# CRUD naming convention: db_<action>_<entity>
def db_create_user(username, email, password_hash) -> dict:
    ...

def db_get_all_careers(category="") -> list[dict]:
    ...

def db_save_favourite(user_id, career_id) -> dict:
    ...
```

### Rules You Must Follow
- ✅ All functions return plain Python types: `dict`, `list[dict]`, `int`, `bool`.
- ✅ Always use parameterised queries: `conn.execute("SELECT * FROM x WHERE id=?", (id,))`.
- ✅ Always close connections in a `finally` block or use context managers.
- ✅ Return `{"error": "message"}` on failure, `{"success": True}` on success.
- ✅ Use `INSERT OR IGNORE` for seed data so re-runs are safe.
- ❌ Never return `sqlite3.Row` objects directly — always convert with `dict(row)`.
- ❌ Never import from `logic.py`, `ui.py`, or `validator.py`.
- ❌ Never write Flask routes or CustomTkinter widgets.
- ❌ Never hardcode strings like `"career_platform.db"` — use `DB_PATH` from config.

### Function Naming Convention
```
db_create_<entity>   →  INSERT
db_get_<entity>      →  SELECT
db_update_<entity>   →  UPDATE
db_delete_<entity>   →  DELETE
db_save_<entity>     →  INSERT with conflict handling
```

### How Others Import From You
```python
# logic.py imports:
from database import (
    db_create_user, db_get_user_by_username,
    db_get_all_careers, db_save_quiz_result, ...
)

# Nobody else (ui.py, validator.py) should import from database.py.
# They go through the Flask API instead.
```

---

## 🧪 QA Engineer — `validator.py`

### Your Role
You are the **gatekeeper of all input**. Every piece of data that enters
the system — from the GUI, from the API, from the quiz — must pass
through your validation functions first.

### What You Write
```python
from config import QUIZ_QUESTIONS  # Only import from config

# Regex patterns — all in one dict
REGEX = {
    "email":    re.compile(r"^[\w\.\+\-]{1,64}@[\w\-]+\.[a-zA-Z]{2,10}$"),
    "username": re.compile(r"^[a-zA-Z0-9_\-]{3,30}$"),
    ...
}

# Sanitation — always returns a clean string, never raises
def sanitise_string(value, max_len=500) -> str:
    ...

# Validation — always returns (bool, str): (is_valid, error_message)
def validate_email(email) -> tuple[bool, str]:
    ...

def validate_quiz_answers(answers) -> tuple[bool, str]:
    ...

# Unit tests — all in one TestCase class
class TestCareerApp(unittest.TestCase):
    def test_01_valid_email(self): ...
    def test_02_invalid_email(self): ...
```

### Rules You Must Follow
- ✅ Every validation function returns `(bool, str)` — `(True, "")` on pass,
  `(False, "Human-readable error message")` on fail.
- ✅ Every sanitise function returns a safe string and never raises exceptions.
- ✅ Test names must be numbered: `test_01_`, `test_02_`, etc.
- ✅ Write at least 2 tests per validation rule (valid case + invalid case).
- ✅ `run_all_tests()` must return a formatted string (used by the GUI).
- ❌ Never import from `database.py`, `logic.py`, or `ui.py`.
- ❌ Never write UI code or Flask routes.
- ❌ Never call `sys.exit()` or `raise SystemExit` inside tests.
- ❌ Never use `print()` in validation functions — return the error instead.

### Integration Pattern
```python
# In logic.py (Lead Dev calls your functions):
from validator import validate_register_request, sanitise_string

@flask_app.route("/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    ok, msg = validate_register_request(data)  # QA's function
    if not ok:
        return jsonify({"error": msg}), 400
    # ... proceed
```

---

## ⚙️ Lead Developer — `logic.py`

### Your Role
You are the **brain of the application**. You write all Flask routes,
connect the Groq AI, implement the career matching engine, and handle
authentication. You call the Data Engineer's functions and the QA
Engineer's validators — you never write your own SQL or raw validation.

### What You Write
```python
from config   import FLASK_PORT, GROQ_API_KEY, CAREER_WEIGHTS, ...
from database import db_create_user, db_get_all_careers, ...
from validator import validate_register_request, sanitise_string, ...

flask_app = Flask(__name__)

def hash_password(pw): ...
def verify_password(pw, hash): ...
def ask_groq(prompt, system="...") -> str: ...
def match_careers(answers, top_n=5) -> list[str]: ...

@flask_app.route("/careers")
def api_get_careers(): ...

def start_flask(): ...
def launch_flask_thread() -> threading.Thread: ...
```

### Rules You Must Follow
- ✅ Every route must call a validator before touching data:
  ```python
  ok, msg = validate_xyz_request(data)
  if not ok:
      return jsonify({"error": msg}), 400
  ```
- ✅ Every route calls a `db_` function — never raw `sqlite3` calls.
- ✅ Always handle Groq AI timeouts gracefully with a user-friendly fallback.
- ✅ Return consistent JSON: `{"success": True, ...}` or `{"error": "..."}`.
- ✅ HTTP status codes: 200 OK, 400 Bad Request, 401 Unauthorized, 409 Conflict, 500 Server Error.
- ❌ Never write CustomTkinter code.
- ❌ Never write raw SQL — only call `db_` functions from `database.py`.
- ❌ Never skip validation — always call the QA validator first.
- ❌ Never store plaintext passwords — always use `hash_password()`.

### Flask Route Template
```python
@flask_app.route("/resource", methods=["POST"])
def api_create_resource():
    data = request.get_json(silent=True) or {}  # safe JSON parse
    ok, msg = validate_resource_request(data)   # QA gate
    if not ok:
        return jsonify({"error": msg}), 400
    result = db_create_resource(                 # Data layer
        sanitise_string(data["field"])
    )
    if "error" in result:
        return jsonify(result), 409
    return jsonify(result)
```

---

## 🎨 Front-End Developer — `ui.py`

### Your Role
You build **everything the user sees**. Every widget, every frame, every
chart is written here. You communicate with the backend exclusively
through HTTP requests to Flask — no direct DB calls, no business logic.

### What You Write
```python
from config import COL, FONTS, BASE_URL, QUIZ_QUESTIONS, ...
from validator import validate_login_form, sanitise_string

# Font helper
def F(key: str) -> ctk.CTkFont:
    spec = FONTS.get(key, ("Arial", 12))
    return ctk.CTkFont(*spec)

class SplashScreen(ctk.CTkToplevel): ...

class CareerApp(ctk.CTk):
    def _build_sidebar(self): ...
    def _build_home(self): ...
    def _build_auth(self): ...
    def _build_quiz(self): ...
    # ... one _build_ method per section
    # ... one _load_ method per section that fetches data
```

### Rules You Must Follow
- ✅ **ALL colours come from `COL`** — never hardcode hex values.
  ```python
  # CORRECT
  ctk.CTkLabel(..., text_color=COL["accent"])
  # WRONG
  ctk.CTkLabel(..., text_color="#FF6B35")
  ```
- ✅ **ALL fonts come from `FONTS`** via the `F()` helper:
  ```python
  ctk.CTkLabel(..., font=F("body_bold"))
  ```
- ✅ **ALL API calls go in a `threading.Thread`** — never block the GUI:
  ```python
  def _load_careers(self):
      def fetch():
          r = http_req.get(f"{BASE_URL}/careers")
          data = r.json()
          self.after(0, lambda: self._render_careers(data))
      threading.Thread(target=fetch, daemon=True).start()
  ```
- ✅ Client-side validation before sending to API:
  ```python
  ok, msg = validate_login_form(username, password)
  if not ok:
      self._login_msg.configure(text=f"⚠️ {msg}", text_color=COL["warning"])
      return
  ```
- ✅ Layout: sidebar (left, fixed width) + scrollable main (right, expands).
- ✅ One `_build_<name>()` method per frame — called once at startup.
- ✅ One `_load_<name>()` method per frame that needs data — called on show.
- ✅ Dynamic content goes inside a dedicated sub-frame that gets cleared/rebuilt.
- ❌ Never import from `database.py` or `logic.py`.
- ❌ Never call `sqlite3` directly.
- ❌ Never define Flask routes.
- ❌ Never block the main thread with `time.sleep()` or slow API calls.

### Widget Naming Convention
```python
self._login_user   # CTkEntry  — prefix: self._
self._login_msg    # CTkLabel for status messages
self._career_list  # CTkFrame holding dynamic cards
self._quiz_body    # CTkFrame rebuilt on each quiz step
```

---

## 🔄 How the Files Talk to Each Other

```
career_app.py
    │
    ├── init_db()           ← database.py   (creates tables + seeds)
    ├── launch_flask_thread() ← logic.py    (starts Flask in background)
    └── CareerApp()         ← ui.py         (starts the GUI)

ui.py  ────────────── HTTP ──────────────→  logic.py (Flask)
                                                │
                                    ┌───────────┴───────────┐
                              validator.py             database.py
                           (validates input)         (runs SQL queries)
                                    │                       │
                                    └─────── config.py ─────┘
                                         (constants only)
```

### Import Rules Summary

| File | Can import from | Cannot import from |
|------|-----------------|--------------------|
| `config.py` | `os`, stdlib only | Everything else |
| `database.py` | `config` | `logic`, `ui`, `validator` |
| `validator.py` | `config` | `database`, `logic`, `ui` |
| `logic.py` | `config`, `database`, `validator` | `ui` |
| `ui.py` | `config`, `validator` | `database`, `logic` (use HTTP instead) |
| `career_app.py` | `config`, `database`, `logic`, `ui` | (entry point) |

---

## 🚦 Pull Request Checklist

Before submitting code, every team member must confirm:

### All Roles
- [ ] I only modified files in my assigned ownership area.
- [ ] I imported constants from `config.py` — no hardcoded values.
- [ ] I did not add business logic to a file that should not have it.
- [ ] My code runs without errors: `python career_app.py`.

### Data Engineer (`database.py`)
- [ ] All new functions are named `db_<action>_<entity>`.
- [ ] All queries use `?` placeholders — no string formatting in SQL.
- [ ] All functions return `dict` or `list[dict]`, not `sqlite3.Row`.
- [ ] `init_db()` is idempotent — safe to run multiple times.

### QA Engineer (`validator.py`)
- [ ] New feature has at least 2 tests (valid + invalid).
- [ ] All validation functions return `(bool, str)`.
- [ ] `run_all_tests()` still works and outputs cleanly.
- [ ] No tests make network calls or DB calls.

### Lead Developer (`logic.py`)
- [ ] Every route calls a validator before processing.
- [ ] Every route uses a `db_` function — no raw SQL.
- [ ] Groq AI calls have `try/except` with fallback messages.
- [ ] All routes return consistent JSON format.

### Front-End Developer (`ui.py`)
- [ ] All colours use `COL["key"]` — no hex literals.
- [ ] All fonts use `F("key")` helper.
- [ ] All API calls run in a `threading.Thread`.
- [ ] No function blocks the main thread.
- [ ] Tested with login, logout, quiz, careers, compare, and favourites.

---

## 🆘 Common Mistakes & Fixes

| Mistake | Fix |
|---------|-----|
| `text_color="#7B2FBE"` in ui.py | Use `text_color=COL["primary"]` |
| Raw SQL in logic.py | Call `db_get_all_careers()` from database.py |
| `http_req.get(...)` blocking UI | Wrap in `threading.Thread(target=...).start()` |
| `sqlite3.Row` returned from db function | Add `dict(row)` before returning |
| Validation logic in logic.py | Move to validator.py, call it from logic.py |
| Hardcoded `5050` port in ui.py | Use `BASE_URL` from config |
| Missing `try/except` on API call in ui.py | Always wrap http calls in try/except |
| Quiz option string differs from config | Copy options exactly from `QUIZ_QUESTIONS` in config.py |

---

*Last updated: 2024 — Career Exploration Platform v2.0.0*
