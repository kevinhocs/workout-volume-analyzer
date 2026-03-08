#!/usr/bin/env python3

import sys
import sqlite3
from pathlib import Path

from db_utils import table_exists, column_exists, load_sessions
from analytics import analyze_sets, aggregate_weekly_volume

def header(title):
    print(f"\n{title}")
    print("=" * len(title))

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
    try:
        sessions = load_sessions(conn)

        results = analyze_sets(conn, sessions)

        session_volume = results["session_volume"]
        weekly_exercise_volume = results["weekly_exercise_volume"]
        exercise_best_1rm = results["exercise_best_1rm"]
        exercise_best_load = results["exercise_best_load"]
        exercise_best_load_reps = results["exercise_best_load_reps"]
        exercise_pr_progress = results["exercise_pr_progress"]
        exercise_sessions = results["exercise_sessions"]
        exercise_weekly_1rm = results["exercise_weekly_1rm"]

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

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

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    weekly_volume = aggregate_weekly_volume(sessions, session_volume)

    header("Weekly Training Volume")

    prev_volume = None

    for (year, week), volume in sorted(weekly_volume.items()):

        if prev_volume is None:
            trend = ""
        elif volume > prev_volume:
            trend = " ↑"
        elif volume < prev_volume:
            trend = " ↓"
        else:
            trend = " →"

        print(f"\n{year}-W{week:02d}  total_volume={int(volume)}{trend}")

        for exercise, v in sorted(weekly_exercise_volume.get((year, week), {}).items()):
            print(f"  {exercise:<22} {int(v)}")

        prev_volume = volume

    header("Estimated 1RM")

    for exercise, est in sorted(exercise_best_1rm.items()):
        print(f"{exercise:<22} {int(round(est))}")

    header("Actual Personal Records")

    if not exercise_best_load:
        print("None")
    else:
        for exercise in sorted(exercise_best_load):
            load = exercise_best_load[exercise]
            reps = exercise_best_load_reps[exercise]

            print(f"{exercise:<22} {int(load)} x {reps}")

    # TODO: Detect PR progression over time windows (week-over-week)

    header("New PRs")

    if not exercise_pr_progress:
        print("None")
    else:
        for exercise in sorted(exercise_pr_progress):
            diff = exercise_pr_progress[exercise]
            new_pr = exercise_best_1rm[exercise]
            print(f"{exercise:<22} {int(round(new_pr))} (+{int(round(diff))})")

    header("Strength Progression")

    for exercise, weeks in sorted(exercise_weekly_1rm.items()):
        print(f"\n{exercise}")

        prev_1rm = None

        for (year, week), value in sorted(weeks.items()):

            if prev_1rm is None:
                print(f"  {year}-W{week:02d}  {int(round(value))}")
            else:
                diff = value - prev_1rm
                sign = "+" if diff >= 0 else ""
                print(f"  {year}-W{week:02d}  {int(round(value))} ({sign}{int(round(diff))})")

            prev_1rm = value

    header("Exercise Frequency")

    for exercise, workout_ids in sorted(exercise_sessions.items()):
        count = len(workout_ids)
        label = "session" if count == 1 else "sessions"
        print(f"{exercise:<22} {count} {label}")

if __name__ == "__main__":
    main()
