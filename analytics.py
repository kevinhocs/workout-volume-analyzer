from exercise_pattern import is_bodyweight_exercise

# ----------------------------------------------------------------------
# Set-level analytics
# ----------------------------------------------------------------------

def analyze_sets(conn, sessions):

    session_volume = {sid: 0 for sid in sessions}
    weekly_exercise_volume = {}
    exercise_best_1rm = {}
    exercise_best_load = {}
    exercise_best_load_reps = {}
    exercise_pr_progress = {}
    exercise_sessions = {}
    exercise_weekly_1rm = {}

    # ----------------------------------------------------------------------
    # Set accumulation
    # ----------------------------------------------------------------------

    curr = conn.execute("""
    SELECT s.workout_id, e.name, s.reps, s.weight_lbs
    FROM sets s
    JOIN exercise e ON s.exercise_id = e.exercise_id
    """)

    for workout_id, exercise_name, reps, weight in curr:
        if reps <= 0 or weight < 0:
            raise ValueError(f"invalid set data: reps={reps}, weight={weight} in workout {workout_id}")

        if workout_id not in sessions:
            raise ValueError(f"set references non-existent workout: {workout_id}")

        session_date, bodyweight = sessions[workout_id]

        load = weight
        if is_bodyweight_exercise(exercise_name):
            if bodyweight is None:
                raise ValueError(f"missing bodyweight for workout {workout_id} ({exercise_name})")
            load = bodyweight + weight

        exercise_sessions.setdefault(exercise_name, set()).add(workout_id)

        #TODO: Consider supporting bodyweight percentage (e.g., dips ≈ 0.9 * BW)

        volume = reps * load

        session_volume[workout_id] += volume

        # Estimate 1RM and detect PR progression
        estimated_1rm = load * (1 + reps / 30)
        
        # Track weekly best 1RM
        iso_year, iso_week, _ = session_date.isocalendar()
        week_key = (iso_year, iso_week)

        exercise_weekly_1rm.setdefault(exercise_name, {})

        current = exercise_weekly_1rm[exercise_name].get(week_key)

        if current is None or estimated_1rm > current:
            exercise_weekly_1rm[exercise_name][week_key] = estimated_1rm

        # Update best estimated 1RM and record PR improvement
        if exercise_name not in exercise_best_1rm:
            exercise_best_1rm[exercise_name] = estimated_1rm
        elif estimated_1rm > exercise_best_1rm[exercise_name]:

            diff = estimated_1rm - exercise_best_1rm[exercise_name]
            exercise_pr_progress[exercise_name] = (
            exercise_pr_progress.get(exercise_name, 0) + diff
            )
            exercise_best_1rm[exercise_name] = estimated_1rm

        # Track actual PR (heaviest load lifted)
        if exercise_name not in exercise_best_load or load > exercise_best_load[exercise_name]:
            exercise_best_load[exercise_name] = load
            exercise_best_load_reps[exercise_name] = reps

        # Initialize week bucket if needed
        weekly_exercise_volume.setdefault(week_key, {})

        # Accumulate exercise volume for that week
        weekly_exercise_volume[week_key][exercise_name] = (
            weekly_exercise_volume[week_key].get(exercise_name, 0) + volume
        )

    return {
        "session_volume": session_volume,
        "weekly_exercise_volume": weekly_exercise_volume,
        "exercise_best_1rm": exercise_best_1rm,
        "exercise_best_load": exercise_best_load,
        "exercise_best_load_reps": exercise_best_load_reps,
        "exercise_pr_progress": exercise_pr_progress,
        "exercise_sessions": exercise_sessions,
        "exercise_weekly_1rm": exercise_weekly_1rm
    }

# ----------------------------------------------------------------------
# Weekly aggregation utilities
# ----------------------------------------------------------------------


def aggregate_weekly_volume(sessions, session_volume):
    weekly_volume = {}

    for session_id, (session_date, _) in sessions.items():
        iso_year, iso_week, _ = session_date.isocalendar()
        key = (iso_year, iso_week)

        weekly_volume[key] = (
            weekly_volume.get(key, 0) + session_volume[session_id]
        )

    return weekly_volume

# ----------------------------------------------------------------------
# Plateau detection
# ----------------------------------------------------------------------

def detect_plateaus(exercise_weekly_1rm, threshold=2):

    plateaus = {}

    for exercise, weeks in exercise_weekly_1rm.items():

        if len(weeks) < threshold + 1:
            continue

        sorted_weeks = sorted(weeks.items())

        best = None
        weeks_since_pr = 0

        for _, value in sorted_weeks:

            if best is None or value > best:
                best = value
                weeks_since_pr = 0
            else:
                weeks_since_pr += 1

        if weeks_since_pr >= threshold:
            plateaus[exercise] = weeks_since_pr

    return plateaus

# ----------------------------------------------------------------------
# Volume volatility detection
# ----------------------------------------------------------------------
def detect_volume_volatility(weekly_volume, spike=1.5, drop=0.6):

    volatility = []

    sorted_weeks = sorted(weekly_volume.items())

    prev_volume = None

    for (year, week), volume in sorted_weeks:

        if prev_volume is not None:

            change = volume / prev_volume

            if change >= spike:
                pct = int((change - 1) * 100)
                volatility.append((year, week, "spike", pct))

            elif change <= drop:
                pct = int((1 - change) * 100)
                volatility.append((year, week, "drop", pct))

        prev_volume = volume

    return volatility