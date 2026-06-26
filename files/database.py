"""
╔══════════════════════════════════════════════════════════════╗
║         database.py  —  DATA ENGINEER ASSET                 ║
║  DB initialisation, relational schema, parameterised CRUD.  ║
║  ⚠️  NO UI code. NO Flask routes. NO business logic.        ║
╚══════════════════════════════════════════════════════════════╝
"""

import sqlite3
from config import DB_PATH

# ══════════════════════════════════════════════════════════════
#  CONNECTION
# ══════════════════════════════════════════════════════════════
def get_db() -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ══════════════════════════════════════════════════════════════
#  SCHEMA INITIALISATION
# ══════════════════════════════════════════════════════════════
def init_db():
    """Create all tables and seed reference data if not already present."""
    conn = get_db()
    c    = conn.cursor()

    # ── users ─────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── careers ───────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            title            TEXT NOT NULL,
            category         TEXT NOT NULL,
            description      TEXT,
            skills_required  TEXT,
            avg_salary       TEXT,
            growth_outlook   TEXT
        )
    """)

    # ── quiz_results ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER,
            answers          TEXT,
            matched_careers  TEXT,
            ai_analysis      TEXT,
            taken_at         TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # ── resources ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id   INTEGER,
            type        TEXT,
            title       TEXT,
            url         TEXT,
            description TEXT,
            FOREIGN KEY(career_id) REFERENCES careers(id) ON DELETE CASCADE
        )
    """)

    # ── favourites ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS favourites (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            career_id  INTEGER NOT NULL,
            saved_at   TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, career_id),
            FOREIGN KEY(user_id)  REFERENCES users(id)   ON DELETE CASCADE,
            FOREIGN KEY(career_id)REFERENCES careers(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    _seed_careers(conn)
    _seed_resources(conn)
    conn.close()


# ══════════════════════════════════════════════════════════════
#  SEED DATA
# ══════════════════════════════════════════════════════════════
def _seed_careers(conn: sqlite3.Connection):
    careers = [
        ("Software Engineer",       "Technology",
         "Design, develop and maintain software applications.",
         "Python,Java,JavaScript,Problem Solving", "M 1,710,000 – M 2,880,000", "Excellent"),
        ("Data Scientist",          "Technology",
         "Analyse complex data to help organisations make informed decisions.",
         "Python,Statistics,Machine Learning,SQL",  "M 1,620,000 – M 2,790,000", "Excellent"),
        ("UX/UI Designer",          "Design",
         "Create intuitive and visually appealing user experiences.",
         "Figma,Empathy,Creativity,Prototyping",    "M 1,260,000 – M 2,160,000", "Good"),
        ("Doctor (Medicine)",        "Healthcare",
         "Diagnose and treat patients, promote health and wellness.",
         "Medicine,Anatomy,Communication,Empathy",  "M 3,240,000 – M 5,400,000","Excellent"),
        ("Civil Engineer",           "Engineering",
         "Plan and oversee construction of infrastructure projects.",
         "Mathematics,CAD,Project Management,Physics","M 1,350,000 – M 2,340,000","Good"),
        ("Graphic Designer",         "Design",
         "Create visual concepts to communicate ideas that inspire audiences.",
         "Adobe Suite,Creativity,Typography,Colour Theory","M 810,000 – M 1,530,000","Moderate"),
        ("Accountant",               "Finance",
         "Prepare financial statements, manage budgets and tax compliance.",
         "Excel,Accounting,Attention to Detail,Mathematics","M 990,000 – M 1,800,000","Stable"),
        ("Teacher",                  "Education",
         "Educate and inspire students across various subjects and levels.",
         "Communication,Patience,Subject Knowledge,Creativity","M 720,000 – M 1,350,000","Stable"),
        ("Cybersecurity Analyst",    "Technology",
         "Protect computer systems and networks from digital threats.",
         "Networking,Python,Ethical Hacking,Risk Assessment","M 1,530,000 – M 2,610,000","Excellent"),
        ("Mechanical Engineer",      "Engineering",
         "Design and develop mechanical systems and devices.",
         "CAD,Physics,Mathematics,Problem Solving","M 1,404,000 – M 2,340,000","Good"),
        ("Nurse",                    "Healthcare",
         "Provide care and support to patients in various medical settings.",
         "Empathy,Medical Knowledge,Communication,Stamina","M 1,080,000 – M 1,800,000","Excellent"),
        ("Marketing Manager",        "Business",
         "Develop strategies to promote products and build brand awareness.",
         "Communication,Creativity,Analytics,Leadership","M 1,170,000 – M 2,160,000","Good"),
        ("Environmental Scientist",  "Science",
         "Study environmental issues and develop solutions to protect ecosystems.",
         "Biology,Chemistry,Research,Data Analysis","M 990,000 – M 1,710,000","Good"),
        ("Lawyer",                   "Law",
         "Advise and represent clients in legal matters and court proceedings.",
         "Research,Communication,Critical Thinking,Persuasion","M 1,440,000 – M 3,600,000","Moderate"),
        ("Architect",                "Design",
         "Design buildings and structures that are functional and beautiful.",
         "CAD,Creativity,Maths,Project Management","M 1,260,000 – M 2,340,000","Good"),
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO careers
          (title,category,description,skills_required,avg_salary,growth_outlook)
        VALUES (?,?,?,?,?,?)
    """, careers)
    conn.commit()


def _seed_resources(conn: sqlite3.Connection):
    resources = [
        (1, "Video",   "Python for Beginners",
         "https://youtube.com/python",                "Learn Python from scratch"),
        (1, "Article", "Software Engineering Roadmap",
         "https://roadmap.sh/software-design-architecture", "Career path guide"),
        (2, "Video",   "Data Science Full Course",
         "https://youtube.com/datasci",              "End-to-end data science"),
        (2, "Article", "Kaggle Learn",
         "https://kaggle.com/learn",                 "Free data science courses"),
        (3, "Video",   "UI/UX Design Fundamentals",
         "https://youtube.com/uxdesign",             "Design principles"),
        (3, "Article", "Figma Tutorials",
         "https://help.figma.com",                   "Official Figma guides"),
        (4, "Article", "Khan Academy Medicine",
         "https://khanacademy.org/science/health-and-medicine","Free medical content"),
        (9, "Article", "TryHackMe",
         "https://tryhackme.com",                    "Hands-on cybersecurity labs"),
        (12,"Video",   "Digital Marketing Fundamentals",
         "https://youtube.com/digitalmarketing",     "Marketing basics"),
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO resources
          (career_id,type,title,url,description)
        VALUES (?,?,?,?,?)
    """, resources)
    conn.commit()


# ══════════════════════════════════════════════════════════════
#  USER CRUD
# ══════════════════════════════════════════════════════════════
def db_create_user(username: str, email: str, password_hash: str) -> dict:
    """Insert a new user. Returns {success, user_id} or {error}."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, password_hash)
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()
        return {"success": True, "user_id": row["id"]}
    except sqlite3.IntegrityError:
        return {"error": "Username or email already exists"}
    finally:
        conn.close()


def db_get_user_by_username(username: str) -> dict | None:
    """Return user row as dict or None."""
    conn = get_db()
    row  = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def db_get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    row  = conn.execute(
        "SELECT id, username, email, created_at FROM users WHERE id=?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════
#  CAREER CRUD
# ══════════════════════════════════════════════════════════════
def db_get_all_careers(category: str = "") -> list[dict]:
    conn = get_db()
    if category and category != "All":
        rows = conn.execute(
            "SELECT * FROM careers WHERE category=? ORDER BY title", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM careers ORDER BY title").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_get_career_by_id(career_id: int) -> dict | None:
    conn = get_db()
    row  = conn.execute("SELECT * FROM careers WHERE id=?", (career_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def db_search_careers(query: str) -> list[dict]:
    like = f"%{query.lower()}%"
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM careers
        WHERE lower(title) LIKE ? OR lower(description) LIKE ?
           OR lower(skills_required) LIKE ?
        ORDER BY title
    """, (like, like, like)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
#  QUIZ RESULTS CRUD
# ══════════════════════════════════════════════════════════════
def db_save_quiz_result(user_id, answers_json: str,
                        matched_json: str, ai_text: str) -> int:
    """Insert quiz result and return its rowid."""
    conn = get_db()
    cur  = conn.execute("""
        INSERT INTO quiz_results (user_id, answers, matched_careers, ai_analysis)
        VALUES (?,?,?,?)
    """, (user_id, answers_json, matched_json, ai_text))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def db_get_quiz_history(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM quiz_results WHERE user_id=? ORDER BY taken_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
#  RESOURCES CRUD
# ══════════════════════════════════════════════════════════════
def db_get_resources(career_id: int = None) -> list[dict]:
    conn = get_db()
    if career_id:
        rows = conn.execute(
            "SELECT * FROM resources WHERE career_id=?", (career_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM resources ORDER BY career_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════
#  FAVOURITES CRUD
# ══════════════════════════════════════════════════════════════
def db_save_favourite(user_id: int, career_id: int) -> dict:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO favourites (user_id, career_id) VALUES (?,?)",
            (user_id, career_id)
        )
        conn.commit()
        return {"success": True}
    except sqlite3.IntegrityError:
        return {"message": "Already in favourites"}
    finally:
        conn.close()


def db_get_favourites(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT c.* FROM careers c
        JOIN favourites f ON f.career_id = c.id
        WHERE f.user_id = ?
        ORDER BY c.title
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_remove_favourite(user_id: int, career_id: int) -> dict:
    conn = get_db()
    conn.execute(
        "DELETE FROM favourites WHERE user_id=? AND career_id=?",
        (user_id, career_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


# ══════════════════════════════════════════════════════════════
#  STATS (for dashboard)
# ══════════════════════════════════════════════════════════════
def db_get_stats() -> dict:
    conn = get_db()
    stats = {
        "total_users":    conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "total_careers":  conn.execute("SELECT COUNT(*) FROM careers").fetchone()[0],
        "total_quizzes":  conn.execute("SELECT COUNT(*) FROM quiz_results").fetchone()[0],
        "total_resources":conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0],
    }
    conn.close()
    return stats


def db_get_category_counts() -> list[dict]:
    """Return [{'category': ..., 'count': ...}, ...] for chart rendering."""
    conn  = get_db()
    rows  = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM careers GROUP BY category ORDER BY count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
