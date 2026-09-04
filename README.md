# Log Set

A command-line gym log designed for the fastest possible workout entry, minimizing phone time in the gym while providing key reports that support training decisions.

## Status

This is the stable, non-coaching version. It records and summarizes training without prescribing workouts or recommending progression.

## Requirements

- Python 3
- No third-party packages

## Usage

Run:

```powershell
python log_set.py
```

Log a set:

```text
exercise,weight,reps
```

Add an optional note:

```text
exercise,weight,reps,note
```

Example:

```text
bench,185,8,felt strong
```

Type `help` or `menu` while the program is running to see the available commands.

## Features

- Fast CSV workout logging
- Optional set notes
- Repeat the previous set or previous two sets
- Daily and exercise-specific history
- Weekly and rolling seven-day volume reports
- Four-week and eight-week averages
- Week-to-week volume comparisons
- Exercise categorization
- Alternating rehab reminders

## Data

Workout history is stored locally in `gym_log.csv`. Exercise categories are stored in `exercise_categories.csv`.

These personal data files are excluded from Git.
