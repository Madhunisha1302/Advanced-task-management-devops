from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "tasks.db"


# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()


# -----------------------------
# HOME / DASHBOARD
# -----------------------------

@app.route("/")
def home():

    connection = get_db()

    search = request.args.get("search", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")

    query = "SELECT * FROM tasks WHERE 1=1"
    values = []

    # Search
    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        values.append(f"%{search}%")
        values.append(f"%{search}%")

    # Status filter
    if status:
        query += " AND status = ?"
        values.append(status)

    # Priority filter
    if priority:
        query += " AND priority = ?"
        values.append(priority)

    query += " ORDER BY id DESC"

    tasks = connection.execute(
        query,
        values
    ).fetchall()

    # Dashboard counts

    total = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    pending = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'Pending'"
    ).fetchone()[0]

    progress = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'In Progress'"
    ).fetchone()[0]

    completed = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = 'Completed'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        pending=pending,
        progress=progress,
        completed=completed,
        search=search,
        selected_status=status,
        selected_priority=priority
    )


# -----------------------------
# ADD TASK
# -----------------------------

@app.route("/add", methods=["POST"])
def add_task():

    title = request.form.get("title", "").strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    priority = request.form.get(
        "priority",
        "Medium"
    )

    due_date = request.form.get(
        "due_date",
        ""
    )

    if not title:
        return "Task title is required", 400

    connection = get_db()

    connection.execute("""
        INSERT INTO tasks
        (
            title,
            description,
            priority,
            status,
            due_date,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        priority,
        "Pending",
        due_date,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# -----------------------------
# UPDATE STATUS
# -----------------------------

@app.route(
    "/update/<int:task_id>",
    methods=["POST"]
)
def update_task(task_id):

    status = request.form.get(
        "status",
        "Pending"
    )

    # Allow only valid statuses
    valid_statuses = [
        "Pending",
        "In Progress",
        "Completed"
    ]

    if status not in valid_statuses:
        return "Invalid status", 400

    connection = get_db()

    connection.execute(
        """
        UPDATE tasks
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            task_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# -----------------------------
# DELETE TASK
# -----------------------------

@app.route(
    "/delete/<int:task_id>",
    methods=["POST"]
)
def delete_task(task_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


# -----------------------------
# HEALTH CHECK
# -----------------------------

@app.route("/health")
def health():

    return {
        "status": "healthy",
        "application": "Advanced Task Management System"
    }


# -----------------------------
# START APPLICATION
# -----------------------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )