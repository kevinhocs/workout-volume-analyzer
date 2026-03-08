def header(title):
    print(f"\n{title}")
    print("=" * len(title))


def print_reports(
    weekly_volume,
    weekly_exercise_volume,
    exercise_best_1rm,
    exercise_best_load,
    exercise_best_load_reps,
    exercise_pr_progress,
    exercise_sessions,
    exercise_weekly_1rm,
    plateaus,
    volatility,
):

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

    header("Plateau Detection")

    if not plateaus:
        print("None")
    else:
        for exercise, weeks in sorted(plateaus.items()):
            print(f"{exercise:<22} plateau ({weeks} weeks)")

    header("Volume Volatility")

    if not volatility:
        print("None")
    else:
        for year, week, change_type, pct in volatility:
            sign = "+" if change_type == "spike" else "-"
            print(f"{year}-W{week:02d} {change_type} ({sign}{pct}%)")

    header("Exercise Frequency")

    for exercise, workout_ids in sorted(exercise_sessions.items()):
        count = len(workout_ids)
        label = "session" if count == 1 else "sessions"
        print(f"{exercise:<22} {count} {label}")