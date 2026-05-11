import sqlite3 

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
                FOREIGN KEY (daycare_id) REFERENCES daycare(id),
                UNIQUE (daycare_id,email)
);
"""

def main():
 conn = sqlite3.connect(db_name)
 cursor = conn.cursor()
 cursor.execute("PRAGMA foreign_keys = ON")
 cursor.executescript(SCHEMA)
 conn.commit()
 conn.close()
 print(f"database initialized:{db_name}")

if __name__=="__main__":
    main()

