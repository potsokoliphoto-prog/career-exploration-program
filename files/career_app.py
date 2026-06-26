"""
╔══════════════════════════════════════════════════════════════╗
║         career_app.py  —  MAIN ENTRY POINT                  ║
║  Run:  python career_app.py                                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import time
import sys

from config   import BASE_URL, APP_NAME, FLASK_PORT
from database import init_db
from logic    import launch_flask_thread


def wait_for_flask(max_tries=25, delay=0.3):
    try:
        import requests
        for _ in range(max_tries):
            try:
                r = requests.get(f"{BASE_URL}/status", timeout=1)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(delay)
    except ImportError:
        time.sleep(2)
    return False


def main():
    # 1 — Init DB
    print(f"[{APP_NAME}] Initialising database...")
    try:
        init_db()
        print(f"[{APP_NAME}] Database OK.")
    except Exception as e:
        print(f"[ERROR] Database: {e}")
        sys.exit(1)

    # 2 — Start Flask
    print(f"[{APP_NAME}] Starting Flask on port {FLASK_PORT}...")
    try:
        launch_flask_thread()
    except Exception as e:
        print(f"[ERROR] Flask: {e}")
        sys.exit(1)

    # 3 — Import CTk and build window FIRST, then show splash inside it
    print(f"[{APP_NAME}] Building GUI...")
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        from ui import CareerApp, SplashScreen

        # Create main window immediately (visible)
        app = CareerApp()

        # Show splash overlay inside the already-open window
        splash = SplashScreen(app)
        splash.set_status("Initialising database... OK")
        app.update()
        time.sleep(0.5)

        splash.set_status("Waiting for API server...")
        app.update()

        # Wait for Flask in small steps, keeping GUI responsive
        ready = False
        try:
            import requests
            for _ in range(25):
                try:
                    r = requests.get(f"{BASE_URL}/status", timeout=0.5)
                    if r.status_code == 200:
                        ready = True
                        break
                except Exception:
                    pass
                time.sleep(0.3)
                app.update()
        except ImportError:
            time.sleep(2)
            app.update()

        if ready:
            splash.set_status("API ready!")
        else:
            splash.set_status("Starting up...")
        app.update()
        time.sleep(0.4)

        splash.close()
        app.update()

        print(f"[{APP_NAME}] GUI launched. API at {BASE_URL}")
        app.mainloop()

    except Exception as e:
        import traceback
        print(f"\n[CRASH] GUI error:\n")
        traceback.print_exc()
        input("\nPress Enter to close...")
        sys.exit(1)


if __name__ == "__main__":
    main()