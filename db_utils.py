from datetime import date


def table_exists(conn, table_name):
    curr = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
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

    curr = conn.execute(
        "SELECT workout_id, workout_date, bodyweight_lbs FROM workout"
    )

    for session_id, date_str, bodyweight in curr:
        parsed_date = parse_iso_date(date_str)

        if parsed_date is None:
            raise ValueError(
                f"invalid date format: {date_str} in session {session_id}"
            )

        sessions[session_id] = (parsed_date, bodyweight)

    if not sessions:
        raise ValueError("no sessions found in database")

    return sessions