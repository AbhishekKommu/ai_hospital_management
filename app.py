"""
=============================================================
 AI Hospital Management System
 Complete, Production-Ready Flask Application
=============================================================
"""

import os
import sqlite3
import logging
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================
# APP CONFIG
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ai_hospital_super_secret_key_2025_change_me"
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_FOLDER, "hospital.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================
# DATABASE HELPERS
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(conn):
    try:
        if conn:
            conn.close()
    except Exception as e:
        logger.warning(f"DB close error: {e}")


def init_db():
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'staff',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER DEFAULT 0,
                gender TEXT DEFAULT 'Other',
                phone TEXT DEFAULT '',
                diagnosis TEXT DEFAULT '',
                status TEXT DEFAULT 'Stable',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT DEFAULT 'General',
                phone TEXT DEFAULT '',
                available TEXT DEFAULT 'Yes',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                date TEXT DEFAULT '',
                time TEXT DEFAULT '',
                department TEXT DEFAULT 'General',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed admin
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "admin")
            )
            logger.info("Seeded admin user (admin/admin123)")

        # Seed doctors
        cur.execute("SELECT COUNT(*) FROM doctors")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                """INSERT INTO doctors (name, department, phone, available)
                   VALUES (?, ?, ?, ?)""",
                [
                    ("Dr. A. Sharma", "Cardiology", "9876543210", "Yes"),
                    ("Dr. P. Nair", "Neurology", "9876543211", "Yes"),
                    ("Dr. S. Gupta", "Pediatrics", "9876543212", "No"),
                    ("Dr. R. Verma", "Orthopedics", "9876543213", "Yes"),
                    ("Dr. K. Iyer", "Dermatology", "9876543214", "Yes"),
                ]
            )
            logger.info("Seeded sample doctors")

        # Seed patients
        cur.execute("SELECT COUNT(*) FROM patients")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                """INSERT INTO patients (name, age, gender, phone, diagnosis, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    ("John Doe", 58, "Male", "9000011111", "Hypertension", "Stable"),
                    ("Sarah Kim", 34, "Female", "9000022222", "Migraine", "Recovering"),
                    ("Raj Mehta", 67, "Male", "9000033333", "Cardiac Arrhythmia", "Critical"),
                    ("Emma Watson", 29, "Female", "9000044444", "Fracture", "Stable"),
                    ("Aarav Patel", 45, "Male", "9000055555", "Diabetes Type 2", "Recovering"),
                ]
            )
            logger.info("Seeded sample patients")

        # Seed appointments
        cur.execute("SELECT COUNT(*) FROM appointments")
        if cur.fetchone()[0] == 0:
            today = datetime.now().strftime("%Y-%m-%d")
            cur.executemany(
                """INSERT INTO appointments
                   (patient_name, doctor_name, date, time, department)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    ("John Doe", "Dr. A. Sharma", today, "09:30", "Cardiology"),
                    ("Sarah Kim", "Dr. P. Nair", today, "11:15", "Neurology"),
                    ("Emma Watson", "Dr. S. Gupta", today, "14:00", "Pediatrics"),
                    ("Raj Mehta", "Dr. R. Verma", today, "16:30", "Orthopedics"),
                ]
            )
            logger.info("Seeded sample appointments")

        conn.commit()
        logger.info(f"Database ready at {DB_PATH}")

    except Exception as e:
        conn.rollback()
        logger.error(f"DB init failed: {e}")
        raise
    finally:
        close_db(conn)


# ============================================================
# AUTH DECORATOR
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {e}")
    return "<h1>500 - Internal Server Error</h1>", 500


# ============================================================
# CONTEXT PROCESSOR
# ============================================================
@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year,
        "app_name": "AI Hospital",
    }


# ============================================================
# AUTH ROUTES
# ============================================================
@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        conn = get_db()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        finally:
            close_db(conn)

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not username or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
            return render_template("register.html")

        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()

            if existing:
                flash("Username already taken.", "danger")
                return render_template("register.html")

            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Registration failed: {e}")
            flash("Registration failed. Try again.", "danger")
            return render_template("register.html")
        finally:
            close_db(conn)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    try:
        stats = {
            "patients": conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] or 0,
            "doctors": conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] or 0,
            "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] or 0,
            "available": conn.execute(
                "SELECT COUNT(*) FROM doctors WHERE available = 'Yes'"
            ).fetchone()[0] or 0,
        }
        recent_patients = conn.execute(
            "SELECT * FROM patients ORDER BY id DESC LIMIT 5"
        ).fetchall() or []
        doctors = conn.execute(
            "SELECT * FROM doctors ORDER BY id DESC LIMIT 5"
        ).fetchall() or []
        appointments = conn.execute(
            "SELECT * FROM appointments ORDER BY id DESC LIMIT 5"
        ).fetchall() or []
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        stats = {"patients": 0, "doctors": 0, "appointments": 0, "available": 0}
        recent_patients, doctors, appointments = [], [], []
    finally:
        close_db(conn)

    return render_template(
        "dashboard.html",
        stats=stats,
        patients=recent_patients,
        doctors=doctors,
        appointments=appointments,
    )


# ============================================================
# PATIENTS
# ============================================================
@app.route("/patients")
@login_required
def patients():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM patients ORDER BY id DESC"
        ).fetchall() or []
    except Exception as e:
        logger.error(f"Patients error: {e}")
        rows = []
    finally:
        close_db(conn)
    return render_template("patients.html", patients=rows)


@app.route("/add_patient", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        age_raw = (request.form.get("age") or "0").strip()
        gender = (request.form.get("gender") or "Other").strip()
        phone = (request.form.get("phone") or "").strip()
        diagnosis = (request.form.get("diagnosis") or "").strip()
        status = (request.form.get("status") or "Stable").strip()

        if not name:
            flash("Patient name is required.", "danger")
            return render_template("add_patient.html")

        try:
            age = int(age_raw) if age_raw else 0
            age = max(0, min(age, 130))
        except ValueError:
            age = 0

        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO patients
                   (name, age, gender, phone, diagnosis, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, age, gender, phone, diagnosis, status)
            )
            conn.commit()
            flash(f"Patient '{name}' added successfully!", "success")
        except Exception as e:
            conn.rollback()
            logger.error(f"Add patient error: {e}")
            flash("Failed to add patient.", "danger")
        finally:
            close_db(conn)

        return redirect(url_for("patients"))

    return render_template("add_patient.html")


@app.route("/delete_patient/<int:pid>", methods=["POST"])
@login_required
def delete_patient(pid):
    conn = get_db()
    try:
        conn.execute("DELETE FROM patients WHERE id = ?", (pid,))
        conn.commit()
        flash("Patient deleted.", "success")
    except Exception as e:
        conn.rollback()
        logger.error(f"Delete patient error: {e}")
        flash("Failed to delete.", "danger")
    finally:
        close_db(conn)
    return redirect(url_for("patients"))


# ============================================================
# DOCTORS
# ============================================================
@app.route("/doctors")
@login_required
def doctors():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM doctors ORDER BY id DESC"
        ).fetchall() or []
    except Exception as e:
        logger.error(f"Doctors error: {e}")
        rows = []
    finally:
        close_db(conn)
    return render_template("doctors.html", doctors=rows)


# ============================================================
# APPOINTMENTS
# ============================================================
@app.route("/appointments")
@login_required
def appointments():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM appointments ORDER BY date DESC, time DESC"
        ).fetchall() or []
    except Exception as e:
        logger.error(f"Appointments error: {e}")
        rows = []
    finally:
        close_db(conn)
    return render_template("appointments.html", appointments=rows)


@app.route("/add_appointment", methods=["GET", "POST"])
@login_required
def add_appointment():
    if request.method == "POST":
        patient_name = (request.form.get("patient_name") or "").strip()
        doctor_name = (request.form.get("doctor_name") or "").strip()
        department = (request.form.get("department") or "General").strip()
        date = (request.form.get("date") or "").strip()
        time = (request.form.get("time") or "").strip()

        if not patient_name or not doctor_name or not date or not time:
            flash("All fields are required.", "danger")
            return redirect(url_for("add_appointment"))

        conn = get_db()
        try:
            conn.execute(
                """INSERT INTO appointments
                   (patient_name, doctor_name, date, time, department)
                   VALUES (?, ?, ?, ?, ?)""",
                (patient_name, doctor_name, date, time, department)
            )
            conn.commit()
            flash("Appointment booked successfully!", "success")
        except Exception as e:
            conn.rollback()
            logger.error(f"Add appointment error: {e}")
            flash("Failed to book appointment.", "danger")
        finally:
            close_db(conn)

        return redirect(url_for("appointments"))

    conn = get_db()
    try:
        docs = conn.execute(
            "SELECT name, department FROM doctors ORDER BY name"
        ).fetchall() or []
    except Exception as e:
        logger.error(f"Doctors load error: {e}")
        docs = []
    finally:
        close_db(conn)

    return render_template("add_appointment.html", doctors=docs)


# ============================================================
# API
# ============================================================
@app.route("/api/stats")
@login_required
def api_stats():
    conn = get_db()
    try:
        stats = {
            "patients": conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "doctors": conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
            "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
            "available": conn.execute(
                "SELECT COUNT(*) FROM doctors WHERE available='Yes'"
            ).fetchone()[0],
        }
    except Exception as e:
        logger.error(f"API error: {e}")
        stats = {}
    finally:
        close_db(conn)
    return jsonify(stats)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 60)
    print("  🏥 AI HOSPITAL MANAGEMENT SYSTEM")
    print("=" * 60)
    print(f"  Database : {DB_PATH}")
    print(f"  Server   : http://127.0.0.1:5000")
    print(f"  Login    : admin / admin123")
    print("=" * 60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=True)