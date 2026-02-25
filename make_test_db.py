"""Test database generator for the workout analyzer.

Creates a small, deterministic SQLite database (test.db)
used to validate correctness and invariant handling.
Not used by the analyzer at runtime.
"""

import sqlite3

DB_NAME = "test.db"

conn = sqlite3.connect(DB_NAME)

# ----------------------------------------------------------------------
# Reset schema 
# ----------------------------------------------------------------------

conn.execute("DROP TABLE IF EXISTS sets")
conn.execute("DROP TABLE IF EXISTS exercises")
conn.execute("DROP TABLE IF EXISTS sessions")

# ----------------------------------------------------------------------
# Create tables
# ----------------------------------------------------------------------

conn.execute("""
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL
)
""")

conn.execute("""
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
)
""")

conn.execute("""
CREATE TABLE sets (
    session_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL
)
""")

# ----------------------------------------------------------------------
# Insert deterministic test data
# ----------------------------------------------------------------------

conn.executemany(
    "INSERT INTO sessions VALUES (?, ?)",
    [
        (1, "2026-02-01"),
        (2, "2026-02-03"),
    ]
)

conn.executemany(
    "INSERT INTO exercises VALUES (?, ?)",
    [
        (1, "Squat"),
        (2, "Bench Press"),
        (3, "Deadlift"),
    ]
)

conn.executemany(
    "INSERT INTO sets VALUES (?, ?, ?, ?)",
    [
        (1, 1, 5, 100), # Session 1, Squat
        (1, 2, 5, 120), # Session 1, Bench Press
        (2, 3, 3, 150), # Session 2, Deadlift
        (2, 1, 3, 200), # Session 2, Squat
    ]
)

conn.commit()
conn.close()