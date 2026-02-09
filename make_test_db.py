"""Test database generator for the workout analyzer.

Creates a small, deterministic SQLite database (test.db)
used to validate correctness and invariant handling.
Not used by the analyzer at runtime.
"""

import sqlite3

DB_NAME = "test.db"

conn = sqlite3.connect(DB_NAME)

# ----------------------------------------------------------------------
# Reset schema (idempotent)
# ----------------------------------------------------------------------

conn.execute("DROP TABLE IF EXISTS sets")
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
CREATE TABLE sets (
    session_id INTEGER NOT NULL,
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
        (3, "2026-02-05"),
    ]
)

conn.executemany(
    "INSERT INTO sets VALUES (?, ?, ?)",
    [
        (1, 5, 100),
        (1, 5, 120),
        (2, 3, 200),
    ]
)

conn.commit()
conn.close()