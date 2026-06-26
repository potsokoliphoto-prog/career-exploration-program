"""
╔══════════════════════════════════════════════════════════════╗
║         validator.py  —  QA ENGINEER ASSET                  ║
║  Form validation, sanitation, RegEx rules, unit tests.      ║
║  ⚠️  NO UI widgets. NO DB calls. NO Flask routes.           ║
╚══════════════════════════════════════════════════════════════╝
"""

import re
import json
import time
import unittest
from config import QUIZ_QUESTIONS

# ══════════════════════════════════════════════════════════════
#  REGEX RULES  (all patterns in one place for easy maintenance)
# ══════════════════════════════════════════════════════════════
REGEX = {
    "email":    re.compile(r"^[\w\.\+\-]{1,64}@[\w\-]{1,63}(\.[a-zA-Z]{2,10}){1,3}$"),
    "username": re.compile(r"^[a-zA-Z0-9_\-]{3,30}$"),
    "password": re.compile(r"^.{6,128}$"),           # min 6 chars
    "safe_text":re.compile(r"^[^<>\"';&|`$]{1,500}$"),# no injection chars
    "digits":   re.compile(r"^\d+$"),
    "url":      re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9\-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE
    ),
}

# ══════════════════════════════════════════════════════════════
#  SANITISATION HELPERS
# ══════════════════════════════════════════════════════════════
def sanitise_string(value: str, max_len: int = 500) -> str:
    """Strip whitespace, collapse multiple spaces, truncate."""
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned[:max_len]


def sanitise_username(value: str) -> str:
    return sanitise_string(value, 30).lower()


def sanitise_email(value: str) -> str:
    return sanitise_string(value, 254).lower()


# ══════════════════════════════════════════════════════════════
#  VALIDATION FUNCTIONS  — each returns (is_valid: bool, message: str)
# ══════════════════════════════════════════════════════════════
def validate_username(username: str) -> tuple[bool, str]:
    u = sanitise_string(username)
    if not u:
        return False, "Username is required."
    if len(u) < 3:
        return False, "Username must be at least 3 characters."
    if len(u) > 30:
        return False, "Username must be 30 characters or fewer."
    if not REGEX["username"].match(u):
        return False, "Username may only contain letters, numbers, _ or -"
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    e = sanitise_email(email)
    if not e:
        return False, "Email is required."
    if not REGEX["email"].match(e):
        return False, "Please enter a valid email address."
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)."
    return True, ""


def validate_register_form(username: str, email: str, password: str) -> tuple[bool, str]:
    """Full registration form validation — returns first error found."""
    ok, msg = validate_username(username)
    if not ok:
        return False, msg
    ok, msg = validate_email(email)
    if not ok:
        return False, msg
    ok, msg = validate_password(password)
    if not ok:
        return False, msg
    return True, ""


def validate_login_form(username: str, password: str) -> tuple[bool, str]:
    if not username or not username.strip():
        return False, "Username is required."
    if not password:
        return False, "Password is required."
    return True, ""


def validate_quiz_answers(answers: list) -> tuple[bool, str]:
    """Ensure answers list is complete and all options are legitimate."""
    if not isinstance(answers, list):
        return False, "Answers must be a list."
    if len(answers) == 0:
        return False, "No answers provided."
    if len(answers) != len(QUIZ_QUESTIONS):
        return False, (
            f"Expected {len(QUIZ_QUESTIONS)} answers, got {len(answers)}."
        )
    all_valid_options = {
        opt
        for q in QUIZ_QUESTIONS
        for opt in q["options"]
    }
    for i, ans in enumerate(answers):
        if not isinstance(ans, str) or not ans.strip():
            return False, f"Answer {i+1} is empty or invalid."
        if ans not in all_valid_options:
            return False, f"Answer {i+1} contains an unrecognised option."
    return True, ""


def validate_career_id(career_id) -> tuple[bool, str]:
    try:
        cid = int(career_id)
        if cid < 1:
            raise ValueError
        return True, ""
    except (TypeError, ValueError):
        return False, "career_id must be a positive integer."


def validate_user_id(user_id) -> tuple[bool, str]:
    if user_id is None:
        return False, "user_id is required."
    try:
        uid = int(user_id)
        if uid < 1:
            raise ValueError
        return True, ""
    except (TypeError, ValueError):
        return False, "user_id must be a positive integer."


def validate_search_query(query: str) -> tuple[bool, str]:
    if not isinstance(query, str):
        return False, "Search query must be a string."
    if len(query) > 200:
        return False, "Search query is too long."
    if not REGEX["safe_text"].match(query) and query.strip():
        return False, "Search query contains invalid characters."
    return True, ""


# ══════════════════════════════════════════════════════════════
#  API REQUEST VALIDATORS  (used in logic.py Flask routes)
# ══════════════════════════════════════════════════════════════
def validate_register_request(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Request body must be JSON."
    return validate_register_form(
        data.get("username", ""),
        data.get("email", ""),
        data.get("password", ""),
    )


def validate_login_request(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Request body must be JSON."
    return validate_login_form(
        data.get("username", ""),
        data.get("password", ""),
    )


def validate_quiz_request(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Request body must be JSON."
    return validate_quiz_answers(data.get("answers", []))


def validate_favourite_request(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Request body must be JSON."
    ok, msg = validate_user_id(data.get("user_id"))
    if not ok:
        return False, msg
    return validate_career_id(data.get("career_id"))


# ══════════════════════════════════════════════════════════════
#  UNIT TESTS  (10 test cases — run via ui.py Tests tab)
# ══════════════════════════════════════════════════════════════
class TestCareerApp(unittest.TestCase):

    # ── Validation Tests ──────────────────────────────────────
    def test_01_valid_email(self):
        ok, _ = validate_email("student@university.ac.ls")
        self.assertTrue(ok, "Valid email should pass.")

    def test_02_invalid_email(self):
        ok, _ = validate_email("not-an-email")
        self.assertFalse(ok, "Invalid email should fail.")

    def test_03_username_too_short(self):
        ok, msg = validate_username("ab")
        self.assertFalse(ok)
        self.assertIn("3", msg)

    def test_04_username_special_chars(self):
        ok, _ = validate_username("user name!")
        self.assertFalse(ok, "Spaces/special chars should fail username validation.")

    def test_05_valid_username(self):
        ok, _ = validate_username("Potsoko_99")
        self.assertTrue(ok)

    def test_06_password_too_short(self):
        ok, _ = validate_password("abc")
        self.assertFalse(ok)

    def test_07_valid_password(self):
        ok, _ = validate_password("Secure@2024!")
        self.assertTrue(ok)

    def test_08_quiz_empty_answers(self):
        ok, msg = validate_quiz_answers([])
        self.assertFalse(ok)
        self.assertIn("No answers", msg)

    def test_09_quiz_wrong_count(self):
        ok, msg = validate_quiz_answers(["Building & coding", "Helping people"])
        self.assertFalse(ok)
        self.assertIn("Expected", msg)

    def test_10_quiz_invalid_option(self):
        answers = [q["options"][0] for q in QUIZ_QUESTIONS]
        answers[-1] = "MADE UP OPTION"
        ok, msg = validate_quiz_answers(answers)
        self.assertFalse(ok)
        self.assertIn("unrecognised", msg)

    def test_11_quiz_valid_answers(self):
        answers = [q["options"][0] for q in QUIZ_QUESTIONS]
        ok, msg = validate_quiz_answers(answers)
        self.assertTrue(ok, msg)

    def test_12_sanitise_strips_whitespace(self):
        result = sanitise_string("  hello   world  ")
        self.assertEqual(result, "hello world")

    def test_13_career_id_valid(self):
        ok, _ = validate_career_id(3)
        self.assertTrue(ok)

    def test_14_career_id_zero(self):
        ok, _ = validate_career_id(0)
        self.assertFalse(ok)

    def test_15_career_id_string_digits(self):
        ok, _ = validate_career_id("5")
        self.assertTrue(ok, "String digit should be coerced to int.")

    # ── API Route Tests (requires Flask test client passed in) ─
    # These are called by run_flask_tests() below
    def test_16_register_missing_fields(self):
        ok, msg = validate_register_request({"username": "x"})
        self.assertFalse(ok)

    def test_17_full_register_valid(self):
        ok, msg = validate_register_request({
            "username": "testuser99",
            "email":    "test99@mail.com",
            "password": "SafePass123"
        })
        self.assertTrue(ok, msg)

    def test_18_login_empty_username(self):
        ok, _ = validate_login_request({"username": "", "password": "abc"})
        self.assertFalse(ok)

    def test_19_favourite_missing_career_id(self):
        ok, _ = validate_favourite_request({"user_id": 1})
        self.assertFalse(ok)

    def test_20_sanitise_email_lowercase(self):
        result = sanitise_email("  USER@DOMAIN.COM  ")
        self.assertEqual(result, "user@domain.com")


def run_all_tests() -> str:
    """Run all tests and return formatted string output."""
    import io
    stream = io.StringIO()
    suite  = unittest.TestLoader().loadTestsFromTestCase(TestCareerApp)
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    summary = (
        f"\n{'═'*55}\n"
        f"  Ran      : {result.testsRun} tests\n"
        f"  ✅ Passed : {passed}\n"
        f"  ❌ Failed : {len(result.failures)}\n"
        f"  💥 Errors : {len(result.errors)}\n"
        f"{'═'*55}\n"
        f"  {'ALL TESTS PASSED ✅' if result.wasSuccessful() else 'SOME TESTS FAILED ❌'}\n"
        f"{'═'*55}"
    )
    return stream.getvalue() + summary


def run_flask_tests(client) -> str:
    """Additional integration tests using a Flask test client."""
    results = []

    def check(name, condition, detail=""):
        status = "✅ PASS" if condition else "❌ FAIL"
        results.append(f"  {status}  {name}" + (f"\n         {detail}" if detail else ""))

    # Register new user
    r = client.post("/auth/register", json={
        "username": f"qa_tester_{int(time.time())}",
        "email":    f"qa_{int(time.time())}@test.com",
        "password": "QATest123"
    })
    check("POST /auth/register (valid)", r.status_code == 200)

    # Duplicate register should 409
    r2 = client.post("/auth/register", json={
        "username": "qa_dup", "email": "dup@test.com", "password": "pass123"
    })
    client.post("/auth/register", json={
        "username": "qa_dup", "email": "dup@test.com", "password": "pass123"
    })
    # Login wrong password
    r3 = client.post("/auth/login", json={"username": "nobody", "password": "wrong"})
    check("POST /auth/login (wrong creds) → 401", r3.status_code == 401)

    # GET /careers
    r4 = client.get("/careers")
    check("GET /careers → 200 + list", r4.status_code == 200 and isinstance(r4.get_json(), list))

    # GET /resources
    r5 = client.get("/resources")
    check("GET /resources → 200 + list", r5.status_code == 200)

    # POST /quiz empty
    r6 = client.post("/quiz", json={"answers": []})
    check("POST /quiz (empty answers) → 400", r6.status_code == 400)

    # GET /status
    r7 = client.get("/status")
    check("GET /status → 200", r7.status_code == 200)

    # GET /careers?category=Technology
    r8 = client.get("/careers?category=Technology")
    data = r8.get_json()
    all_tech = all(c["category"] == "Technology" for c in data)
    check("GET /careers?category=Technology → filtered", all_tech)

    return "\n".join(["Flask Integration Tests:", *results])
