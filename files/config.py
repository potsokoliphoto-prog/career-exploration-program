"""
╔══════════════════════════════════════════════════════════════╗
║         config.py  —  CEO / PRODUCT LEAD ASSET              ║
║  Global styling, colour palettes, role definitions,         ║
║  font configs, API settings, and sandbox configuration.     ║
║  ⚠️  NO business logic. NO database calls. NO UI widgets.   ║
╚══════════════════════════════════════════════════════════════╝
"""

# ── App Identity ──────────────────────────────────────────────
APP_NAME        = "Career Exploration Platform"
APP_VERSION     = "2.0.0"
APP_TAGLINE     = "Discover Your Path — Powered by Groq AI"
APP_AUTHOR      = "Team CareerLab"
APP_YEAR        = "2024"

# ── Server / API Config ───────────────────────────────────────
FLASK_PORT      = 5050
FLASK_HOST      = "127.0.0.1"
BASE_URL        = f"http://{FLASK_HOST}:{FLASK_PORT}"
SECRET_KEY      = "career_platform_secret_xk92_2024"
DEBUG_MODE      = False

# ── Groq AI Configuration ─────────────────────────────────────
# ⚠️  NEVER paste your real key here in a shared repo.
#     Set it via environment variable:  export GROQ_API_KEY="gsk_..."
import os
GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "gsk_YOUR_GROQ_API_KEY_HERE")
GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL      = "llama3-8b-8192"
GROQ_MAX_TOKENS = 600
GROQ_TEMPERATURE= 0.7
GROQ_TIMEOUT    = 20

# ── Database ──────────────────────────────────────────────────
DB_PATH         = "career_platform.db"

# ══════════════════════════════════════════════════════════════
#  BOLD COLOUR PALETTE  (single source of truth for ALL files)
# ══════════════════════════════════════════════════════════════
COL = {
    # Backgrounds
    "bg":           "#0D0D1A",   # near-black navy — main window background
    "panel":        "#1A1A35",   # deep purple — sidebar / panels
    "card":         "#252550",   # card background
    "input_bg":     "#1E1E40",   # entry/textbox background

    # Brand colours
    "primary":      "#7B2FBE",   # vivid violet — primary action
    "primary_hover":"#9B4FDE",   # lighter violet on hover
    "accent":       "#FF6B35",   # hot orange — secondary action / badges
    "accent_hover": "#FF8C5A",   # lighter orange

    # Semantic colours
    "success":      "#00E676",   # electric green
    "warning":      "#FFD600",   # golden yellow
    "danger":       "#FF1744",   # red — delete / logout
    "info":         "#00B0FF",   # sky blue

    # Text
    "text":         "#F0EEFF",   # warm white — main body text
    "text_dim":     "#C0B8E8",   # slightly dimmed text
    "muted":        "#9E9EBF",   # muted purple-grey — helper text
    "disabled":     "#555570",   # disabled controls

    # Borders & highlights
    "border":       "#3A3A70",   # subtle border
    "highlight":    "#00E5FF",   # cyan highlight — links / AI labels
    "selected":     "#4A2080",   # selected item background

    # Category badge colours (maps to career categories)
    "cat_tech":     "#00B0FF",
    "cat_health":   "#00E676",
    "cat_design":   "#FF6B35",
    "cat_eng":      "#FFD600",
    "cat_finance":  "#7B2FBE",
    "cat_edu":      "#FF80AB",
    "cat_biz":      "#80D8FF",
    "cat_science":  "#CCFF90",
    "cat_law":      "#FF9E80",
    "cat_default":  "#B0BEC5",
}

CATEGORY_COLOURS = {
    "Technology":           COL["cat_tech"],
    "Healthcare":           COL["cat_health"],
    "Design":               COL["cat_design"],
    "Engineering":          COL["cat_eng"],
    "Finance":              COL["cat_finance"],
    "Education":            COL["cat_edu"],
    "Business":             COL["cat_biz"],
    "Science":              COL["cat_science"],
    "Law":                  COL["cat_law"],
}

# ══════════════════════════════════════════════════════════════
#  FONTS  (used by ui.py — import COL and FONTS from here)
# ══════════════════════════════════════════════════════════════
FONTS = {
    "title":        ("Arial", 28, "bold"),
    "heading":      ("Arial", 20, "bold"),
    "subheading":   ("Arial", 16, "bold"),
    "body":         ("Arial", 13),
    "body_bold":    ("Arial", 13, "bold"),
    "small":        ("Arial", 11),
    "small_bold":   ("Arial", 11, "bold"),
    "micro":        ("Arial", 10),
    "mono":         ("Courier", 12),
    "mono_small":   ("Courier", 11),
    "logo":         ("Arial", 22, "bold"),
    "stat":         ("Arial", 26, "bold"),
    "quiz_q":       ("Arial", 18, "bold"),
    "quiz_opt":     ("Arial", 13),
    "badge":        ("Arial", 10, "bold"),
}

# ══════════════════════════════════════════════════════════════
#  TEAM ROLE REGISTRY
# ══════════════════════════════════════════════════════════════
TEAM_ROLES = {
    "CEO": {
        "file":         "config.py",
        "name":         "CEO / Product Lead",
        "emoji":        "👑",
        "owns":         ["COL", "FONTS", "APP_*", "GROQ_*", "FLASK_*", "DB_PATH",
                         "TEAM_ROLES", "CAREER_CATEGORIES", "QUIZ_QUESTIONS"],
        "must_not":     ["UI widgets", "DB calls", "business logic"],
        "description":  "Defines global constants consumed by all other files."
    },
    "DATA": {
        "file":         "database.py",
        "name":         "Data Engineer",
        "emoji":        "🗄️",
        "owns":         ["init_db()", "CRUD functions", "seed data", "get_db()"],
        "must_not":     ["UI code", "Flask routes", "business rules"],
        "description":  "Pure database layer — schema, seeds, parameterised queries."
    },
    "QA": {
        "file":         "validator.py",
        "name":         "QA Engineer",
        "emoji":        "🧪",
        "owns":         ["validate_*()", "sanitise_*()", "TestCareerApp", "RegEx rules"],
        "must_not":     ["UI code", "DB calls", "Flask routes"],
        "description":  "Input validation, sanitation, regex, and unit tests."
    },
    "LEAD": {
        "file":         "logic.py",
        "name":         "Lead Developer",
        "emoji":        "⚙️",
        "owns":         ["Flask app", "routes", "auth helpers", "match_careers()",
                         "ask_groq()", "start_flask()"],
        "must_not":     ["UI widgets", "direct DB schema changes"],
        "description":  "Core application logic, Flask API, Groq AI integration."
    },
    "FRONTEND": {
        "file":         "ui.py",
        "name":         "Front-End Developer",
        "emoji":        "🎨",
        "owns":         ["CareerApp (CTk)", "SplashScreen", "all frames/widgets",
                         "sidebar", "matplotlib charts"],
        "must_not":     ["DB calls", "Flask route definitions", "business logic"],
        "description":  "Full desktop UI — layout, frames, widgets, charts."
    },
}

# ══════════════════════════════════════════════════════════════
#  QUIZ QUESTIONS  (owned by CEO — shared to logic.py & ui.py)
# ══════════════════════════════════════════════════════════════
QUIZ_QUESTIONS = [
    {
        "q": "Which activities do you enjoy most?",
        "options": [
            "Building & coding",
            "Helping people",
            "Creating art / design",
            "Solving puzzles",
            "Leading teams",
            "Researching & analysing",
        ],
    },
    {
        "q": "What is your strongest skill set?",
        "options": [
            "Technical / programming",
            "Communication & empathy",
            "Creative & visual",
            "Mathematics & logic",
            "Organisation & planning",
            "Science & research",
        ],
    },
    {
        "q": "What type of work environment suits you best?",
        "options": [
            "Remote / independent",
            "Hospital / care setting",
            "Studio / creative space",
            "Office / corporate",
            "Outdoor / fieldwork",
            "Laboratory / research",
        ],
    },
    {
        "q": "Which value matters most in your career?",
        "options": [
            "High salary",
            "Making a difference",
            "Creative freedom",
            "Job security",
            "Innovation",
            "Work-life balance",
        ],
    },
    {
        "q": "What subject did/do you enjoy most at school?",
        "options": [
            "Computer Science",
            "Biology / Health",
            "Art & Design",
            "Mathematics",
            "Business Studies",
            "Physics / Chemistry",
        ],
    },
]

# ══════════════════════════════════════════════════════════════
#  CAREER CATEGORIES LIST
# ══════════════════════════════════════════════════════════════
CAREER_CATEGORIES = [
    "All", "Technology", "Healthcare", "Design",
    "Engineering", "Finance", "Education",
    "Business", "Science", "Law",
]

# ══════════════════════════════════════════════════════════════
#  CAREER MATCHING WEIGHTS  (owned by CEO, consumed by logic.py)
# ══════════════════════════════════════════════════════════════
CAREER_WEIGHTS = {
    "Software Engineer": {
        "Building & coding": 3, "Technical / programming": 3,
        "Remote / independent": 2, "High salary": 2, "Computer Science": 3,
    },
    "Data Scientist": {
        "Researching & analysing": 3, "Mathematics & logic": 3,
        "Technical / programming": 2, "High salary": 2, "Mathematics": 2,
    },
    "UX/UI Designer": {
        "Creating art / design": 3, "Creative & visual": 3,
        "Studio / creative space": 2, "Creative freedom": 3, "Art & Design": 3,
    },
    "Doctor (Medicine)": {
        "Helping people": 3, "Communication & empathy": 2,
        "Hospital / care setting": 3, "Making a difference": 3, "Biology / Health": 3,
    },
    "Civil Engineer": {
        "Solving puzzles": 2, "Mathematics & logic": 3,
        "Outdoor / fieldwork": 2, "Innovation": 2, "Physics / Chemistry": 2,
    },
    "Graphic Designer": {
        "Creating art / design": 3, "Creative & visual": 3,
        "Studio / creative space": 2, "Creative freedom": 2, "Art & Design": 3,
    },
    "Accountant": {
        "Mathematics & logic": 3, "Organisation & planning": 3,
        "Office / corporate": 2, "Job security": 3, "Mathematics": 3,
    },
    "Teacher": {
        "Helping people": 3, "Communication & empathy": 3,
        "Making a difference": 3, "Work-life balance": 2, "Biology / Health": 1,
    },
    "Cybersecurity Analyst": {
        "Building & coding": 2, "Technical / programming": 3,
        "Solving puzzles": 3, "High salary": 2, "Computer Science": 3,
    },
    "Mechanical Engineer": {
        "Solving puzzles": 3, "Mathematics & logic": 3,
        "Innovation": 3, "Physics / Chemistry": 3, "Mathematics": 2,
    },
    "Nurse": {
        "Helping people": 3, "Communication & empathy": 3,
        "Hospital / care setting": 3, "Making a difference": 3, "Biology / Health": 3,
    },
    "Marketing Manager": {
        "Leading teams": 3, "Communication & empathy": 2,
        "Creative & visual": 2, "Office / corporate": 2, "Business Studies": 3,
    },
    "Environmental Scientist": {
        "Researching & analysing": 3, "Outdoor / fieldwork": 3,
        "Making a difference": 3, "Laboratory / research": 2, "Physics / Chemistry": 2,
    },
    "Lawyer": {
        "Solving puzzles": 2, "Communication & empathy": 2,
        "Leading teams": 2, "High salary": 2, "Organisation & planning": 3,
    },
    "Architect": {
        "Creating art / design": 2, "Mathematics & logic": 2,
        "Creative & visual": 3, "Innovation": 2, "Art & Design": 2,
    },
}
