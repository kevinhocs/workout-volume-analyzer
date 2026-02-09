## Workout Volume Analyzer

A correctness-focused analysis tool for validating structured workout data and computing weekly training volume from a SQLite database.

## Features

- Opens SQLite databases in read-only mode
- Validates required tables and columns explicitly
- Enforces data invariants (dates, foreign keys, numeric constraints)
- Computes weekly training volume using ISO-8601 calendar weeks
- Produces deterministic, sorted output
- Fails fast on invalid or inconsistent data

## Why This Project Exists

This project was built to demonstrate engineering judgment around data correctness, not feature breadth or presentation.

The focus is on:
- explicit schema contracts
- invariant enforcement
- fail-fast behavior
- deterministic computation

## Design Overview

- Database opened in read-only mode to guarantee no side effects
- Schema invariants validated before any computation
- Sessions loaded into a canonical in-memory representation
- Set data validated and accumulated per session
- Weekly aggregation performed using ISO-8601 week semantics
- Output generated only after all validation succeeds

## Data Model

The analyzer assumes the following schema contract.

### `sessions`

| column | type | constraints |
|------|------|-------------|
| id | INTEGER | primary key |
| date | TEXT | ISO-8601 (`YYYY-MM-DD`) |

### `sets`

| column | type | constraints |
|------|------|-------------|
| session_id | INTEGER | references `sessions.id` |
| reps | INTEGER | > 0 |
| weight | REAL | > 0 |

Any deviation from this contract will cause immediate failure.

## Volume Definition

Weekly training volume is defined as:
```
sum(weight × repetitions) across all sets in a given ISO-8601 calendar week
```

Units depend on the data stored in the database (e.g., pounds or kilograms × repetitions).

## Example Output
```
2026-W05 volume=1100
2026-W06 volume=600
```

Each line represents total training volume for one ISO calendar week.

## Error Handling
The analyzer exits immediately with a descriptive error message if any invariant is violated, including:

- Missing tables or columns
- Invalid date formats
- Non-positive repetitions or weight
- Sets referencing non-existent sessions
- Empty session data

No partial results are produced on failure.

## Limitations

- No database mutation or schema migration
- No unit normalization or inference
- No visualization or reporting UI
- No recovery from invalid data
- No time zone normalization

These are intentional non-goals to preserve correctness and clarity.

## Running the Analyzer
```
py analyze.py path/to/database.db
```

Results are printed to stdout.

## Testing

A small helper script (make_test_db.py) is included to generate a deterministic test database.
Invariant enforcement was validated by manually introducing invalid test data (e.g., bad dates, invalid foreign keys, non-positive values) and confirming the analyzer fails fast.