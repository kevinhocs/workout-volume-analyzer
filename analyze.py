#!/usr/bin/env python3

import sys
import sqlite3
from pathlib import Path
from datetime import date
from exercise_pattern import is_bodyweight_exercise

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

    curr = conn.execute("SELECT workout_id, workout_date, bodyweight_lbs FROM workout")
    for session_id, date_str, bodyweight in curr.fetchall():
        parsed_date = parse_iso_date(date_str)
        if parsed_date is None:
            print(f"Error: invalid date format: {date_str} in session {session_id}")
            sys.exit(1)

        sessions[session_id] = (parsed_date, bodyweight)

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

    required_tables = ["workout", "exercise", "exercise_log"]

    for table in required_tables:
        if not table_exists(conn, table):
            print(f"Error: required table not found: {table}")
            sys.exit(1)

    required_columns = {
        "workout": ["workout_id", "workout_date", "bodyweight_lbs"],
        "exercise": ["exercise_id", "name"],
        "exercise_log": ["workout_id", "reps", "weight_lbs", "sets"]
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

        dates = sorted(session_date for session_date, _ in sessions.values())
        print(f"Date range: {dates[0]} to {dates[-1]}")

        # Count exercise
        curr = conn.execute("SELECT exercise_id, name FROM exercise")
        exercises = curr.fetchall()

        print(f"Distinct exercises: {len(exercises)}")
        print()

        for exercise_id, exercise_name in exercises:
            curr = conn.execute(
                "SELECT MAX(weight_lbs) FROM exercise_log WHERE exercise_id=? GROUP BY workout_id",
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
    weekly_exercise_volume = {}
    exercise_best_1rm = {}
    exercise_best_load = {}
    exercise_best_load_reps = {}

    # ------------------------------------------------------------------
    # Set accumulation (enforce data invariants)
    # ------------------------------------------------------------------

    curr = conn.execute("""SELECT workout_id, e.name, reps, weight_lbs, sets FROM exercise_log l
                         JOIN exercise e ON l.exercise_id = e.exercise_id""")

    for workout_id, exercise_name, reps, weight, sets in curr.fetchall():
        if reps <= 0 or weight < 0:
            print(f"Error: invalid set data: reps={reps}, weight={weight} in workout {workout_id}")
            sys.exit(1)

        if workout_id not in sessions:
            print(f"Error: set references non-existent workout: {workout_id}")
            sys.exit(1)

        session_date, bodyweight = sessions[workout_id]

        load = weight
        if is_bodyweight_exercise(exercise_name):
            if bodyweight is None:
                print(f"Error: missing bodyweight for workout {workout_id} ({exercise_name})")
                sys.exit(1)
            load = bodyweight + weight

        volume = reps * load * sets

        # session volume
        session_volume[workout_id] += volume

        # exercise 1RM tracking
        estimated_1rm = load * (1 + reps / 30)
        # track best estimated 1RM
        if exercise_name not in exercise_best_1rm:
            exercise_best_1rm[exercise_name] = estimated_1rm
        else:
            exercise_best_1rm[exercise_name] = max(exercise_best_1rm[exercise_name], estimated_1rm)

        # track actual PR (heaviest load lifted)
        if exercise_name not in exercise_best_load or load > exercise_best_load[exercise_name]:
            exercise_best_load[exercise_name] = load
            exercise_best_load_reps[exercise_name] = reps

        # determine the week
        iso_year, iso_week, _ = session_date.isocalendar()
        week_key = (iso_year, iso_week)

        # create week entry if missing
        if week_key not in weekly_exercise_volume:
            weekly_exercise_volume[week_key] = {}

        # accumulate exercise volume for that week
        weekly_exercise_volume[week_key][exercise_name] = (
            weekly_exercise_volume[week_key].get(exercise_name, 0) + volume
        )

    # ------------------------------------------------------------------
    # Weekly aggregation
    # ------------------------------------------------------------------

    weekly_volume = {}

    for session_id, (session_date, _) in sessions.items():
        iso_year, iso_week, _ = session_date.isocalendar()
        key = (iso_year, iso_week)

        weekly_volume[key] = (
            weekly_volume.get(key, 0) + session_volume[session_id]
        )

    for (year, week), volume in sorted(weekly_volume.items()):
        print(f"\n{year}-W{week:02d} total_volume={int(volume)}")

        print("Exercise Breakdown")
        print("------------------")

        for exercise, v in sorted(weekly_exercise_volume.get((year, week), {}).items()):
            print(f"{exercise:<20} {int(v)}")

    print("\nEstimated 1RM")
    print("------------------")

    for exercise, est in sorted(exercise_best_1rm.items()):
        print(f"{exercise:<20} {int(round(est))}")

    print("\nActual Personal Records")
    print("----------")

    for exercise in sorted(exercise_best_load):
        load = exercise_best_load[exercise]
        reps = exercise_best_load_reps[exercise]

        print(f"{exercise:<20} {int(load)} x {reps}")


if __name__ == "__main__":
    main()
