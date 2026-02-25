#!/usr/bin/env python3

import sys
import sqlite3
from pathlib import Path
from datetime import date

# ----------------------------------------------------------------------
# Schema / utility helpers
# ----------------------------------------------------------------------

def table_exists(conn, table_name):
    curr = conn.execute(
        "SELECT name FROM sqlite_master WHERE type= 'table' AND name=?",
        (table_name,)
    )
    return curr.fetchone() is not None

def column_exists(conn, table, column):
    curr = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in curr.fetchall())

def parse_iso_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None

def load_sessions(conn):
    sessions = {}

    curr = conn.execute("SELECT id, date FROM sessions")
    for session_id, date_str in curr.fetchall():
        parsed_date = parse_iso_date(date_str)
        if parsed_date is None:
            print(f"Error: invalid date format: {date_str} in session {session_id}")
            sys.exit(1)

        sessions[session_id] = parsed_date

    if not sessions:
        print("Error: no sessions found in database")
        sys.exit(1)

    return sessions

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python analyze.py <path-to-db> [--audit]")
        sys.exit(1)

    audit_mode = False
    if len(sys.argv) == 3:
        if sys.argv[2] != "--audit":
            print(f"Unknown option: {sys.argv[2]}")
            sys.exit(1)
        audit_mode = True

    db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"Error: database file not found: {db_path}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True
        )
    except sqlite3.Error as e:
        print(f"Error opening database: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Schema invariants
    # ------------------------------------------------------------------

    required_tables = ["sessions", "exercises", "sets"]

    for table in required_tables:
        if not table_exists(conn, table):
            print(f"Error: required table not found: {table}")
            sys.exit(1)

    required_columns = {
        "sessions": ["id", "date"],
        "exercises": ["id", "name"],
        "sets": ["session_id", "reps", "weight"]
    }

    for table, columns in required_columns.items():
        for col in columns:
            if not column_exists(conn, table, col):
                print(f"Error: required column not found: {col} in table {table}")
                sys.exit(1)

    # ------------------------------------------------------------------
    # Canonical load: sessions
    # ------------------------------------------------------------------

    sessions = load_sessions(conn)
    if audit_mode:
        print(f"Total sessions loaded: {len(sessions)}")

        dates = sorted(sessions.values())
        print(f"Date range: {dates[0]} to {dates[-1]}")

        # Count exercise
        curr = conn.execute("SELECT id, name FROM exercises")
        exercises = curr.fetchall()

        print(f"Distinct exercises: {len(exercises)}")
        print()

        for exercise_id, exercise_name in exercises:
            curr = conn.execute(
                "SELECT MAX(weight) FROM sets WHERE exercise_id=? GROUP BY session_id",
                (exercise_id,)
            )

            top_sets = [row[0] for row in curr.fetchall()]

            if not top_sets:
                continue

            mean = sum(top_sets) / len(top_sets)
            variance = sum((x - mean) ** 2 for x in top_sets) / len(top_sets)
            std_dev = variance ** 0.5

            print(f"Exercise: {exercise_name}")
            print(f"  Sessions: {len(top_sets)}")
            print(f"  Avg Top Set: {mean:.2f}")
            print(f"  Std Dev: {std_dev:.2f}")
            print()

        sys.exit(0)
    session_volume = {sid: 0 for sid in sessions}

    # ------------------------------------------------------------------
    # Set accumulation (enforce data invariants)
    # ------------------------------------------------------------------

    curr = conn.execute("SELECT session_id, reps, weight FROM sets")

    for session_id, reps, weight in curr.fetchall():
        if reps <= 0 or weight <= 0:
            print(f"Error: invalid set data: reps={reps}, weight={weight} in session {session_id}")
            sys.exit(1)

        if session_id not in sessions:
            print(f"Error: set references non-existent session: {session_id}")
            sys.exit(1)

        session_volume[session_id] += reps * weight

    # ------------------------------------------------------------------
    # Weekly aggregation
    # ------------------------------------------------------------------

    weekly_volume = {}

    for session_id, session_date in sessions.items():
        iso_year, iso_week, _ = session_date.isocalendar()
        key = (iso_year, iso_week)

        weekly_volume[key] = (
            weekly_volume.get(key, 0) + session_volume[session_id]
        )

    for (year, week), volume in sorted(weekly_volume.items()):
        print(f"{year}-W{week:02d} volume={int(volume)}")


if __name__ == "__main__":
    main()
