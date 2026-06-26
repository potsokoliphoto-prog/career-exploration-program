"""
╔══════════════════════════════════════════════════════════════╗
║         logic.py  —  LEAD DEVELOPER ASSET                   ║
║  Flask app, API routes, auth helpers, Groq AI, matching.    ║
║  ⚠️  NO UI widgets. Import DB fns from database.py.         ║
║      Import constants from config.py.                       ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import hashlib
import threading
from datetime import datetime

import requests as http_req
from flask import Flask, request, jsonify, render_template_string

from config import (
    FLASK_PORT, FLASK_HOST, SECRET_KEY, DEBUG_MODE,
    GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL,
    GROQ_MAX_TOKENS, GROQ_TEMPERATURE, GROQ_TIMEOUT,
    CAREER_WEIGHTS, APP_NAME, APP_VERSION,
)
from database import (
    db_create_user, db_get_user_by_username,
    db_get_all_careers, db_get_resources,
    db_save_quiz_result, db_get_quiz_history,
    db_save_favourite, db_get_favourites,
    db_remove_favourite, db_get_stats,
)
from validator import (
    validate_register_request, validate_login_request,
    validate_quiz_request, validate_favourite_request,
    sanitise_string,
)

# ══════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════════
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ══════════════════════════════════════════════════════════════
#  GROQ AI
# ══════════════════════════════════════════════════════════════
def ask_groq(prompt: str,
             system: str = "You are an expert career counsellor helping students.") -> str:
    """Call the Groq API and return the response text."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       GROQ_MODEL,
        "max_tokens":  GROQ_MAX_TOKENS,
        "temperature": GROQ_TEMPERATURE,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
    }
    try:
        r = http_req.post(GROQ_API_URL, json=payload,
                          headers=headers, timeout=GROQ_TIMEOUT)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except http_req.exceptions.Timeout:
        return "[AI timeout — please try again.]"
    except http_req.exceptions.ConnectionError:
        return "[AI unavailable — check your internet connection.]"
    except Exception as e:
        return f"[AI error: {e}]"


# ══════════════════════════════════════════════════════════════
#  CAREER MATCHING ENGINE
# ══════════════════════════════════════════════════════════════
def match_careers(answers: list, top_n: int = 5) -> list[str]:
    """Score careers against quiz answers and return top N titles."""
    scores = {career: 0 for career in CAREER_WEIGHTS}
    for ans in answers:
        for career, weights in CAREER_WEIGHTS.items():
            scores[career] += weights.get(ans, 0)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [title for title, score in ranked[:top_n] if score > 0]


# ══════════════════════════════════════════════════════════════
#  FLASK APPLICATION
# ══════════════════════════════════════════════════════════════
flask_app = Flask(__name__)
flask_app.secret_key = SECRET_KEY

# ── Web index (human-readable API docs) ───────────────────────
@flask_app.route("/")
def web_index():
    return render_template_string("""
<!DOCTYPE html><html><head>
<title>{{ name }} API</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0D0D1A;color:#F0EEFF;font-family:'Segoe UI',sans-serif;padding:40px;max-width:800px;margin:auto}
  h1{color:#7B2FBE;font-size:2rem;margin-bottom:8px}
  h2{color:#FF6B35;margin:30px 0 12px}
  p{color:#9E9EBF;margin-bottom:20px}
  .endpoint{background:#1A1A35;border-left:4px solid #7B2FBE;padding:14px 18px;border-radius:6px;margin:8px 0}
  .method{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:bold;margin-right:10px}
  .get{background:#00B0FF;color:#000}
  .post{background:#FF6B35;color:#fff}
  code{color:#00E5FF;font-size:.95rem}
  .badge{background:#252550;padding:2px 8px;border-radius:12px;font-size:.8rem;color:#FFD600}
</style></head><body>
<h1>🎯 {{ name }}</h1>
<p>Version {{ version }} — Flask API running. Use the desktop app for the full experience.</p>
<span class="badge">✅ Server Online</span>
<h2>Available Endpoints</h2>
{% for ep in endpoints %}
<div class="endpoint">
  <span class="method {{ ep.method.lower() }}">{{ ep.method }}</span>
  <code>{{ ep.path }}</code> — {{ ep.desc }}
</div>
{% endfor %}
</body></html>
""", name=APP_NAME, version=APP_VERSION, endpoints=[
    {"method":"GET",  "path":"/careers",              "desc":"List careers (filter: ?category=)"},
    {"method":"GET",  "path":"/resources",             "desc":"List resources (filter: ?career_id=)"},
    {"method":"POST", "path":"/quiz",                  "desc":"Submit quiz answers → AI career matches"},
    {"method":"POST", "path":"/auth/register",         "desc":"Register a new user"},
    {"method":"POST", "path":"/auth/login",            "desc":"Login and get user_id"},
    {"method":"POST", "path":"/favourites",            "desc":"Save a favourite career"},
    {"method":"GET",  "path":"/favourites/<user_id>",  "desc":"Get user's favourite careers"},
    {"method":"DELETE","path":"/favourites",           "desc":"Remove a favourite career"},
    {"method":"GET",  "path":"/stats",                 "desc":"Platform statistics"},
    {"method":"GET",  "path":"/status",                "desc":"Health check"},
])


# ── GET /status ───────────────────────────────────────────────
@flask_app.route("/status")
def api_status():
    return jsonify({
        "status":  "running",
        "app":     APP_NAME,
        "version": APP_VERSION,
        "time":    datetime.now().isoformat(),
    })


# ── GET /stats ────────────────────────────────────────────────
@flask_app.route("/stats")
def api_stats():
    return jsonify(db_get_stats())


# ── GET /careers ──────────────────────────────────────────────
@flask_app.route("/careers", methods=["GET"])
def api_get_careers():
    category = sanitise_string(request.args.get("category", ""))
    careers  = db_get_all_careers(category)
    return jsonify(careers)


# ── GET /resources ────────────────────────────────────────────
@flask_app.route("/resources", methods=["GET"])
def api_get_resources():
    career_id_str = request.args.get("career_id")
    career_id     = int(career_id_str) if career_id_str and career_id_str.isdigit() else None
    return jsonify(db_get_resources(career_id))


# ── POST /quiz ────────────────────────────────────────────────
@flask_app.route("/quiz", methods=["POST"])
def api_post_quiz():
    data = request.get_json(silent=True) or {}

    # QA validation
    ok, msg = validate_quiz_request(data)
    if not ok:
        return jsonify({"error": msg}), 400

    answers = data["answers"]
    user_id = data.get("user_id")
    matched = match_careers(answers)

    prompt = (
        f"A student answered a career quiz with these choices: {answers}. "
        f"Their top career matches are: {matched}. "
        "Write 3 motivating, personalised sentences of career guidance. "
        "Be specific about their strengths."
    )
    ai_text = ask_groq(prompt)

    db_save_quiz_result(
        user_id,
        json.dumps(answers),
        json.dumps(matched),
        ai_text,
    )
    return jsonify({"matched_careers": matched, "ai_analysis": ai_text})


# ── POST /auth/register ───────────────────────────────────────
@flask_app.route("/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    ok, msg = validate_register_request(data)
    if not ok:
        return jsonify({"error": msg}), 400

    result = db_create_user(
        sanitise_string(data["username"]),
        sanitise_string(data["email"]).lower(),
        hash_password(data["password"]),
    )
    if "error" in result:
        return jsonify(result), 409
    result["username"] = data["username"]
    return jsonify(result)


# ── POST /auth/login ──────────────────────────────────────────
@flask_app.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    ok, msg = validate_login_request(data)
    if not ok:
        return jsonify({"error": msg}), 400

    user = db_get_user_by_username(sanitise_string(data["username"]))
    if user and verify_password(data["password"], user["password_hash"]):
        return jsonify({
            "success":  True,
            "user_id":  user["id"],
            "username": user["username"],
        })
    return jsonify({"error": "Invalid username or password."}), 401


# ── POST /favourites ──────────────────────────────────────────
@flask_app.route("/favourites", methods=["POST"])
def api_save_favourite():
    data = request.get_json(silent=True) or {}
    ok, msg = validate_favourite_request(data)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify(db_save_favourite(int(data["user_id"]), int(data["career_id"])))


# ── GET /favourites/<user_id> ─────────────────────────────────
@flask_app.route("/favourites/<int:user_id>", methods=["GET"])
def api_get_favourites(user_id):
    return jsonify(db_get_favourites(user_id))


# ── DELETE /favourites ────────────────────────────────────────
@flask_app.route("/favourites", methods=["DELETE"])
def api_remove_favourite():
    data = request.get_json(silent=True) or {}
    ok, msg = validate_favourite_request(data)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify(db_remove_favourite(int(data["user_id"]), int(data["career_id"])))


# ── GET /quiz/history/<user_id> ───────────────────────────────
@flask_app.route("/quiz/history/<int:user_id>", methods=["GET"])
def api_quiz_history(user_id):
    return jsonify(db_get_quiz_history(user_id))


# ── AI Career Advice endpoint (bonus) ────────────────────────
@flask_app.route("/ai/advice", methods=["POST"])
def api_ai_advice():
    data   = request.get_json(silent=True) or {}
    career = sanitise_string(data.get("career", ""), 100)
    if not career:
        return jsonify({"error": "career field is required"}), 400
    prompt = (
        f"Give a student 4 practical steps to start preparing for a career as a {career}. "
        "Be specific, motivating, and concise."
    )
    return jsonify({"advice": ask_groq(prompt)})


# ══════════════════════════════════════════════════════════════
#  FLASK THREAD LAUNCHER
# ══════════════════════════════════════════════════════════════
def start_flask():
    """Start Flask in a daemon thread (called from career_app.py)."""
    flask_app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=DEBUG_MODE,
        use_reloader=False,
    )


def launch_flask_thread() -> threading.Thread:
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════
#  SKILL GAP ANALYSIS ENDPOINT
# ══════════════════════════════════════════════════════════════
@flask_app.route("/skill-gap", methods=["POST"])
def api_skill_gap():
    data        = request.get_json(silent=True) or {}
    career_name = sanitise_string(data.get("career", ""), 100)
    user_skills = sanitise_string(data.get("user_skills", ""), 1000)
    if not career_name or not user_skills:
        return jsonify({"error": "career and user_skills are required"}), 400

    conn = __import__('database').get_db()
    row  = conn.execute(
        "SELECT * FROM careers WHERE title=?", (career_name,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Career '{career_name}' not found"}), 404

    required_skills = row["skills_required"]
    prompt = (
        f"A student wants to become a {career_name}. "
        f"Required skills for this career: {required_skills}. "
        f"The student currently has these skills: {user_skills}. "
        "Respond ONLY with a JSON object with these exact keys: "
        "\"missing_skills\" (list of skills they lack), "
        "\"matching_skills\" (list they already have), "
        "\"learning_plan\" (3 concrete steps to close the gap), "
        "\"readiness_percent\" (integer 0-100). "
        "Return only valid JSON, no extra text."
    )
    ai_raw = ask_groq(prompt)
    import re, json as _json
    try:
        clean = re.sub(r"```json|```", "", ai_raw).strip()
        result = _json.loads(clean)
    except Exception:
        result = {
            "missing_skills":    [],
            "matching_skills":   [],
            "learning_plan":     [ai_raw],
            "readiness_percent": 0,
        }
    result["career"]           = career_name
    result["required_skills"]  = required_skills.split(",")
    return jsonify(result)


# ══════════════════════════════════════════════════════════════
#  ANALYTICS AI SUMMARY ENDPOINT
# ══════════════════════════════════════════════════════════════
@flask_app.route("/analytics/summary", methods=["GET"])
def api_analytics_summary():
    from database import db_get_stats, db_get_category_counts
    stats  = db_get_stats()
    counts = db_get_category_counts()
    top    = counts[0]["category"] if counts else "Technology"
    prompt = (
        f"Career platform stats: {stats}. "
        f"Career category distribution: {counts}. "
        f"The most popular category is {top}. "
        "Write 3 short, insightful sentences summarising these analytics "
        "for a student audience. Be encouraging and specific."
    )
    return jsonify({"summary": ask_groq(prompt), "stats": stats, "categories": counts})


# ══════════════════════════════════════════════════════════════
#  QUIZ RESUME — SAVE PROGRESS & LOAD LAST INCOMPLETE QUIZ
# ══════════════════════════════════════════════════════════════
@flask_app.route("/quiz/progress/<int:user_id>", methods=["GET"])
def api_quiz_progress(user_id):
    """Return the most recent incomplete quiz progress for a user."""
    conn = __import__('database').get_db()
    row  = conn.execute("""
        SELECT * FROM quiz_results
        WHERE user_id=? AND matched_careers IS NULL
        ORDER BY taken_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    conn.close()
    if row:
        import json as _json
        return jsonify({
            "found":   True,
            "answers": _json.loads(row["answers"] or "[]"),
            "quiz_id": row["id"],
        })
    return jsonify({"found": False, "answers": []})


@flask_app.route("/quiz/progress", methods=["POST"])
def api_save_quiz_progress():
    """Save partial quiz answers (no matched_careers yet)."""
    data    = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    answers = data.get("answers", [])
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    import json as _json
    conn = __import__('database').get_db()
    # Delete any existing incomplete quiz for this user first
    conn.execute(
        "DELETE FROM quiz_results WHERE user_id=? AND matched_careers IS NULL",
        (user_id,)
    )
    conn.execute(
        "INSERT INTO quiz_results (user_id, answers) VALUES (?,?)",
        (user_id, _json.dumps(answers))
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ══════════════════════════════════════════════════════════════
#  CAREERS WITH RESOURCES ENDPOINT
# ══════════════════════════════════════════════════════════════
@flask_app.route("/careers/<int:career_id>/resources", methods=["GET"])
def api_career_resources(career_id):
    """Get resources for a specific career."""
    from database import db_get_resources
    return jsonify(db_get_resources(career_id))
