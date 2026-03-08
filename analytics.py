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
    SELECT workout_id, e.name, reps, weight_lbs, sets 
    FROM exercise_log l
    JOIN exercise e ON l.exercise_id = e.exercise_id
    """)

    for workout_id, exercise_name, reps, weight, sets in curr.fetchall():
        if reps <= 0 or sets <= 0 or weight < 0:
            raise ValueError(f"invalid set data: reps={reps}, weight={weight}, sets={sets} in workout {workout_id}")

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

        volume = reps * load * sets

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
            exercise_pr_progress[exercise_name] = diff
            exercise_best_1rm[exercise_name] = estimated_1rm

        # Track actual PR (heaviest load lifted)
        if exercise_name not in exercise_best_load or load > exercise_best_load[exercise_name]:
            exercise_best_load[exercise_name] = load
            exercise_best_load_reps[exercise_name] = reps

        # Determine the week
        iso_year, iso_week, _ = session_date.isocalendar()
        week_key = (iso_year, iso_week)

        # Initialize week bucket if needed
        if week_key not in weekly_exercise_volume:
            weekly_exercise_volume[week_key] = {}

        # Accumulate exercise volume for that week
        weekly_exercise_volume[week_key][exercise_name] = (
            weekly_exercise_volume[week_key].get(exercise_name, 0) + volume
        )

    return (
        session_volume,
        weekly_exercise_volume,
        exercise_best_1rm,
        exercise_best_load,
        exercise_best_load_reps,
        exercise_pr_progress,
        exercise_sessions,
        exercise_weekly_1rm
        )

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