"""
╔══════════════════════════════════════════════════════════════╗
║         ui.py  —  FRONT-END DEVELOPER ASSET                 ║
║  CustomTkinter desktop UI — fully rebuilt v3.0              ║
║  ⚠️  NO direct DB calls. All data via Flask API.            ║
╚══════════════════════════════════════════════════════════════╝
"""

import threading
import webbrowser
import json
from tkinter import messagebox
import tkinter as tk

import customtkinter as ctk
import requests as http_req

from config import (
    COL, FONTS, APP_NAME, APP_TAGLINE, APP_VERSION,
    BASE_URL, QUIZ_QUESTIONS, CAREER_CATEGORIES,
    CATEGORY_COLOURS,
)
from validator import validate_register_form, validate_login_form

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ── Font helper ───────────────────────────────────────────────
def F(key):
    spec = FONTS.get(key, ("Arial", 12))
    if len(spec) == 3:
        return ctk.CTkFont(spec[0], spec[1], spec[2])
    return ctk.CTkFont(spec[0], spec[1])


# ══════════════════════════════════════════════════════════════
#  SPLASH SCREEN  (embedded — no CTkToplevel crash on Windows)
# ══════════════════════════════════════════════════════════════
class SplashScreen:
    def __init__(self, parent):
        self._parent = parent
        self._frame  = ctk.CTkFrame(parent, fg_color=COL["panel"], corner_radius=0)
        self._frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        ctk.CTkLabel(self._frame, text="🎯",
                     font=ctk.CTkFont("Arial", 60)).pack(pady=(80, 4))
        ctk.CTkLabel(self._frame, text=APP_NAME,
                     font=F("heading"), text_color=COL["primary"]).pack()
        ctk.CTkLabel(self._frame, text=APP_TAGLINE,
                     font=F("small"), text_color=COL["muted"]).pack(pady=(4, 20))
        self._status = ctk.CTkLabel(self._frame, text="Starting...",
                                    font=F("body"), text_color=COL["highlight"])
        self._status.pack()
        self._bar = ctk.CTkProgressBar(self._frame, width=400,
                                       mode="indeterminate",
                                       progress_color=COL["primary"],
                                       fg_color=COL["border"])
        self._bar.pack(pady=14)
        self._bar.start()
        ctk.CTkLabel(self._frame, text=f"v{APP_VERSION}",
                     font=F("micro"), text_color=COL["disabled"]).pack(side="bottom", pady=20)
        parent.update()

    def set_status(self, msg):
        self._status.configure(text=msg)
        self._parent.update()

    def close(self):
        self._bar.stop()
        self._frame.destroy()


# ══════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════
class CareerApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title(f"🎯 {APP_NAME}")
        self.geometry("1300x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COL["bg"])
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Session state
        self.current_user  = None
        self.user_id       = None
        self.quiz_answers  = []
        self.quiz_step     = 0
        self.all_careers   = []
        self.compare_list  = []
        self.selected_career = None

        self._build_sidebar()
        self._build_main()
        self.show_frame("home")

    # ═══════════════════════════════════════════════════════════
    #  SIDEBAR
    # ═══════════════════════════════════════════════════════════
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240,
                                    fg_color=COL["panel"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_f = ctk.CTkFrame(self.sidebar, fg_color=COL["selected"], corner_radius=12)
        logo_f.pack(fill="x", padx=14, pady=(20, 4))
        ctk.CTkLabel(logo_f, text="🎯 Career Explorer",
                     font=F("logo"), text_color=COL["primary"]).pack(pady=(12, 0))
        ctk.CTkLabel(logo_f, text=APP_TAGLINE, font=F("micro"),
                     text_color=COL["muted"], wraplength=200).pack(pady=(2, 10))

        # ── Account box (shown after login) ───────────────────
        self._acct_box = ctk.CTkFrame(self.sidebar, fg_color=COL["card"],
                                      corner_radius=10, border_width=1,
                                      border_color=COL["border"])
        self._acct_box.pack(fill="x", padx=14, pady=(8, 0))

        self._acct_name = ctk.CTkLabel(self._acct_box, text="⚪  Not logged in",
                                       font=F("small_bold"), text_color=COL["muted"])
        self._acct_name.pack(anchor="w", padx=12, pady=(10, 2))

        self._acct_email = ctk.CTkLabel(self._acct_box, text="",
                                        font=F("micro"), text_color=COL["disabled"])
        self._acct_email.pack(anchor="w", padx=12)

        self._logout_btn = ctk.CTkButton(self._acct_box, text="Logout",
                                         fg_color=COL["danger"],
                                         font=F("small_bold"),
                                         height=28, width=90,
                                         command=self._do_logout)
        self._logout_btn.pack(anchor="w", padx=12, pady=(6, 10))
        self._logout_btn.pack_forget()   # hidden until logged in

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COL["border"]).pack(
            fill="x", padx=14, pady=8)

        # Nav
        self._nav_btns = {}
        nav = [
            ("🏠",  "Home",              "home"),
            ("🔐",  "Login / Register",  "auth"),
            ("📝",  "Career Quiz",       "quiz"),
            ("💼",  "Browse Careers",    "careers"),
            ("📚",  "Resources",         "resources"),
            ("⚖️",  "Compare Careers",   "compare"),
            ("❤️",  "My Favourites",     "favourites"),
            ("🔍",  "Skill Gap Analysis","skillgap"),
            ("📊",  "Analytics",         "analytics"),
        ]
        for icon, label, key in nav:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}", anchor="w",
                font=F("body"), fg_color="transparent",
                hover_color=COL["selected"], text_color=COL["text"],
                corner_radius=8, height=40,
                command=lambda k=key: self.show_frame(k))
            btn.pack(fill="x", padx=10, pady=1)
            self._nav_btns[key] = btn

        ctk.CTkLabel(self.sidebar, text=f"v{APP_VERSION}  •  2024",
                     font=F("micro"), text_color=COL["disabled"]).pack(
            side="bottom", pady=10)

    # ── Update account box after login/logout ─────────────────
    def _refresh_account_box(self):
        if self.current_user:
            self._acct_name.configure(
                text=f"🟢  {self.current_user}",
                text_color=COL["success"])
            self._acct_email.configure(text=f"ID: {self.user_id}")
            self._logout_btn.pack(anchor="w", padx=12, pady=(6, 10))
        else:
            self._acct_name.configure(text="⚪  Not logged in",
                                      text_color=COL["muted"])
            self._acct_email.configure(text="")
            self._logout_btn.pack_forget()

    # ═══════════════════════════════════════════════════════════
    #  MAIN CONTAINER
    # ═══════════════════════════════════════════════════════════
    def _build_main(self):
        self._main = ctk.CTkFrame(self, fg_color=COL["bg"], corner_radius=0)
        self._main.pack(side="right", fill="both", expand=True)
        self.frames = {}
        for name in ["home","auth","quiz","careers","resources",
                     "compare","favourites","skillgap","analytics"]:
            f = ctk.CTkScrollableFrame(self._main, fg_color=COL["bg"],
                                       corner_radius=0,
                                       scrollbar_button_color=COL["primary"])
            f.pack(fill="both", expand=True)
            f.pack_forget()
            self.frames[name] = f

        self._build_home()
        self._build_auth()
        self._build_quiz()
        self._build_careers()
        self._build_resources()
        self._build_compare()
        self._build_favourites()
        self._build_skillgap()
        self._build_analytics()

    def show_frame(self, name):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
        for k, b in self._nav_btns.items():
            b.configure(fg_color=COL["primary"] if k == name else "transparent",
                        text_color="white" if k == name else COL["text"])
        if name == "careers":    self._load_careers()
        if name == "favourites": self._load_favourites()
        if name == "resources":  self._load_resources()
        if name == "analytics":  self._load_analytics()
        if name == "compare":    self._render_compare()

    # ── Layout helpers ─────────────────────────────────────────
    def _header(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title, font=F("title"),
                     text_color=COL["accent"]).pack(anchor="w", padx=40, pady=(30, 2))
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle, font=F("body"),
                         text_color=COL["muted"]).pack(anchor="w", padx=40, pady=(0, 16))

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=COL["card"], corner_radius=12,
                            border_width=1, border_color=COL["border"], **kw)

    def _divider(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=COL["border"]).pack(
            fill="x", padx=40, pady=6)

    def _api(self, method, path, **kw):
        """Synchronous API call — always use in a thread."""
        fn = getattr(http_req, method)
        return fn(f"{BASE_URL}{path}", timeout=20, **kw)

    # ═══════════════════════════════════════════════════════════
    #  HOME
    # ═══════════════════════════════════════════════════════════
    def _build_home(self):
        f = self.frames["home"]
        self._header(f, f"🎯 Welcome to {APP_NAME}", APP_TAGLINE)

        hero = ctk.CTkFrame(f, fg_color=COL["primary"], corner_radius=16, height=170)
        hero.pack(fill="x", padx=40, pady=(0, 24))
        hero.pack_propagate(False)
        ctk.CTkLabel(hero, text="Find Your Perfect Career Path",
                     font=F("heading"), text_color="white").place(relx=0.04, rely=0.20)
        ctk.CTkLabel(hero,
                     text="Answer 5 questions — let our Groq AI match you to ideal careers.",
                     font=F("body"), text_color="#D0C0FF").place(relx=0.04, rely=0.55)
        ctk.CTkButton(hero, text="Take the Quiz →",
                      fg_color=COL["accent"], hover_color=COL["accent_hover"],
                      font=F("body_bold"), width=170, height=40,
                      command=lambda: self.show_frame("quiz")).place(relx=0.74, rely=0.32)

        # Stats row
        self._home_stats = ctk.CTkFrame(f, fg_color="transparent")
        self._home_stats.pack(fill="x", padx=40, pady=(0, 24))
        self._refresh_home_stats()

        self._divider(f)
        ctk.CTkLabel(f, text="Quick Access", font=F("subheading"),
                     text_color=COL["text"]).pack(anchor="w", padx=40, pady=(12, 8))
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill="x", padx=40, pady=(0, 30))
        for label, color, target in [
            ("📝  Quiz",          COL["primary"], "quiz"),
            ("💼  Careers",       COL["accent"],  "careers"),
            ("🔍  Skill Gap",     COL["info"],    "skillgap"),
            ("📊  Analytics",     COL["success"], "analytics"),
            ("⚖️  Compare",       COL["warning"], "compare"),
        ]:
            ctk.CTkButton(row, text=label, fg_color=color,
                          hover_color=COL["border"], font=F("body_bold"),
                          width=155, height=50, corner_radius=10,
                          command=lambda t=target: self.show_frame(t)).pack(side="left", padx=6)

    def _refresh_home_stats(self):
        for w in self._home_stats.winfo_children():
            w.destroy()
        try:
            stats = self._api("get", "/stats").json()
        except:
            stats = {}
        for val, lbl in [
            (str(stats.get("total_careers", "15+")), "Careers"),
            (str(stats.get("total_users", "0")),     "Users"),
            (str(stats.get("total_quizzes", "0")),   "Quizzes"),
            ("11",                                    "API Endpoints"),
            ("Groq",                                  "AI Engine"),
        ]:
            c = self._card(self._home_stats, width=170, height=90)
            c.pack(side="left", padx=6)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=val, font=F("stat"),
                         text_color=COL["success"]).pack(pady=(14, 0))
            ctk.CTkLabel(c, text=lbl, font=F("small"),
                         text_color=COL["muted"]).pack()

    # ═══════════════════════════════════════════════════════════
    #  AUTH  — with welcome box update
    # ═══════════════════════════════════════════════════════════
    def _build_auth(self):
        f = self.frames["auth"]
        self._header(f, "🔐 Account Access",
                     "Login to save progress — or create a new account")

        wrap = ctk.CTkFrame(f, fg_color="transparent")
        wrap.pack(pady=10, padx=40, anchor="w")

        # Login card
        lc = self._card(wrap, width=390)
        lc.pack(side="left", padx=0, pady=10, ipadx=10, ipady=10)
        ctk.CTkLabel(lc, text="🔑  Login", font=F("subheading"),
                     text_color=COL["highlight"]).pack(pady=(20, 14))
        self._login_user = ctk.CTkEntry(lc, placeholder_text="Username",
                                        width=320, height=40,
                                        fg_color=COL["input_bg"],
                                        border_color=COL["border"])
        self._login_user.pack(pady=6)
        self._login_pass = ctk.CTkEntry(lc, placeholder_text="Password",
                                        show="•", width=320, height=40,
                                        fg_color=COL["input_bg"],
                                        border_color=COL["border"])
        self._login_pass.pack(pady=6)
        self._login_pass.bind("<Return>", lambda _: self._do_login())
        ctk.CTkButton(lc, text="Login", fg_color=COL["primary"],
                      hover_color=COL["primary_hover"], font=F("body_bold"),
                      width=320, height=42, command=self._do_login).pack(pady=(12, 6))
        self._login_msg = ctk.CTkLabel(lc, text="", font=F("small"),
                                       text_color=COL["success"], wraplength=310)
        self._login_msg.pack(pady=(0, 16))

        # Register card
        rc = self._card(wrap, width=390)
        rc.pack(side="left", padx=24, pady=10, ipadx=10, ipady=10)
        ctk.CTkLabel(rc, text="✨  Create Account", font=F("subheading"),
                     text_color=COL["accent"]).pack(pady=(20, 14))
        self._reg_user  = ctk.CTkEntry(rc, placeholder_text="Username",
                                       width=320, height=40,
                                       fg_color=COL["input_bg"],
                                       border_color=COL["border"])
        self._reg_user.pack(pady=6)
        self._reg_email = ctk.CTkEntry(rc, placeholder_text="Email address",
                                       width=320, height=40,
                                       fg_color=COL["input_bg"],
                                       border_color=COL["border"])
        self._reg_email.pack(pady=6)
        self._reg_pass  = ctk.CTkEntry(rc, placeholder_text="Password (min 6 chars)",
                                       show="•", width=320, height=40,
                                       fg_color=COL["input_bg"],
                                       border_color=COL["border"])
        self._reg_pass.pack(pady=6)
        ctk.CTkButton(rc, text="Create Account", fg_color=COL["accent"],
                      hover_color=COL["accent_hover"], font=F("body_bold"),
                      width=320, height=42, command=self._do_register).pack(pady=(12, 6))
        self._reg_msg = ctk.CTkLabel(rc, text="", font=F("small"),
                                     text_color=COL["success"], wraplength=310)
        self._reg_msg.pack(pady=(0, 16))

    def _do_login(self):
        username = self._login_user.get().strip()
        password = self._login_pass.get()
        ok, msg  = validate_login_form(username, password)
        if not ok:
            self._login_msg.configure(text=f"⚠️ {msg}", text_color=COL["warning"])
            return
        def fetch():
            try:
                r = self._api("post", "/auth/login",
                              json={"username": username, "password": password})
                d = r.json()
                self.after(0, lambda: self._on_login_result(d))
            except Exception as e:
                self.after(0, lambda: self._login_msg.configure(
                    text=f"❌ {e}", text_color=COL["danger"]))
        threading.Thread(target=fetch, daemon=True).start()

    def _on_login_result(self, d):
        if d.get("success"):
            self.current_user = d["username"]
            self.user_id      = d["user_id"]
            self._refresh_account_box()
            self._login_msg.configure(
                text=f"✅ Welcome back, {self.current_user}!",
                text_color=COL["success"])
            # Check for saved quiz progress
            self._check_quiz_resume()
        else:
            self._login_msg.configure(
                text=f"❌ {d.get('error', 'Login failed')}",
                text_color=COL["danger"])

    def _do_logout(self):
        self.current_user = None
        self.user_id      = None
        self._refresh_account_box()
        self._login_msg.configure(text="✅ Logged out.", text_color=COL["muted"])

    def _do_register(self):
        username = self._reg_user.get().strip()
        email    = self._reg_email.get().strip()
        password = self._reg_pass.get()
        ok, msg  = validate_register_form(username, email, password)
        if not ok:
            self._reg_msg.configure(text=f"⚠️ {msg}", text_color=COL["warning"])
            return
        def fetch():
            try:
                r = self._api("post", "/auth/register",
                              json={"username": username,
                                    "email": email, "password": password})
                d = r.json()
                self.after(0, lambda: self._reg_msg.configure(
                    text="✅ Account created! You can now login."
                    if d.get("success") else f"❌ {d.get('error','Failed')}",
                    text_color=COL["success"] if d.get("success") else COL["danger"]))
            except Exception as e:
                self.after(0, lambda: self._reg_msg.configure(
                    text=f"❌ {e}", text_color=COL["danger"]))
        threading.Thread(target=fetch, daemon=True).start()

    # ═══════════════════════════════════════════════════════════
    #  QUIZ  — with resume, save progress, save results to profile
    # ═══════════════════════════════════════════════════════════
    def _build_quiz(self):
        f = self.frames["quiz"]
        self._header(f, "📝 Career Matching Quiz",
                     "Answer all 5 questions — AI will match you to ideal careers")
        self._quiz_body = ctk.CTkFrame(f, fg_color="transparent")
        self._quiz_body.pack(fill="x", padx=40, pady=6)
        self._render_quiz_step()

    def _check_quiz_resume(self):
        """Called after login — check if there's saved progress."""
        if not self.user_id:
            return
        def fetch():
            try:
                r = self._api("get", f"/quiz/progress/{self.user_id}")
                d = r.json()
                if d.get("found") and d.get("answers"):
                    self.after(0, lambda: self._offer_quiz_resume(d["answers"]))
            except:
                pass
        threading.Thread(target=fetch, daemon=True).start()

    def _offer_quiz_resume(self, saved_answers):
        """Show a banner offering to resume the quiz."""
        # Show it on the auth page as a prompt
        resume_bar = ctk.CTkFrame(self.frames["auth"],
                                  fg_color=COL["primary"], corner_radius=10)
        resume_bar.pack(fill="x", padx=40, pady=10)
        ctk.CTkLabel(resume_bar,
                     text=f"📝  You have a quiz in progress ({len(saved_answers)}/5 answered).",
                     font=F("body_bold"), text_color="white").pack(side="left", padx=16, pady=12)
        ctk.CTkButton(resume_bar, text="Resume Quiz →",
                      fg_color=COL["accent"], font=F("small_bold"),
                      height=32, width=130,
                      command=lambda: self._resume_quiz(saved_answers)).pack(
            side="right", padx=16, pady=10)

    def _resume_quiz(self, saved_answers):
        self.quiz_answers = saved_answers
        self.quiz_step    = len(saved_answers)
        self.show_frame("quiz")

    def _render_quiz_step(self):
        for w in self._quiz_body.winfo_children():
            w.destroy()
        if self.quiz_step >= len(QUIZ_QUESTIONS):
            self._show_quiz_results()
            return

        q = QUIZ_QUESTIONS[self.quiz_step]
        pct = self.quiz_step / len(QUIZ_QUESTIONS)

        ctk.CTkLabel(self._quiz_body,
                     text=f"Question {self.quiz_step + 1} of {len(QUIZ_QUESTIONS)}",
                     font=F("small"), text_color=COL["muted"]).pack(anchor="w")
        bar = ctk.CTkProgressBar(self._quiz_body, width=750, height=8,
                                  fg_color=COL["border"],
                                  progress_color=COL["primary"])
        bar.pack(anchor="w", pady=(4, 18))
        bar.set(pct)

        # Login reminder
        if not self.user_id:
            ctk.CTkLabel(self._quiz_body,
                         text="💡  Login to save your progress and resume later.",
                         font=F("small"), text_color=COL["warning"]).pack(
                anchor="w", pady=(0, 8))

        card = self._card(self._quiz_body)
        card.pack(fill="x", pady=8)
        ctk.CTkLabel(card, text=q["q"], font=F("quiz_q"),
                     text_color=COL["text"], wraplength=700).pack(
            padx=30, pady=(28, 20))
        for opt in q["options"]:
            ctk.CTkButton(card, text=opt,
                          fg_color=COL["panel"], hover_color=COL["primary"],
                          font=F("quiz_opt"), text_color=COL["text"],
                          height=46, width=680, corner_radius=8,
                          border_width=1, border_color=COL["border"],
                          command=lambda o=opt: self._quiz_select(o)).pack(pady=4, padx=30)
        ctk.CTkFrame(card, height=18, fg_color="transparent").pack()

        if self.quiz_step > 0:
            ctk.CTkButton(self._quiz_body, text="← Back",
                          fg_color=COL["border"], font=F("small"),
                          width=100, height=34,
                          command=self._quiz_back).pack(anchor="w", pady=10)

    def _quiz_select(self, answer):
        if self.quiz_step < len(self.quiz_answers):
            self.quiz_answers[self.quiz_step] = answer
        else:
            self.quiz_answers.append(answer)
        self.quiz_step += 1
        # Auto-save progress if logged in
        if self.user_id and self.quiz_step < len(QUIZ_QUESTIONS):
            threading.Thread(target=self._save_quiz_progress, daemon=True).start()
        self._render_quiz_step()

    def _save_quiz_progress(self):
        try:
            self._api("post", "/quiz/progress",
                      json={"user_id": self.user_id,
                            "answers": self.quiz_answers})
        except:
            pass

    def _quiz_back(self):
        if self.quiz_step > 0:
            self.quiz_step -= 1
            if len(self.quiz_answers) > self.quiz_step:
                self.quiz_answers.pop()
            self._render_quiz_step()

    def _show_quiz_results(self):
        for w in self._quiz_body.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._quiz_body,
                     text="🤖 Analysing with Groq AI...",
                     font=F("body"), text_color=COL["highlight"]).pack(pady=24)
        prog = ctk.CTkProgressBar(self._quiz_body, width=400, mode="indeterminate",
                                   progress_color=COL["primary"],
                                   fg_color=COL["border"])
        prog.pack()
        prog.start()
        self.update()

        def fetch():
            try:
                r = self._api("post", "/quiz",
                              json={"answers": self.quiz_answers,
                                    "user_id": self.user_id})
                d = r.json()
            except Exception as e:
                d = {"error": str(e)}
            prog.stop()
            self.after(0, lambda: self._display_quiz_results(d))
        threading.Thread(target=fetch, daemon=True).start()

    def _display_quiz_results(self, data):
        for w in self._quiz_body.winfo_children():
            w.destroy()
        if "error" in data:
            ctk.CTkLabel(self._quiz_body, text=f"❌ {data['error']}",
                         text_color=COL["danger"], font=F("body")).pack(pady=20)
            return

        ctk.CTkLabel(self._quiz_body, text="🎉 Your Career Matches",
                     font=F("heading"), text_color=COL["success"]).pack(pady=(10, 6))

        if self.user_id:
            ctk.CTkLabel(self._quiz_body,
                         text="✅ Results saved to your profile.",
                         font=F("small"), text_color=COL["muted"]).pack()

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, career in enumerate(data.get("matched_careers", [])):
            c = self._card(self._quiz_body, height=62)
            c.pack(fill="x", pady=4)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=f"  {medals[i]}  {career}",
                         font=F("body_bold"), text_color=COL["text"]).pack(
                side="left", padx=16, pady=10)
            ctk.CTkButton(c, text="View Resources",
                          fg_color=COL["info"], font=F("small_bold"),
                          width=130, height=30,
                          command=lambda cn=career: self._go_career_resources(cn)).pack(
                side="right", padx=16)

        ai_card = self._card(self._quiz_body)
        ai_card.pack(fill="x", pady=14)
        ctk.CTkLabel(ai_card, text="🤖  Groq AI Career Counsellor:",
                     font=F("body_bold"), text_color=COL["highlight"]).pack(
            anchor="w", padx=22, pady=(18, 6))
        ctk.CTkLabel(ai_card,
                     text=data.get("ai_analysis", "Analysis unavailable."),
                     font=F("body"), text_color=COL["text_dim"],
                     wraplength=740, justify="left").pack(padx=22, pady=(0, 18))

        row = ctk.CTkFrame(self._quiz_body, fg_color="transparent")
        row.pack(pady=14)
        ctk.CTkButton(row, text="🔄  Retake Quiz", fg_color=COL["primary"],
                      command=self._reset_quiz, width=150, height=40).pack(
            side="left", padx=8)
        ctk.CTkButton(row, text="💼  Browse Careers", fg_color=COL["accent"],
                      command=lambda: self.show_frame("careers"),
                      width=160, height=40).pack(side="left", padx=8)

    def _go_career_resources(self, career_name):
        """Navigate to resources filtered for a specific career."""
        self.selected_career = career_name
        self.show_frame("resources")

    def _reset_quiz(self):
        self.quiz_answers = []
        self.quiz_step    = 0
        self._render_quiz_step()

    # ═══════════════════════════════════════════════════════════
    #  CAREERS — dynamic filters, sorting, deduplication
    # ═══════════════════════════════════════════════════════════
    def _build_careers(self):
        f = self.frames["careers"]
        self._header(f, "💼 Browse Careers",
                     "Search, filter and sort all career paths")

        ctrl = ctk.CTkFrame(f, fg_color="transparent")
        ctrl.pack(fill="x", padx=40, pady=(0, 4))

        # Search
        self._career_search = ctk.CTkEntry(
            ctrl, placeholder_text="🔍  Search title, skill, or description...",
            width=280, height=40, fg_color=COL["input_bg"],
            border_color=COL["border"])
        self._career_search.pack(side="left", padx=(0, 8))
        self._career_search.bind("<KeyRelease>", lambda _: self._filter_careers())

        # Category filter
        self._cat_var = tk.StringVar(value="All")
        ctk.CTkOptionMenu(ctrl, variable=self._cat_var,
                          values=CAREER_CATEGORIES,
                          fg_color=COL["card"], button_color=COL["primary"],
                          button_hover_color=COL["primary_hover"],
                          dropdown_fg_color=COL["panel"],
                          width=160, height=40,
                          command=lambda _: self._filter_careers()).pack(
            side="left", padx=6)

        # Sort
        self._sort_var = tk.StringVar(value="A–Z")
        ctk.CTkOptionMenu(ctrl, variable=self._sort_var,
                          values=["A–Z", "Z–A", "Salary ↑", "Salary ↓",
                                  "Growth: Excellent", "Growth: Good"],
                          fg_color=COL["card"], button_color=COL["primary"],
                          button_hover_color=COL["primary_hover"],
                          dropdown_fg_color=COL["panel"],
                          width=160, height=40,
                          command=lambda _: self._filter_careers()).pack(
            side="left", padx=6)

        ctk.CTkButton(ctrl, text="🔄", fg_color=COL["border"],
                      width=44, height=40,
                      command=self._load_careers).pack(side="left", padx=4)

        self._career_count = ctk.CTkLabel(ctrl, text="",
                                          font=F("small"), text_color=COL["muted"])
        self._career_count.pack(side="right", padx=10)

        self._career_list = ctk.CTkFrame(f, fg_color="transparent")
        self._career_list.pack(fill="both", expand=True, padx=40, pady=6)

    def _load_careers(self):
        def fetch():
            try:
                r = self._api("get", "/careers")
                # Deduplicate by title
                seen = set()
                careers = []
                for c in r.json():
                    if c["title"] not in seen:
                        seen.add(c["title"])
                        careers.append(c)
                self.all_careers = careers
                self.after(0, self._filter_careers)
            except Exception as e:
                print(f"[careers] {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def _filter_careers(self):
        search  = self._career_search.get().lower()
        cat     = self._cat_var.get()
        sort_by = self._sort_var.get()

        results = []
        for c in self.all_careers:
            if cat != "All" and c.get("category") != cat:
                continue
            text = (c.get("title","") + c.get("description","") +
                    c.get("skills_required","")).lower()
            if search and search not in text:
                continue
            results.append(c)

        # Sort
        def salary_key(c):
            s = c.get("avg_salary","M 0")
            try:
                return int("".join(filter(str.isdigit, s.split("–")[0])))
            except:
                return 0

        growth_rank = {"Excellent": 3, "Good": 2, "Moderate": 1, "Stable": 0}
        if sort_by == "A–Z":
            results.sort(key=lambda c: c.get("title",""))
        elif sort_by == "Z–A":
            results.sort(key=lambda c: c.get("title",""), reverse=True)
        elif sort_by == "Salary ↑":
            results.sort(key=salary_key)
        elif sort_by == "Salary ↓":
            results.sort(key=salary_key, reverse=True)
        elif sort_by == "Growth: Excellent":
            results = [c for c in results if c.get("growth_outlook") == "Excellent"]
        elif sort_by == "Growth: Good":
            results = [c for c in results if c.get("growth_outlook") in ("Excellent","Good")]

        for w in self._career_list.winfo_children():
            w.destroy()
        for career in results:
            self._render_career_card(self._career_list, career)
        self._career_count.configure(text=f"{len(results)} result(s)")

    def _render_career_card(self, parent, career):
        cat_color = CATEGORY_COLOURS.get(career.get("category",""), COL["cat_default"])
        c = self._card(parent)
        c.pack(fill="x", pady=5)

        top = ctk.CTkFrame(c, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(14, 4))
        ctk.CTkLabel(top, text=career.get("title",""),
                     font=F("subheading"), text_color=COL["text"]).pack(side="left")
        ctk.CTkLabel(top, text=f"  {career.get('category','')}  ",
                     font=F("badge"), fg_color=cat_color,
                     corner_radius=6, text_color="#000").pack(side="right", padx=4)

        ctk.CTkLabel(c, text=career.get("description",""),
                     font=F("body"), text_color=COL["muted"],
                     wraplength=760, justify="left").pack(anchor="w", padx=20, pady=4)

        sk_row = ctk.CTkFrame(c, fg_color="transparent")
        sk_row.pack(fill="x", padx=20, pady=(2, 4))
        ctk.CTkLabel(sk_row, text="🛠 Skills: ", font=F("small_bold"),
                     text_color=COL["highlight"]).pack(side="left")
        skills = career.get("skills_required","").split(",")
        ctk.CTkLabel(sk_row,
                     text=" · ".join(s.strip() for s in skills[:5]),
                     font=F("small"), text_color=COL["text_dim"]).pack(side="left")

        info = ctk.CTkFrame(c, fg_color="transparent")
        info.pack(fill="x", padx=20, pady=(0, 4))
        ctk.CTkLabel(info, text=f"💰 {career.get('avg_salary','N/A')}",
                     font=F("body_bold"), text_color=COL["success"]).pack(
            side="left", padx=(0, 20))
        ctk.CTkLabel(info, text=f"📈 {career.get('growth_outlook','N/A')}",
                     font=F("body"), text_color=COL["warning"]).pack(side="left")

        btn_row = ctk.CTkFrame(c, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 12))
        for label, color, cmd in [
            ("❤️ Save",       COL["danger"],   lambda cid=career["id"]: self._save_favourite(cid)),
            ("⚖️ Compare",    COL["primary"],  lambda cc=career: self._add_compare(cc)),
            ("📚 Resources",  COL["info"],     lambda cn=career.get("title",""): self._go_career_resources(cn)),
            ("🔍 Skill Gap",  COL["success"],  lambda cn=career.get("title",""): self._go_skillgap(cn)),
            ("🤖 AI Advice",  COL["warning"],  lambda cn=career.get("title",""): self._show_ai_advice(cn)),
        ]:
            ctk.CTkButton(btn_row, text=label, fg_color=color,
                          font=F("small_bold"), width=110, height=32,
                          command=cmd).pack(side="right", padx=4)

    def _save_favourite(self, career_id):
        if not self.user_id:
            messagebox.showwarning("Login Required", "Please login to save favourites.")
            return
        def fetch():
            try:
                r = self._api("post", "/favourites",
                              json={"user_id": self.user_id, "career_id": career_id})
                d = r.json()
                msg = "❤️ Saved to favourites!" if d.get("success") else d.get("message","Done")
                self.after(0, lambda: messagebox.showinfo("Favourites", msg))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=fetch, daemon=True).start()

    def _add_compare(self, career):
        if len(self.compare_list) >= 3:
            messagebox.showwarning("Compare", "Max 3 careers. Clear list first.")
            return
        if any(c["id"] == career["id"] for c in self.compare_list):
            messagebox.showinfo("Compare", f"{career['title']} is already added.")
            return
        self.compare_list.append(career)
        messagebox.showinfo("Compare",
            f"✅ {career['title']} added ({len(self.compare_list)}/3)\n"
            "Go to ⚖️ Compare tab to see the comparison.")

    def _go_skillgap(self, career_name):
        self.selected_career = career_name
        self.show_frame("skillgap")
        self._prefill_skillgap(career_name)

    def _show_ai_advice(self, career_title):
        win = ctk.CTkToplevel(self)
        win.title(f"🤖 AI Advice — {career_title}")
        win.geometry("620x400")
        win.configure(fg_color=COL["panel"])
        ctk.CTkLabel(win, text=f"🤖  {career_title} — AI Career Advice",
                     font=F("subheading"), text_color=COL["highlight"]).pack(
            pady=(20, 8), padx=20)
        box = ctk.CTkTextbox(win, fg_color=COL["card"], text_color=COL["text"],
                              font=F("body"), width=580, height=300)
        box.pack(padx=20, pady=10)
        box.insert("1.0", "Fetching Groq AI advice...")
        box.configure(state="disabled")

        def fetch():
            try:
                r = self._api("post", "/ai/advice", json={"career": career_title})
                text = r.json().get("advice", "No advice returned.")
            except Exception as e:
                text = f"Error: {e}"
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("1.0", text)
            box.configure(state="disabled")
        threading.Thread(target=fetch, daemon=True).start()

    # ═══════════════════════════════════════════════════════════
    #  RESOURCES — filtered by selected career, no duplicates
    # ═══════════════════════════════════════════════════════════
    def _build_resources(self):
        f = self.frames["resources"]
        self._header(f, "📚 Learning Resources",
                     "Search and filter videos, articles and courses by career")

        # ── Row 1: Search box ─────────────────────────────────
        row1 = ctk.CTkFrame(f, fg_color="transparent")
        row1.pack(fill="x", padx=40, pady=(0, 6))

        self._res_search = ctk.CTkEntry(
            row1, placeholder_text="🔍  Search resources by title or description...",
            width=420, height=40,
            fg_color=COL["input_bg"], border_color=COL["border"])
        self._res_search.pack(side="left", padx=(0, 8))
        self._res_search.bind("<KeyRelease>", lambda _: self._apply_res_filters())

        ctk.CTkButton(row1, text="🔄  Refresh",
                      fg_color=COL["border"], font=F("small_bold"),
                      width=90, height=40,
                      command=self._load_resources).pack(side="left", padx=4)

        self._res_count = ctk.CTkLabel(row1, text="", font=F("small"),
                                       text_color=COL["muted"])
        self._res_count.pack(side="right", padx=10)

        # ── Row 2: Career filter + Type filter ────────────────
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=40, pady=(0, 10))

        ctk.CTkLabel(row2, text="Career:", font=F("small_bold"),
                     text_color=COL["muted"]).pack(side="left", padx=(0, 6))
        self._res_filter_var = tk.StringVar(value="All Careers")
        self._res_career_menu = ctk.CTkOptionMenu(
            row2, variable=self._res_filter_var, values=["All Careers"],
            fg_color=COL["card"], button_color=COL["primary"],
            button_hover_color=COL["primary_hover"],
            dropdown_fg_color=COL["panel"], width=240, height=38,
            command=lambda _: self._apply_res_filters())
        self._res_career_menu.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row2, text="Type:", font=F("small_bold"),
                     text_color=COL["muted"]).pack(side="left", padx=(0, 6))
        self._res_type_var = tk.StringVar(value="All Types")
        ctk.CTkOptionMenu(row2, variable=self._res_type_var,
                          values=["All Types", "Video", "Article", "Course"],
                          fg_color=COL["card"], button_color=COL["primary"],
                          button_hover_color=COL["primary_hover"],
                          dropdown_fg_color=COL["panel"], width=150, height=38,
                          command=lambda _: self._apply_res_filters()).pack(
            side="left")

        self._res_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._res_frame.pack(fill="both", expand=True, padx=40)

        # Cache for loaded resources + maps
        self._res_cache       = []
        self._res_id_to_name  = {}
        self._res_name_to_id  = {}

    def _load_resources(self):
        """Fetch all resources and careers from API, cache locally, then render."""
        for w in self._res_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._res_frame, text="Loading resources...",
                     font=F("body"), text_color=COL["highlight"]).pack(pady=20)

        def fetch():
            try:
                rc = self._api("get", "/careers").json()
                rr = self._api("get", "/resources").json()
                career_names  = ["All Careers"] + list(dict.fromkeys(c["title"] for c in rc))
                id_to_name    = {c["id"]: c["title"] for c in rc}
                name_to_id    = {c["title"]: c["id"] for c in rc}
                self.after(0, lambda: self._on_resources_loaded(
                    rr, career_names, id_to_name, name_to_id))
            except Exception as e:
                self.after(0, lambda: ctk.CTkLabel(
                    self._res_frame, text=f"❌ Error: {e}",
                    text_color=COL["danger"], font=F("body")).pack(pady=20))
        threading.Thread(target=fetch, daemon=True).start()

    def _on_resources_loaded(self, resources, career_names, id_to_name, name_to_id):
        """Cache data, update dropdown, then apply filters."""
        # Deduplicate resources by URL before caching
        seen_urls = set()
        clean = []
        for res in resources:
            url = res.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                res["_career_name"] = id_to_name.get(res.get("career_id"), "General")
                clean.append(res)
        self._res_cache      = clean
        self._res_id_to_name = id_to_name
        self._res_name_to_id = name_to_id

        # Update career dropdown
        self._res_career_menu.configure(values=career_names)

        # Pre-select career if navigated from another tab
        if self.selected_career and self.selected_career in career_names:
            self._res_filter_var.set(self.selected_career)
            self.selected_career = None
        else:
            self._res_filter_var.set("All Careers")

        self._apply_res_filters()

    def _apply_res_filters(self):
        """Filter cached resources by search text, career and type — no API call."""
        search     = self._res_search.get().lower().strip()
        sel_career = self._res_filter_var.get()
        sel_type   = self._res_type_var.get()

        filtered = []
        for res in self._res_cache:
            # Career filter
            if sel_career != "All Careers":
                cid = self._res_name_to_id.get(sel_career)
                if res.get("career_id") != cid:
                    continue
            # Type filter
            if sel_type != "All Types" and res.get("type","") != sel_type:
                continue
            # Search filter
            if search:
                haystack = (res.get("title","") + " " +
                            res.get("description","") + " " +
                            res.get("_career_name","")).lower()
                if search not in haystack:
                    continue
            filtered.append(res)

        # Render
        for w in self._res_frame.winfo_children():
            w.destroy()

        if not filtered:
            ctk.CTkLabel(self._res_frame,
                         text="No resources found for this filter combination.",
                         font=F("body"), text_color=COL["muted"]).pack(pady=40)
            self._res_count.configure(text="0 resource(s)")
            return

        icons = {"Video": "🎬", "Article": "📄", "Course": "🎓"}
        for res in filtered:
            c = self._card(self._res_frame)
            c.pack(fill="x", pady=5)

            top_row = ctk.CTkFrame(c, fg_color="transparent")
            top_row.pack(fill="x", padx=20, pady=(14, 4))
            icon = icons.get(res.get("type",""), "🔗")
            ctk.CTkLabel(top_row, text=f"{icon}  {res.get('title','')}",
                         font=F("body_bold"), text_color=COL["highlight"]).pack(side="left")
            type_color = {"Video": COL["danger"], "Article": COL["primary"],
                          "Course": COL["success"]}.get(res.get("type",""), COL["muted"])
            ctk.CTkLabel(top_row, text=f"  {res.get('type','')}  ",
                         font=F("badge"), fg_color=type_color,
                         corner_radius=6, text_color="white").pack(side="right")

            # Career category badge
            cat_row = ctk.CTkFrame(c, fg_color="transparent")
            cat_row.pack(fill="x", padx=20, pady=(0, 4))
            career_name = res.get("_career_name", "General")
            cat_color = COL["primary"]
            # Find category for this career
            ctk.CTkLabel(cat_row, text=f"📁  {career_name}",
                         font=F("small_bold"), text_color=COL["accent"]).pack(side="left")

            ctk.CTkLabel(c, text=res.get("description",""),
                         font=F("body"), text_color=COL["text_dim"]).pack(
                anchor="w", padx=20, pady=(0, 4))

            url = res.get("url","")
            ctk.CTkButton(c, text=f"🌐  Open: {url[:70]}",
                          fg_color="transparent", hover_color=COL["border"],
                          text_color=COL["primary"], font=F("small"), anchor="w",
                          command=lambda u=url: webbrowser.open(u)).pack(
                anchor="w", padx=20, pady=(0, 12))

        self._res_count.configure(text=f"{len(filtered)} resource(s)")

    # ═══════════════════════════════════════════════════════════
    #  COMPARE — improved info, add from list
    # ═══════════════════════════════════════════════════════════
    def _build_compare(self):
        f = self.frames["compare"]
        self._header(f, "⚖️ Career Comparison",
                     "Add up to 3 careers and compare them side by side")

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.pack(fill="x", padx=40, pady=(0, 8))

        ctk.CTkButton(top, text="➕  Add Career",
                      fg_color=COL["success"], font=F("body_bold"),
                      height=38, width=140,
                      command=self._open_add_compare).pack(side="left", padx=(0, 8))
        ctk.CTkButton(top, text="🗑️  Clear All",
                      fg_color=COL["danger"], font=F("body_bold"),
                      height=38, width=120,
                      command=self._clear_compare).pack(side="left")
        self._compare_hint = ctk.CTkLabel(top,
                                          text=f"  {len(self.compare_list)}/3 careers added",
                                          font=F("small"), text_color=COL["muted"])
        self._compare_hint.pack(side="left", padx=16)

        self._compare_body = ctk.CTkFrame(f, fg_color="transparent")
        self._compare_body.pack(fill="both", expand=True, padx=40, pady=8)

    def _open_add_compare(self):
        """Popup to pick a career to add."""
        win = ctk.CTkToplevel(self)
        win.title("Add Career to Compare")
        win.geometry("500x520")
        win.configure(fg_color=COL["panel"])
        win.lift()
        win.attributes("-topmost", True)

        ctk.CTkLabel(win, text="Select a career to compare:",
                     font=F("subheading"), text_color=COL["accent"]).pack(pady=(20,10), padx=20)

        search_e = ctk.CTkEntry(win, placeholder_text="🔍 Filter...",
                                width=440, height=36,
                                fg_color=COL["input_bg"], border_color=COL["border"])
        search_e.pack(padx=20, pady=(0,8))

        scroll = ctk.CTkScrollableFrame(win, fg_color=COL["bg"],
                                        height=360, width=450)
        scroll.pack(padx=20, pady=4, fill="both", expand=True)

        def populate(filter_text=""):
            for w in scroll.winfo_children():
                w.destroy()
            for career in self.all_careers:
                if filter_text.lower() not in career["title"].lower():
                    continue
                row = ctk.CTkFrame(scroll, fg_color=COL["card"],
                                   corner_radius=8)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=career["title"],
                             font=F("body_bold"),
                             text_color=COL["text"]).pack(side="left", padx=12, pady=8)
                cat_color = CATEGORY_COLOURS.get(career.get("category",""), COL["cat_default"])
                ctk.CTkLabel(row, text=f" {career.get('category','')} ",
                             font=F("badge"), fg_color=cat_color,
                             corner_radius=5, text_color="#000").pack(side="left")
                ctk.CTkButton(row, text="Add ➕",
                              fg_color=COL["primary"], font=F("small_bold"),
                              width=70, height=28,
                              command=lambda cc=career: (
                                  self._add_compare(cc), win.destroy()
                              )).pack(side="right", padx=10)

        populate()
        search_e.bind("<KeyRelease>", lambda _: populate(search_e.get()))

    def _render_compare(self):
        for w in self._compare_body.winfo_children():
            w.destroy()
        self._compare_hint.configure(
            text=f"  {len(self.compare_list)}/3 careers added")

        if not self.compare_list:
            ctk.CTkLabel(self._compare_body,
                         text="No careers added yet.\nClick ➕ Add Career or go to Browse Careers → ⚖️ Compare.",
                         font=F("body"), text_color=COL["muted"]).pack(pady=60)
            return

        # Comparison table
        cols = len(self.compare_list)
        fields = [
            ("Category",        "category",       COL["highlight"]),
            ("Avg Salary",      "avg_salary",      COL["success"]),
            ("Growth Outlook",  "growth_outlook",  COL["warning"]),
            ("Skills Required", "skills_required", COL["text"]),
            ("Description",     "description",     COL["text_dim"]),
        ]

        # Header row
        hdr = ctk.CTkFrame(self._compare_body, fg_color=COL["card"],
                           corner_radius=10)
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="", width=160,
                     font=F("body_bold")).grid(row=0, column=0, padx=10, pady=10)
        for i, career in enumerate(self.compare_list):
            cat_color = CATEGORY_COLOURS.get(career.get("category",""), COL["cat_default"])
            col_frame = ctk.CTkFrame(hdr, fg_color=cat_color, corner_radius=8)
            col_frame.grid(row=0, column=i+1, padx=8, pady=10, sticky="ew")
            ctk.CTkLabel(col_frame, text=career["title"],
                         font=F("body_bold"), text_color="#000",
                         wraplength=220).pack(padx=10, pady=8)

        # Data rows
        for fi, (label, key, color) in enumerate(fields):
            row_f = ctk.CTkFrame(self._compare_body,
                                 fg_color=COL["card"] if fi % 2 == 0 else COL["panel"],
                                 corner_radius=0)
            row_f.pack(fill="x", pady=1)
            ctk.CTkLabel(row_f, text=label, width=160,
                         font=F("small_bold"),
                         text_color=COL["muted"]).grid(row=0, column=0, padx=10, pady=8)
            for i, career in enumerate(self.compare_list):
                val = career.get(key, "N/A")
                if key == "skills_required":
                    val = "\n".join(f"• {s.strip()}" for s in val.split(",")[:5])
                ctk.CTkLabel(row_f, text=val, width=230,
                             font=F("small"), text_color=color,
                             wraplength=220, justify="left").grid(
                    row=0, column=i+1, padx=8, pady=8, sticky="w")

        # Verdict row — highlight best salary
        verdict = ctk.CTkFrame(self._compare_body,
                               fg_color=COL["selected"], corner_radius=10)
        verdict.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(verdict, text="🏆 Best Salary",
                     font=F("small_bold"), text_color=COL["warning"]).pack(
            side="left", padx=16, pady=10)

        def parse_sal(c):
            try:
                return int("".join(filter(str.isdigit,
                           c.get("avg_salary","M 0").split("–")[0])))
            except:
                return 0
        best = max(self.compare_list, key=parse_sal)
        ctk.CTkLabel(verdict, text=f"  {best['title']} — {best.get('avg_salary','')}",
                     font=F("body_bold"), text_color=COL["success"]).pack(
            side="left", pady=10)

    def _clear_compare(self):
        self.compare_list = []
        self._render_compare()

    # ═══════════════════════════════════════════════════════════
    #  FAVOURITES
    # ═══════════════════════════════════════════════════════════
    def _build_favourites(self):
        f = self.frames["favourites"]
        self._header(f, "❤️ My Favourite Careers", "Your personally saved career paths")
        self._fav_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._fav_frame.pack(fill="both", expand=True, padx=40)

    def _load_favourites(self):
        for w in self._fav_frame.winfo_children():
            w.destroy()
        if not self.user_id:
            ctk.CTkLabel(self._fav_frame,
                         text="Please login to view your saved careers.",
                         font=F("body"), text_color=COL["muted"]).pack(pady=50)
            return
        def fetch():
            try:
                r    = self._api("get", f"/favourites/{self.user_id}")
                favs = r.json()
                self.after(0, lambda: self._display_favourites(favs))
            except Exception as e:
                self.after(0, lambda: ctk.CTkLabel(
                    self._fav_frame, text=f"Error: {e}",
                    text_color=COL["danger"]).pack(pady=20))
        threading.Thread(target=fetch, daemon=True).start()

    def _display_favourites(self, favs):
        for w in self._fav_frame.winfo_children():
            w.destroy()
        if not favs:
            ctk.CTkLabel(self._fav_frame,
                         text="No favourites yet. Browse careers and click ❤️ Save.",
                         font=F("body"), text_color=COL["muted"]).pack(pady=50)
            return
        for career in favs:
            self._render_career_card(self._fav_frame, career)

    # ═══════════════════════════════════════════════════════════
    #  SKILL GAP ANALYSIS
    # ═══════════════════════════════════════════════════════════
    def _build_skillgap(self):
        f = self.frames["skillgap"]
        self._header(f, "🔍 Skill Gap Analysis",
                     "Compare your current skills against any career — see exactly what to learn")

        form = self._card(f)
        form.pack(fill="x", padx=40, pady=(0, 16))

        ctk.CTkLabel(form, text="Select Career:", font=F("body_bold"),
                     text_color=COL["text"]).pack(anchor="w", padx=20, pady=(16, 4))
        self._sg_career_var = tk.StringVar(value="Software Engineer")
        self._sg_career_menu = ctk.CTkOptionMenu(
            form, variable=self._sg_career_var, values=["Software Engineer"],
            fg_color=COL["card"], button_color=COL["primary"],
            button_hover_color=COL["primary_hover"],
            dropdown_fg_color=COL["panel"], width=400, height=38)
        self._sg_career_menu.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(form, text="Your Current Skills (comma separated):",
                     font=F("body_bold"), text_color=COL["text"]).pack(
            anchor="w", padx=20, pady=(4, 4))
        ctk.CTkLabel(form,
                     text='e.g.  Python, Communication, Excel, Problem Solving',
                     font=F("small"), text_color=COL["muted"]).pack(anchor="w", padx=20)
        self._sg_skills = ctk.CTkTextbox(form, height=80, width=760,
                                          fg_color=COL["input_bg"],
                                          border_color=COL["border"],
                                          border_width=1,
                                          text_color=COL["text"],
                                          font=F("body"))
        self._sg_skills.pack(padx=20, pady=(4, 10))

        ctk.CTkButton(form, text="🔍  Analyse Skill Gap",
                      fg_color=COL["primary"], hover_color=COL["primary_hover"],
                      font=F("body_bold"), height=42, width=220,
                      command=self._run_skillgap).pack(padx=20, pady=(0, 16))

        self._sg_result = ctk.CTkFrame(f, fg_color="transparent")
        self._sg_result.pack(fill="both", expand=True, padx=40)

        # Load career names into dropdown
        def load_careers():
            try:
                r = self._api("get", "/careers")
                names = list(dict.fromkeys(c["title"] for c in r.json()))
                self.after(0, lambda: self._sg_career_menu.configure(values=names))
            except:
                pass
        threading.Thread(target=load_careers, daemon=True).start()

    def _prefill_skillgap(self, career_name):
        self._sg_career_var.set(career_name)

    def _run_skillgap(self):
        career     = self._sg_career_var.get()
        user_skills= self._sg_skills.get("1.0", "end").strip()
        if not user_skills:
            messagebox.showwarning("Skill Gap", "Please enter your current skills.")
            return
        for w in self._sg_result.winfo_children():
            w.destroy()
        loading = ctk.CTkLabel(self._sg_result,
                               text="🤖 Analysing with Groq AI...",
                               font=F("body"), text_color=COL["highlight"])
        loading.pack(pady=20)
        prog = ctk.CTkProgressBar(self._sg_result, width=400, mode="indeterminate",
                                   progress_color=COL["primary"],
                                   fg_color=COL["border"])
        prog.pack()
        prog.start()
        self.update()

        def fetch():
            try:
                r = self._api("post", "/skill-gap",
                              json={"career": career, "user_skills": user_skills})
                d = r.json()
            except Exception as e:
                d = {"error": str(e)}
            prog.stop()
            self.after(0, lambda: self._display_skillgap(d))
        threading.Thread(target=fetch, daemon=True).start()

    def _display_skillgap(self, data):
        for w in self._sg_result.winfo_children():
            w.destroy()
        if "error" in data:
            ctk.CTkLabel(self._sg_result, text=f"❌ {data['error']}",
                         text_color=COL["danger"], font=F("body")).pack(pady=20)
            return

        # Readiness meter
        pct = int(data.get("readiness_percent", 0)) / 100
        meter_card = self._card(self._sg_result)
        meter_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(meter_card,
                     text=f"🎯 Readiness for {data.get('career','')}",
                     font=F("subheading"), text_color=COL["accent"]).pack(
            anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(meter_card,
                     text=f"{int(pct*100)}% Ready",
                     font=F("heading"),
                     text_color=COL["success"] if pct >= 0.6 else COL["warning"] if pct >= 0.3 else COL["danger"]
                     ).pack(anchor="w", padx=20)
        bar = ctk.CTkProgressBar(meter_card, width=700, height=16,
                                  fg_color=COL["border"],
                                  progress_color=COL["success"] if pct >= 0.6 else COL["warning"])
        bar.pack(padx=20, pady=(4, 16))
        bar.set(pct)

        # Two columns: matching vs missing
        cols = ctk.CTkFrame(self._sg_result, fg_color="transparent")
        cols.pack(fill="x", pady=6)

        # Matching skills
        match_card = self._card(cols)
        match_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(match_card, text="✅  Skills You Have",
                     font=F("body_bold"), text_color=COL["success"]).pack(
            anchor="w", padx=16, pady=(14, 6))
        matching = data.get("matching_skills", [])
        if matching:
            for sk in matching:
                ctk.CTkLabel(match_card, text=f"  ✓  {sk}",
                             font=F("body"), text_color=COL["text"]).pack(
                    anchor="w", padx=16, pady=2)
        else:
            ctk.CTkLabel(match_card, text="  None detected yet.",
                         font=F("small"), text_color=COL["muted"]).pack(
                anchor="w", padx=16)
        ctk.CTkFrame(match_card, height=14, fg_color="transparent").pack()

        # Missing skills
        miss_card = self._card(cols)
        miss_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ctk.CTkLabel(miss_card, text="❌  Skills to Learn",
                     font=F("body_bold"), text_color=COL["danger"]).pack(
            anchor="w", padx=16, pady=(14, 6))
        missing = data.get("missing_skills", [])
        if missing:
            for sk in missing:
                ctk.CTkLabel(miss_card, text=f"  •  {sk}",
                             font=F("body"), text_color=COL["warning"]).pack(
                    anchor="w", padx=16, pady=2)
        else:
            ctk.CTkLabel(miss_card, text="  You have all key skills! 🎉",
                         font=F("small"), text_color=COL["success"]).pack(
                anchor="w", padx=16)
        ctk.CTkFrame(miss_card, height=14, fg_color="transparent").pack()

        # Learning plan
        plan_card = self._card(self._sg_result)
        plan_card.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(plan_card, text="📋  Your Learning Plan",
                     font=F("body_bold"), text_color=COL["highlight"]).pack(
            anchor="w", padx=20, pady=(14, 6))
        plan = data.get("learning_plan", [])
        for i, step in enumerate(plan, 1):
            ctk.CTkLabel(plan_card, text=f"  {i}.  {step}",
                         font=F("body"), text_color=COL["text"],
                         wraplength=720, justify="left").pack(
                anchor="w", padx=20, pady=4)
        ctk.CTkButton(plan_card, text="📚  Find Resources for This Career",
                      fg_color=COL["info"], font=F("body_bold"),
                      height=38, width=260,
                      command=lambda: self._go_career_resources(
                          data.get("career",""))).pack(
            anchor="w", padx=20, pady=(10, 16))

    # ═══════════════════════════════════════════════════════════
    #  ANALYTICS — more info + AI summary
    # ═══════════════════════════════════════════════════════════
    def _build_analytics(self):
        f = self.frames["analytics"]
        self._header(f, "📊 Analytics Dashboard",
                     "Career distribution, platform stats and AI insights")
        self._analytics_body = ctk.CTkFrame(f, fg_color="transparent")
        self._analytics_body.pack(fill="both", expand=True, padx=40)

    def _load_analytics(self):
        for w in self._analytics_body.winfo_children():
            w.destroy()
        loading = ctk.CTkLabel(self._analytics_body,
                               text="📊 Loading analytics...",
                               font=F("body"), text_color=COL["highlight"])
        loading.pack(pady=20)
        self.update()

        def fetch():
            try:
                r  = self._api("get", "/analytics/summary")
                d  = r.json()
                r2 = self._api("get", "/careers")
                careers = r2.json()
                self.after(0, lambda: self._display_analytics(d, careers))
            except Exception as e:
                self.after(0, lambda: ctk.CTkLabel(
                    self._analytics_body, text=f"❌ {e}",
                    text_color=COL["danger"]).pack(pady=20))
        threading.Thread(target=fetch, daemon=True).start()

    def _display_analytics(self, summary_data, careers):
        for w in self._analytics_body.winfo_children():
            w.destroy()

        # ── AI Summary card ───────────────────────────────────
        ai_card = self._card(self._analytics_body)
        ai_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(ai_card, text="🤖  AI Analytics Summary",
                     font=F("body_bold"), text_color=COL["highlight"]).pack(
            anchor="w", padx=20, pady=(14, 6))
        ctk.CTkLabel(ai_card,
                     text=summary_data.get("summary", "Summary unavailable."),
                     font=F("body"), text_color=COL["text_dim"],
                     wraplength=860, justify="left").pack(padx=20, pady=(0, 14))

        # ── Stats row ─────────────────────────────────────────
        stats = summary_data.get("stats", {})
        stats_row = ctk.CTkFrame(self._analytics_body, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))
        for val, lbl, color in [
            (str(stats.get("total_users",    0)), "Registered Users",   COL["primary"]),
            (str(stats.get("total_careers",  0)), "Career Listings",    COL["accent"]),
            (str(stats.get("total_quizzes",  0)), "Quizzes Taken",      COL["success"]),
            (str(stats.get("total_resources",0)), "Learning Resources", COL["info"]),
        ]:
            c = self._card(stats_row, height=90)
            c.pack(side="left", fill="x", expand=True, padx=5)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=val, font=F("stat"),
                         text_color=color).pack(pady=(14, 0))
            ctk.CTkLabel(c, text=lbl, font=F("small"),
                         text_color=COL["muted"]).pack()

        if not HAS_MATPLOTLIB:
            ctk.CTkLabel(self._analytics_body,
                         text="📦 Install matplotlib for charts:\n"
                              "pip install matplotlib --break-system-packages",
                         font=F("body"), text_color=COL["warning"]).pack(pady=20)
            return

        # ── Build chart data ──────────────────────────────────
        cats = {}
        growth = {}
        for c in careers:
            cat = c.get("category","Other")
            cats[cat] = cats.get(cat, 0) + 1
            g = c.get("growth_outlook","Other")
            growth[g] = growth.get(g, 0) + 1

        fig = Figure(figsize=(11, 8), facecolor=COL["bg"])

        # Pie — categories
        ax1 = fig.add_subplot(221)
        ax1.set_facecolor(COL["card"])
        colours = [CATEGORY_COLOURS.get(k, "#AAAAAA") for k in cats]
        ax1.pie(list(cats.values()), labels=list(cats.keys()),
                colors=colours, autopct="%1.0f%%",
                textprops={"color": COL["text"], "fontsize": 7},
                pctdistance=0.78,
                wedgeprops={"linewidth": 1.5, "edgecolor": COL["bg"]})
        ax1.set_title("Career Categories", color=COL["accent"], fontsize=10, pad=8)

        # Bar — careers per category
        ax2 = fig.add_subplot(222)
        ax2.set_facecolor(COL["card"])
        bar_colors = [CATEGORY_COLOURS.get(k, "#AAAAAA") for k in cats]
        bars = ax2.barh(list(cats.keys()), list(cats.values()),
                        color=bar_colors, edgecolor=COL["bg"], height=0.6)
        ax2.set_xlabel("Count", color=COL["muted"], fontsize=8)
        ax2.set_title("Careers per Category", color=COL["accent"], fontsize=10, pad=8)
        ax2.tick_params(colors=COL["text"], labelsize=7)
        for spine in ax2.spines.values():
            spine.set_edgecolor(COL["border"])
        for bar, val in zip(bars, cats.values()):
            ax2.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                     str(val), va="center", color=COL["text"], fontsize=8)

        # Pie — growth outlook
        ax3 = fig.add_subplot(223)
        ax3.set_facecolor(COL["card"])
        growth_colors = {
            "Excellent": COL["success"], "Good": COL["info"],
            "Moderate": COL["warning"], "Stable": COL["primary"]
        }
        gcols = [growth_colors.get(k, "#AAAAAA") for k in growth]
        ax3.pie(list(growth.values()), labels=list(growth.keys()),
                colors=gcols, autopct="%1.0f%%",
                textprops={"color": COL["text"], "fontsize": 8},
                wedgeprops={"linewidth": 1.5, "edgecolor": COL["bg"]})
        ax3.set_title("Growth Outlook Distribution", color=COL["accent"], fontsize=10, pad=8)

        # Bar — salary ranges (top 8)
        ax4 = fig.add_subplot(224)
        ax4.set_facecolor(COL["card"])
        def parse_max_sal(c):
            try:
                parts = c.get("avg_salary","M 0").replace("M","").replace(",","").split("–")
                return int("".join(filter(str.isdigit, parts[-1].strip())))
            except:
                return 0
        top8 = sorted(careers, key=parse_max_sal, reverse=True)[:8]
        names  = [c["title"][:18] for c in top8]
        sals   = [parse_max_sal(c) for c in top8]
        scols  = [CATEGORY_COLOURS.get(c.get("category",""), "#AAAAAA") for c in top8]
        ax4.barh(names, sals, color=scols, edgecolor=COL["bg"], height=0.6)
        ax4.set_xlabel("Max Salary (USD)", color=COL["muted"], fontsize=8)
        ax4.set_title("Top 8 Highest Paying Careers", color=COL["accent"], fontsize=10, pad=8)
        ax4.tick_params(colors=COL["text"], labelsize=7)
        for spine in ax4.spines.values():
            spine.set_edgecolor(COL["border"])

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=self._analytics_body)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

        # Chart explanations
        exp_card = self._card(self._analytics_body)
        exp_card.pack(fill="x", pady=(8, 20))
        ctk.CTkLabel(exp_card, text="📖  Chart Explanations",
                     font=F("body_bold"), text_color=COL["highlight"]).pack(
            anchor="w", padx=20, pady=(14, 6))
        explanations = [
            ("Top-Left Pie",   "Shows the proportion of careers per industry category on the platform."),
            ("Top-Right Bar",  "Shows the count of careers listed in each category — longer bar = more options."),
            ("Bottom-Left Pie","Shows what percentage of careers have Excellent, Good, Moderate or Stable growth."),
            ("Bottom-Right Bar","Shows the top 8 highest paying careers by maximum salary. Colour = category."),
        ]
        for chart, desc in explanations:
            row = ctk.CTkFrame(exp_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=f"• {chart}:", font=F("small_bold"),
                         text_color=COL["accent"], width=140).pack(side="left")
            ctk.CTkLabel(row, text=desc, font=F("small"),
                         text_color=COL["text_dim"], wraplength=680,
                         justify="left").pack(side="left")
        ctk.CTkFrame(exp_card, height=12, fg_color="transparent").pack()
