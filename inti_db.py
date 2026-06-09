import sqlite3 
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

db_name='hiring_tracker.db'
SCHEMA = """

CREATE TABLE IF NOT EXISTS daycare (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL 
);



CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daycare_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                classification TEXT NOT NULL,
                experience TEXT NOT NULL,
                resume_path TEXT,
                cover_letter_path TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'new',
                interview_date TEXT,
                interview_time TEXT,
                interview_location TEXT,
                interview_email_sent_at TEXT,
                interview_notes TEXT,
                interview_rating INTEGER,
                first_aid_cpr_status TEXT DEFAULT 'pending',
                police_check_status TEXT DEFAULT 'pending',
                child_abuse_check_status TEXT DEFAULT 'pending',
                FOREIGN KEY (daycare_id) REFERENCES daycare(id),
                UNIQUE (daycare_id,email)
                );
 
CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password_hash TEXT NOT NULL,
                 role TEXT NOT NULL
                 
                 );
CREATE TABLE IF NOT EXISTS daycare_membership(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                daycare_id INTEGER NOT NULL,
                FOREIGN KEY (daycare_id) REFERENCES daycare(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
);"""

def main():
 conn = sqlite3.connect(db_name)
 conn.row_factory = sqlite3.Row
 cursor = conn.cursor()
 cursor.execute("PRAGMA foreign_keys = ON")
 cursor.executescript(SCHEMA)
 demo_daycare_name = os.getenv("DEMO_DAYCARE_NAME")
 demo_director_name = os.getenv("DEMO_DIRECTOR_NAME")
 demo_director_email = os.getenv("DEMO_DIRECTOR_EMAIL")
 demo_director_password = os.getenv("DEMO_DIRECTOR_PASSWORD")

 if demo_daycare_name and demo_director_name and demo_director_email and demo_director_password:
        demo_director_email = demo_director_email.strip().lower()

        daycare = cursor.execute(
            "SELECT id FROM daycare WHERE name = ?",
            (demo_daycare_name,)
        ).fetchone()

        if daycare:
            daycare_id = daycare["id"]
        else:
            cursor.execute(
                "INSERT INTO daycare (name) VALUES (?)",
                (demo_daycare_name,)
            )
            daycare_id = cursor.lastrowid

        user = cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (demo_director_email,)
        ).fetchone()

        if user:
            user_id = user["id"]
        else:
            password_hash = generate_password_hash(demo_director_password)

            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (demo_director_name, demo_director_email, password_hash, "director")
            )

            user_id = cursor.lastrowid

        membership = cursor.execute(
            """
            SELECT id FROM daycare_membership
            WHERE daycare_id = ? AND user_id = ?
            """,
            (daycare_id, user_id)
        ).fetchone()

        if not membership:
            cursor.execute(
                """
                INSERT INTO daycare_membership (daycare_id, user_id)
                VALUES (?, ?)
                """,
                (daycare_id, user_id)
            )

        print("Demo daycare/director setup complete.")
 else:
        print("Demo environment variables missing. Skipping demo director setup.")
 conn.commit()
 conn.close()
 print(f"database initialized:{db_name}")

if __name__=="__main__":
    main()

