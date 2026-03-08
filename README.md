## Workout Volume Analyzer

A correctness-focused analysis tool for validating structured workout data and computing weekly training volume from a SQLite database.

## Features

- Opens SQLite databases in read-only mode
- Validates required tables and columns explicitly
- Enforces data invariants (dates, foreign keys, numeric constraints)
- Computes weekly training volume using ISO-8601 calendar weeks
- Tracks per-exercise volume breakdown
- Estimates 1RM using the Epley formula
- Detects actual personal records (heaviest load lifted)
- Detects estimated strength progression (new PRs)
- Normalizes bodyweight exercises using bodyweight + external load
- Produces deterministic, sorted output
- Fails fast on invalid or inconsistent data

## Why This Project Exists

This project emphasizes **data correctness and invariant enforcement** over feature breadth.

Rather than focusing on visualization or UI layers, the analyzer demonstrates how
structured data pipelines can be built with explicit schema contracts and deterministic
computation.

## Design Overview

- Database opened in read-only mode to guarantee no side effects
- Schema invariants validated before any computation
- Sessions loaded into a canonical in-memory representation
- Set data validated and accumulated per session
- Weekly aggregation performed using ISO-8601 week semantics
- Output generated only after all validation succeeds

## Data Model

The analyzer assumes the following schema contract.

### `workout`

| column | type | constraints |
|------|------|-------------|
| workout_id | INTEGER | primary key |
| workout_date | TEXT | ISO-8601 (`YYYY-MM-DD`) |
| bodyweight_lbs | REAL | nullable |

### `exercise`

| column | type | constraints |
|------|------|-------------|
| exercise_id | INTEGER | primary key |
| name | TEXT | exercise identifier |

### `sets`

| column | type | constraints |
|------|------|-------------|
| set_id | INTEGER | primary key |
| workout_id | INTEGER | references `workout.workout_id` |
| exercise_id | INTEGER | references `exercise.exercise_id` |
| set_number | INTEGER | > 0 |
| reps | INTEGER | > 0 |
| weight_lbs | REAL | ≥ 0 |

## Volume Definition

Weekly training volume is defined as:
```
sum(effective_load × repetitions)
```

where
```
effective_load =
    weight_lbs                 (non-bodyweight exercises)
    bodyweight + weight_lbs    (bodyweight exercises)
```

Units depend on the data stored in the database (e.g., pounds or kilograms × repetitions).

## Example Weekly Summary
```
2026-W06 total_volume=21000
```

Each line represents total training volume for one ISO calendar week.

## Strength Analytics

The analyzer computes several strength metrics.

### Estimated 1RM

Estimated one-rep max values are calculated using the Epley formula:
```
1RM = load × (1 + reps / 30)
```

The highest estimated value per exercise is retained.

### Actual Personal Records

The analyzer tracks the heaviest load lifted for each exercise, regardless of repetition count.

Example:
```
Romanian Deadlift    340 x 7
```

### PR Progression

If a newly estimated 1RM exceeds the previous best, the analyzer reports the improvement.

Example:
```
Romanian Deadlift    431 (+12)
```

## Bodyweight Exercise Handling
For bodyweight movements (e.g., dips, pull-ups), total load is modeled as:
```
total_load = bodyweight + external_weight
```

This allows bodyweight exercises to be incorporated into volume and strength calculations consistently with barbell movements.

## Audit Mode
Run audit mode:
```
py analyze.py path/to/database.db --audit
```
Audit mode reports dataset statistics such as:

- number of sessions
- exercise frequency
- average top set weight
- standard deviation of top sets

This mode is useful for validating dataset quality before analysis.

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

## Data Sources

The analyzer can operate on any SQLite database that satisfies the expected schema.

Two typical use cases:

### 1. Analyze data from the Workout Logger application

This tool was designed to operate directly on databases produced by the companion project:

Workout Logger  
https://github.com/kevinhocs/workout-logger

Example:
```
py analyze.py workout.db
```

This allows offline analysis of real training data exported from the logging application.

### 2. Run locally using the included sample dataset

A deterministic example dataset is included under:
```
sample_data/workout_sample.db
```

This dataset intentionally demonstrates:

- strength progression
- plateaus
- regression
- bodyweight exercises
- weighted bodyweight exercises
- weekly training volume variation

Run:
```
py analyze.py sample_data/workout_sample.db
```

This allows the analyzer to be evaluated without requiring the workout logger application.