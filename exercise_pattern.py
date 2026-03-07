def normalize(name):
    name = name.lower().replace("-", " ").strip()

    words = name.split()
    if words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]

    return " ".join(words)

def is_bodyweight_exercise(name):
    name = normalize(name)
    return any(pattern in name for pattern in BODYWEIGHT_PATTERNS)


BODYWEIGHT_PATTERNS = [
    # Pull Ups
    "pull up",
    "chin up",

    # Dips
    "dip",

    # Push Ups
    "push up",

    # Rows
    "inverted row",
    "ring row",

    # Overhead
    "handstand push up",

    # Squats
    "pistol squat",
    "sissy squat",

    # Hamstrings
    "nordic curl",
    "nordic ham curl",
]