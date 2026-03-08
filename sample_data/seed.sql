-- ======================
-- TABLES
-- ======================

CREATE TABLE workout (
    workout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_date TEXT NOT NULL UNIQUE,
    bodyweight_lbs REAL
);

CREATE TABLE exercise (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE sets (
    set_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    weight_lbs REAL NOT NULL,
    reps INTEGER NOT NULL,
    FOREIGN KEY (workout_id) REFERENCES workout(workout_id),
    FOREIGN KEY (exercise_id) REFERENCES exercise(exercise_id)
);

-- ======================
-- EXERCISES
-- ======================

INSERT INTO exercise (exercise_id,name) VALUES
(1,'Bench Press'),
(2,'Squat'),
(3,'Barbell Row'),
(4,'Overhead Press'),
(5,'Chin-Up'),
(6,'Dip');

-- ======================
-- WORKOUTS
-- ======================

INSERT INTO workout (workout_id,workout_date,bodyweight_lbs) VALUES
(1,'2026-01-05',175),
(2,'2026-01-08',176),
(3,'2026-01-12',176),
(4,'2026-01-15',177),
(5,'2026-01-19',177),
(6,'2026-01-22',178),
(7,'2026-01-26',178),  -- Week 05
(8,'2026-02-02',179),  -- Week 06
(9,'2026-02-09',179),  -- Week 07
(10,'2026-02-16',179); -- Week 08 regression

-- ======================
-- SETS
-- ======================

INSERT INTO sets (
workout_id,
exercise_id,
set_number,
weight_lbs,
reps
) VALUES

-- SESSION 1
(1,1,1,225,5),
(1,1,2,215,6),
(1,1,3,205,8),

(1,3,1,185,8),
(1,3,2,175,10),

(1,5,1,0,10),
(1,5,2,0,9),

-- SESSION 2
(2,2,1,315,5),
(2,2,2,305,6),
(2,2,3,295,8),

(2,6,1,25,8),
(2,6,2,25,7),

-- SESSION 3 (bench progression)
(3,1,1,230,5),
(3,1,2,220,6),
(3,1,3,210,8),

(3,4,1,115,5),
(3,4,2,105,6),

-- SESSION 4
(4,2,1,320,5),
(4,2,2,310,6),
(4,2,3,300,8),

(4,3,1,190,8),
(4,3,2,180,10),

-- SESSION 5
(5,5,1,10,8),
(5,5,2,10,7),

(5,1,1,230,5),
(5,1,2,220,6),

-- SESSION 6
(6,2,1,325,5),
(6,2,2,315,6),

(6,5,1,15,6),
(6,5,2,15,5),

-- SESSION 7 (plateau week 1)
(7,1,1,235,5),
(7,1,2,225,6),

-- SESSION 8 (plateau week 2)
(8,1,1,235,5),
(8,1,2,225,6),

-- SESSION 9 (plateau week 3)
(9,1,1,235,5),
(9,1,2,225,6),

-- SESSION 10 (regression)
(10,1,1,220,5),
(10,1,2,210,6);