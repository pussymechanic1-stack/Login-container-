from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
import sqlite3
import hashlib
import subprocess
import re
import os

# =========================
# ENVIRONMENT
# =========================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "development-only-secret"
)

DB = os.getenv(
    "DATABASE_URL",
    "sqlite:///users.db"
)

# Convert SQLite URL to a normal filesystem path
if DB.startswith("sqlite:///"):
    DB = DB.replace("sqlite:///", "", 1)


# =========================
# DATABASE
# =========================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_user(username):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    return user


def get_user_count():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")

    count = cursor.fetchone()[0]

    conn.close()

    return count


# =========================
# SYSTEM COMMAND
# =========================

def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.stdout.strip()

    except Exception:
        return ""


# =========================
# BATTERY
# =========================

def get_battery():

    output = run_command(["termux-battery-status"])

    percentage = "--"
    temperature = "--"
    status = "Unknown"

    match = re.search(r'"percentage":\s*(\d+)', output)

    if match:
        percentage = match.group(1) + "%"

    match = re.search(r'"temperature":\s*"([^"]+)"', output)

    if match:
        temperature = match.group(1) + "°C"

    match = re.search(r'"status":\s*"([^"]+)"', output)

    if match:
        status = match.group(1).title()

    return percentage, temperature, status


# =========================
# MEMORY
# =========================

def get_memory():

    output = run_command(["free", "-h"])

    total = "--"
    used = "--"
    available = "--"

    for line in output.splitlines():

        if line.startswith("Mem:"):

            parts = line.split()

            if len(parts) >= 7:

                total = parts[1]
                used = parts[2]
                available = parts[6]

    return total, used, available


# =========================
# UPTIME
# =========================

def get_uptime():

    output = run_command(["uptime"])

    match = re.search(
        r"up\s+(.+?),\s+\d+\s+user",
        output
    )

    if match:
        return match.group(1)

    return "--"


# =========================
# STORAGE
# =========================

def get_storage():

    output = run_command(
        ["df", "-h", "/storage/emulated"]
    )

    for line in output.splitlines():

        if "/storage/emulated" in line:

            parts = line.split()

            if len(parts) >= 5:

                total = parts[1]
                used = parts[2]
                available = parts[3]
                percent = parts[4]

                return total, used, available, percent

    return "--", "--", "--", "--"


# =========================
# LIVE STATS API
# =========================

@app.route("/api/stats")
def api_stats():

    if "username" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    battery, temperature, battery_status = get_battery()

    mem_total, mem_used, mem_available = get_memory()

    uptime = get_uptime()

    storage_total, storage_used, storage_available, storage_percent = get_storage()

    return {
        "battery": battery,
        "temperature": temperature,
        "battery_status": battery_status,

        "memory": {
            "total": mem_total,
            "used": mem_used,
            "available": mem_available
        },

        "uptime": uptime,

        "storage": {
            "total": storage_total,
            "used": storage_used,
            "available": storage_available,
            "percent": storage_percent
        }
    }


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "username" not in session:
        return redirect("/login")

    return redirect("/dashboard")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = get_user(username)

        if user:

            user_id, db_username, stored_password, role = user

            if hash_password(password) == stored_password:

                session["user_id"] = user_id
                session["username"] = db_username
                session["role"] = role

                return redirect("/dashboard")

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/login")

    battery, temperature, battery_status = get_battery()

    mem_total, mem_used, mem_available = get_memory()

    uptime = get_uptime()

    storage_total, storage_used, storage_available, storage_percent = get_storage()

    users = get_user_count()

    return render_template(
        "dashboard.html",

        username=session["username"],
        role=session["role"],

        battery=battery,
        temperature=temperature,
        battery_status=battery_status,

        mem_total=mem_total,
        mem_used=mem_used,
        mem_available=mem_available,

        uptime=uptime,

        storage_total=storage_total,
        storage_used=storage_used,
        storage_available=storage_available,
        storage_percent=storage_percent,

        users=users
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    debug_mode = os.getenv(
        "FLASK_DEBUG",
        "0"
    ).lower() in ("1", "true", "yes")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug_mode
    )

