"""
High School Management System API

A FastAPI application that allows students to view and sign up
for extracurricular activities and manages student profiles in a persistent SQLite database.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities with persistent student profiles",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)

# Persistent database configuration
DATABASE_PATH = current_dir / "students.db"
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "secret-token")

# In-memory activity catalog; participant lists are hydrated from the database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": [],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": [],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": [],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": [],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": [],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": [],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": [],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": [],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": [],
    },
}

connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
connection.row_factory = sqlite3.Row


class StudentCreate(BaseModel):
    email: str
    name: str
    admission_number: Optional[str] = None
    grade: Optional[str] = None
    faculty: Optional[str] = None
    year: Optional[str] = None
    town: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    admission_number: Optional[str] = None
    grade: Optional[str] = None
    faculty: Optional[str] = None
    year: Optional[str] = None
    town: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    notes: Optional[str] = None


def init_db() -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                email TEXT PRIMARY KEY,
                admission_number TEXT UNIQUE,
                name TEXT NOT NULL,
                grade TEXT,
                faculty TEXT,
                year TEXT,
                town TEXT,
                dob TEXT,
                gender TEXT,
                notes TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_assignments (
                email TEXT NOT NULL,
                activity TEXT NOT NULL,
                PRIMARY KEY (email, activity),
                FOREIGN KEY (email) REFERENCES students(email)
            )
            """
        )
    load_activity_assignments()


def load_activity_assignments() -> None:
    for item in activities.values():
        item["participants"] = []

    assignments = connection.execute(
        "SELECT email, activity FROM activity_assignments"
    ).fetchall()
    for row in assignments:
        activity = row["activity"]
        email = row["email"]
        if activity in activities and email not in activities[activity]["participants"]:
            activities[activity]["participants"].append(email)


def require_admin(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")) -> None:
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


def student_record_to_dict(row: sqlite3.Row) -> dict:
    assignments = connection.execute(
        "SELECT activity FROM activity_assignments WHERE email = ?",
        (row["email"],),
    ).fetchall()
    return {
        "email": row["email"],
        "name": row["name"],
        "admission_number": row["admission_number"],
        "grade": row["grade"],
        "faculty": row["faculty"],
        "year": row["year"],
        "town": row["town"],
        "dob": row["dob"],
        "gender": row["gender"],
        "notes": row["notes"],
        "registered_activities": [assignment["activity"] for assignment in assignments],
    }


def get_student_by_email(email: str) -> Optional[sqlite3.Row]:
    row = connection.execute(
        "SELECT * FROM students WHERE email = ?", (email,)
    ).fetchone()
    return row


def get_student_by_admission_number(admission_number: str) -> Optional[sqlite3.Row]:
    row = connection.execute(
        "SELECT * FROM students WHERE admission_number = ?",
        (admission_number,),
    ).fetchone()
    return row


def search_students(name: Optional[str], admission_number: Optional[str]) -> List[sqlite3.Row]:
    if admission_number:
        return connection.execute(
            "SELECT * FROM students WHERE admission_number = ?",
            (admission_number,),
        ).fetchall()

    if name:
        wildcard_name = f"%{name}%"
        return connection.execute(
            "SELECT * FROM students WHERE name LIKE ?", (wildcard_name,),
        ).fetchall()

    return connection.execute("SELECT * FROM students").fetchall()


def ensure_student_exists(email: str) -> sqlite3.Row:
    student = get_student_by_email(email)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


init_db()


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities() -> dict:
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    student = get_student_by_email(email)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student record not found. Please create the student profile first."
        )

    activity = activities[activity_name]
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    with connection:
        connection.execute(
            "INSERT INTO activity_assignments (email, activity) VALUES (?, ?)",
            (email, activity_name),
        )

    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    with connection:
        connection.execute(
            "DELETE FROM activity_assignments WHERE email = ? AND activity = ?",
            (email, activity_name),
        )

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.get("/students")
def list_students(name: Optional[str] = None, admission_number: Optional[str] = None) -> List[dict]:
    rows = search_students(name, admission_number)
    return [student_record_to_dict(row) for row in rows]


@app.get("/students/{email}")
def get_student(email: str) -> dict:
    row = get_student_by_email(email)
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_record_to_dict(row)


@app.post("/students", dependencies=[Depends(require_admin)], status_code=201)
def create_student(student: StudentCreate) -> dict:
    if get_student_by_email(student.email):
        raise HTTPException(status_code=400, detail="Student already exists")

    try:
        with connection:
            connection.execute(
                "INSERT INTO students (email, admission_number, name, grade, faculty, year, town, dob, gender, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    student.email,
                    student.admission_number,
                    student.name,
                    student.grade,
                    student.faculty,
                    student.year,
                    student.town,
                    student.dob,
                    student.gender,
                    student.notes,
                ),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Admission number or email already exists")

    return student.dict()


@app.patch("/students/{email}", dependencies=[Depends(require_admin)])
def update_student(email: str, student: StudentUpdate) -> dict:
    existing = get_student_by_email(email)
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")

    updated_data = {**existing, **student.dict(exclude_none=True)}
    try:
        with connection:
            connection.execute(
                "UPDATE students SET name = ?, admission_number = ?, grade = ?, faculty = ?, year = ?, town = ?, dob = ?, gender = ?, notes = ? WHERE email = ?",
                (
                    updated_data["name"],
                    updated_data["admission_number"],
                    updated_data["grade"],
                    updated_data["faculty"],
                    updated_data["year"],
                    updated_data["town"],
                    updated_data["dob"],
                    updated_data["gender"],
                    updated_data["notes"],
                    email,
                ),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Admission number already exists")

    return student_record_to_dict(get_student_by_email(email))


@app.delete("/students/{email}", dependencies=[Depends(require_admin)])
def delete_student(email: str) -> dict:
    existing = get_student_by_email(email)
    if not existing:
        raise HTTPException(status_code=404, detail="Student not found")

    with connection:
        connection.execute("DELETE FROM activity_assignments WHERE email = ?", (email,))
        connection.execute("DELETE FROM students WHERE email = ?", (email,))

    for activity in activities.values():
        if email in activity["participants"]:
            activity["participants"].remove(email)

    return {"message": f"Deleted student {email}"}
