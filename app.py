from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cybershield_secret_key"


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("cybershield.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        fraud_type TEXT,
        priority TEXT DEFAULT 'Medium',
        description TEXT,
        status TEXT DEFAULT 'Pending',
        case_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test")
def test():
    return "SYSTEM OK"


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("cybershield.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
        """, (
            request.form["username"],
            request.form["email"].lower(),
            generate_password_hash(request.form["password"])
        ))

        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect("cybershield.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (request.form["email"].lower(),)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], request.form["password"]):
            session["user"] = user[1]
            session["role"] = user[4]
            session["logged_in"] = True
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


# ================= DASHBOARD (SOC INTELLIGENCE UPGRADE) =================
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("cybershield.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM reports")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Investigating'")
    investigating = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'")
    resolved = cursor.fetchone()[0]

    # SOC INTELLIGENCE: Top fraud types
    cursor.execute("""
        SELECT fraud_type, COUNT(*)
        FROM reports
        GROUP BY fraud_type
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    top_frauds = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=session["user"],
        total=total,
        pending=pending,
        investigating=investigating,
        resolved=resolved,
        top_frauds=top_frauds
    )


# ================= REPORT =================
@app.route("/report", methods=["GET", "POST"])
def report():
    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == "POST":
        case_id = f"CYB-{int(datetime.datetime.now().timestamp())}"
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("cybershield.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO reports (
            user, fraud_type, priority,
            description, status, case_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user"],
            request.form["fraud_type"],
            request.form.get("priority", "Medium"),
            request.form["description"],
            "Pending",
            case_id,
            created_at
        ))

        conn.commit()
        conn.close()

        return redirect("/my_reports")

    return render_template("report.html")


# ================= MY REPORTS =================
@app.route("/my_reports")
def my_reports():
    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("cybershield.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, fraud_type, priority, description, status, case_id, created_at
    FROM reports
    WHERE user = ?
    """, (session["user"],))

    reports = cursor.fetchall()
    conn.close()

    return render_template("my_reports.html", reports=reports)


# ================= LEARN =================
@app.route("/learn")
def learn():
    return render_template("learn.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)