import time
import ctypes
from datetime import datetime

import win32gui
import win32process
import psutil

from database import init_db, add_activity


# ============================================================
# SETTINGS
# ============================================================

CHECK_INTERVAL = 5
IDLE_LIMIT = 60


# ============================================================
# PRODUCTIVE APPLICATIONS
# ============================================================

PRODUCTIVE_APPS = {
    "code.exe",
    "pycharm64.exe",
    "idea64.exe",
    "devenv.exe",
    "eclipse.exe",
    "notepad.exe",
    "notepad++.exe",
    "winword.exe",
    "powerpnt.exe",
    "excel.exe",
    "acrord32.exe",
    "sumatrapdf.exe"
}


# ============================================================
# DISTRACTION APPLICATIONS
# ============================================================

DISTRACTION_APPS = {
    "discord.exe",
    "steam.exe",
    "spotify.exe"
}


# ============================================================
# WINDOWS IDLE INFORMATION
# ============================================================

class LASTINPUTINFO(ctypes.Structure):

    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]


# ============================================================
# GET IDLE TIME
# ============================================================

def get_idle_seconds():

    info = LASTINPUTINFO()

    info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if ctypes.windll.user32.GetLastInputInfo(
        ctypes.byref(info)
    ):

        millis = (
            ctypes.windll.kernel32.GetTickCount()
            - info.dwTime
        )

        return millis / 1000.0

    return 0.0


# ============================================================
# GET ACTIVE WINDOW
# ============================================================

def get_active_window():

    try:

        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return "Unknown", "Unknown"

        title = win32gui.GetWindowText(hwnd)

        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:

            process_name = psutil.Process(pid).name()

        except Exception:

            process_name = "Unknown"

        return process_name, title

    except Exception:

        return "Unknown", "Unknown"


# ============================================================
# CLASSIFY APPLICATION
# ============================================================

def classify_application(app_name, window_title):

    app = app_name.lower()
    title = window_title.lower()


    # Direct productive applications

    if app in PRODUCTIVE_APPS:
        return "Productive"


    # Direct distraction applications

    if app in DISTRACTION_APPS:
        return "Distraction"


    # Browser applications

    browsers = {
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
        "opera.exe"
    }


    if app in browsers:

        distraction_words = [

            "youtube",
            "instagram",
            "facebook",
            "netflix",
            "tiktok",
            "reddit",
            "twitter",
            "x.com",
            "prime video",
            "spotify"

        ]


        productive_words = [

            "github",
            "stackoverflow",
            "w3schools",
            "geeksforgeeks",
            "coursera",
            "udemy",
            "kaggle",
            "documentation",
            "python",
            "machine learning",
            "research",
            "google scholar"

        ]


        if any(
            word in title
            for word in distraction_words
        ):

            return "Distraction"


        if any(
            word in title
            for word in productive_words
        ):

            return "Productive"


        return "Neutral"


    return "Neutral"


# ============================================================
# SAVE SESSION
# ============================================================

def save_session(
    app_name,
    window_title,
    start_time,
    end_time,
    idle_seconds
):

    duration = max(
        0,
        end_time - start_time
    )

    category = classify_application(
        app_name,
        window_title
    )


    if idle_seconds >= IDLE_LIMIT:

        category = "Idle"


    add_activity(

        app_name,
        window_title,
        category,
        duration,
        min(
            duration,
            idle_seconds
        )

    )


# ============================================================
# RUN TRACKER
# ============================================================

def run_tracker():

    init_db()


    print("=" * 60)

    print(
        "LIFELENS AI ACTIVITY TRACKER"
    )

    print("=" * 60)

    print(
        "Tracking started automatically."
    )

    print(
        "Keep this window minimized."
    )

    print(
        "Close it to stop tracking.\n"
    )


    last_app = None

    last_title = None

    session_start = time.time()


    try:

        while True:

            app_name, window_title = (
                get_active_window()
            )

            now = time.time()


            # Detect application/window change

            if (
                app_name != last_app
                or window_title != last_title
            ):

                if last_app is not None:

                    idle = get_idle_seconds()

                    save_session(

                        last_app,
                        last_title,
                        session_start,
                        now,
                        idle

                    )


                last_app = app_name

                last_title = window_title

                session_start = now


            # Determine category

            category = classify_application(

                app_name,
                window_title

            )


            # Check idle status

            if get_idle_seconds() >= IDLE_LIMIT:

                category = "Idle"


            print(

                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"{app_name:25} | "
                f"{category:12} | "
                f"{window_title[:55]}"

            )


            time.sleep(CHECK_INTERVAL)


    except KeyboardInterrupt:

        pass


    finally:

        now = time.time()


        if last_app is not None:

            save_session(

                last_app,
                last_title,
                session_start,
                now,
                get_idle_seconds()

            )


        print(
            "\nTracker stopped."
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_tracker()