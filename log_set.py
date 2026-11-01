"""Log Set: fast gym logging from the command line.

Sections, in order (each one only uses the sections above it):
  1. Settings
  2. Data files
  3. Dates
  4. Calculations
  5. Formatting
  6. Reports
  7. Exercise categories
  8. Workout menu
  9. Rehab reminder
  10. Main program
"""

import contextlib
import csv
import io
from datetime import datetime, timedelta

try:
    import console  # Pythonista only
except ImportError:
    console = None


# ======================================================================
# SETTINGS
# ======================================================================

FILENAME = 'gym_log.csv'

CATEGORY_FILENAME = 'exercise_categories.csv'

# How many of the most recent reports stay on screen.
REPORTS_ON_SCREEN = 2

CATEGORY_ORDER = ['Push', 'Pull', 'Legs/Other', 'Uncategorized']

ODD_REHAB = ['Wrist Curls', 'Neck', 'Quads', 'Wall Stretch', 'Glute Bridge']
EVEN_REHAB = ['Straight Leg Raise', 'Copenhagen Plank', 'Calves', 'Hamstrings']


# ======================================================================
# DATA FILES
# Reading and writing gym_log.csv and exercise_categories.csv.
# These are the only functions that open a file.
# ======================================================================

def read_log_rows():
    """Return every row of the workout log that has all six columns.

    Values are left as raw strings; callers parse what they need.
    """
    with open(FILENAME) as file:
        return [
            row
            for row in csv.reader(file)
            if len(row) >= 6
        ]


def parse_date(text):
    return datetime.strptime(text, '%Y-%m-%d').date()


def parse_set_row(row):
    """Return (date, exercise, weight, reps, note), or None if the row is bad."""
    try:
        return (
            parse_date(row[0]),
            row[2].strip(),
            float(row[3]),
            int(float(row[4])),
            row[5].strip(),
        )
    except ValueError:
        return None


def log_set(exercise, weight, reps, note):
    now = datetime.now()

    with open(FILENAME, 'a+', newline='') as file:
        file.seek(0, 2)
        file_size = file.tell()

        if file_size > 0:
            file.seek(file_size - 1)
            last_char = file.read(1)

            if last_char != '\n':
                file.write('\n')

        writer = csv.writer(file)
        writer.writerow([
            now.date(),
            now.strftime('%H:%M'),
            exercise,
            weight,
            reps,
            note
        ])


def rename_exercise_in_log(old_name, new_name):
    rows = []

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) >= 3 and row[2] == old_name:
                row[2] = new_name

            rows.append(row)

    with open(FILENAME, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def load_exercise_categories():
    categories = {}

    try:
        with open(CATEGORY_FILENAME) as file:
            reader = csv.reader(file)

            for row in reader:
                if len(row) < 2:
                    continue

                exercise = row[0].strip()
                category = row[1].strip()

                if exercise and category:
                    categories[exercise] = category

    except FileNotFoundError:
        pass

    return categories


def save_exercise_category(exercise, category):
    with open(CATEGORY_FILENAME, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([exercise, category])


# ======================================================================
# DATES
# ======================================================================

def today_date():
    return datetime.now().date()


def days_before(day, days):
    return day - timedelta(days=days)


def start_of_week(day):
    """Monday of the week containing day."""
    return days_before(day, day.weekday())


# ======================================================================
# CALCULATIONS
# Turn logged sets into numbers. Nothing here prints.
# ======================================================================

def calculate_volume(exercise, weight, reps):
    if exercise.endswith('_iso'):
        reps = reps / 2

    return weight * reps


def get_volume_for_range(start_date, end_date):
    volume_sets = {}
    volume_total = {}

    for row in read_log_rows():
        parsed = parse_set_row(row)

        if parsed is None:
            continue

        date, exercise, weight, reps, note = parsed

        if start_date <= date <= end_date:
            volume = calculate_volume(
                exercise,
                weight,
                reps
            )

            volume_sets[exercise] = (
                volume_sets.get(exercise, 0) + 1
            )

            volume_total[exercise] = (
                volume_total.get(exercise, 0)
                + volume
            )

    return volume_sets, volume_total


def count_sets_for_range(start_date, end_date):
    """Count logged sets per exercise between two dates (inclusive)."""
    total_sets = {}

    for row in read_log_rows():
        try:
            date = parse_date(row[0])
        except ValueError:
            continue

        if start_date <= date <= end_date:
            exercise = row[2].strip()
            total_sets[exercise] = total_sets.get(exercise, 0) + 1

    return total_sets


def get_4_week_set_totals():
    today = today_date()
    start_date = days_before(today, 27)

    try:
        return count_sets_for_range(start_date, today)
    except FileNotFoundError:
        return {}


# ======================================================================
# FORMATTING
# Turn numbers into text, and the shared report layouts.
# ======================================================================

def format_weight(weight):
    weight = float(weight)

    if weight.is_integer():
        return int(weight)

    return weight


def group_reps(reps_list):
    """Turn [8, 8, 6] into '2x8, 6'."""
    grouped = []
    current = reps_list[0]
    count = 1

    for reps in reps_list[1:]:
        if reps == current:
            count += 1
        else:
            grouped.append(f'{count}x{current}' if count > 1 else str(current))
            current = reps
            count = 1

    grouped.append(f'{count}x{current}' if count > 1 else str(current))

    return ', '.join(grouped)


def format_set_difference(value):
    if abs(value) < 0.05:
        value = 0

    if float(value).is_integer():
        return f'{int(value):+d}'

    return f'{value:+.1f}'


def format_volume_difference(value):
    if abs(value) < 0.5:
        value = 0

    return f'{value:+,.0f}'


def print_report_header(title):
    print()
    print('=' * 40)
    print(title)
    print('=' * 40)
    print()


def print_by_category(items, sort_key, format_line):
    """Print items grouped under Push / Pull / Legs/Other / Uncategorized.

    Each item is a tuple whose first value is the exercise name. Within a
    category, items are sorted by sort_key, largest first, and each one is
    printed with format_line(item).
    """
    exercise_categories = load_exercise_categories()

    categorized_exercises = {
        category: []
        for category in CATEGORY_ORDER
    }

    for item in items:
        category = exercise_categories.get(item[0], 'Uncategorized')

        if category not in categorized_exercises:
            category = 'Uncategorized'

        categorized_exercises[category].append(item)

    printed_category = False

    for category in CATEGORY_ORDER:
        exercises = categorized_exercises[category]

        if not exercises:
            continue

        if printed_category:
            print()

        print(f'{category}:')

        exercises.sort(key=sort_key, reverse=True)

        for item in exercises:
            print(format_line(item))

        printed_category = True


def print_categorized_volume(volume_sets, volume_total):
    def format_line(item):
        exercise, volume = item
        sets = volume_sets[exercise]
        set_word = 'set' if sets == 1 else 'sets'

        return (
            f'    {exercise:<22}'
            f'{sets:>3} {set_word}, '
            f'{volume:>8,.0f} lbs'
        )

    print_by_category(
        volume_total.items(),
        sort_key=lambda item: item[1],
        format_line=format_line,
    )


# ======================================================================
# REPORTS
# One function per report command.
# ======================================================================

def show_today_workout():
    today = today_date()
    entries = {}
    exercise_order = []

    for row in read_log_rows():
        parsed = parse_set_row(row)

        if parsed is None:
            continue

        date, exercise, weight, reps, note = parsed

        if date == today:
            if exercise not in entries:
                entries[exercise] = {}
                exercise_order.append(exercise)

            key = (weight, note)
            entries[exercise].setdefault(key, []).append(reps)

    print_report_header('Today')

    if not entries:
        print('    No workouts logged today.')
        return

    name_width = min(max(len(exercise) for exercise in exercise_order), 16)

    for exercise in exercise_order:
        groups = []

        for (weight, note), reps_list in entries[exercise].items():
            group = f'{format_weight(weight)}: {group_reps(reps_list)}'

            if note:
                group += f' ({note})'

            groups.append(group)

        print(f'  {exercise:<{name_width}}  ' + ' | '.join(groups))


def show_copy_mode(exercise_name):
    entries = [
        row
        for row in read_log_rows()
        if row[2] == exercise_name
    ]

    if not entries:
        print(f'No history found for {exercise_name}.')
        return

    last_date = entries[-1][0]

    print(f'\nLast {exercise_name} workout: {last_date}\n')

    for row in entries:
        if row[0] == last_date:
            print(f'{row[2]}, {row[3]}, {row[4]}, {row[5]}')


# How far back the plain 'history' command looks.
HISTORY_WEEKS = 8


def show_exercise_history(*exercise_names, weeks=None):
    """Print the history of the named exercises.

    weeks=None shows everything; otherwise only the last that many weeks.
    """
    history = {}

    if weeks is not None:
        start_date = days_before(today_date(), weeks * 7 - 1)

    for row in read_log_rows():
        exercise = row[2]

        if exercise not in exercise_names:
            continue

        try:
            date = row[0]
            weight = float(row[3])
            reps = int(float(row[4]))

            if weeks is not None and parse_date(date) < start_date:
                continue
        except ValueError:
            continue

        key = (date, exercise, weight)

        history.setdefault(key, []).append(reps)

    if not history:
        if weeks is None:
            print('No history found.')
        else:
            print(f'No history in the last {weeks} weeks. Try fh NAMES for all of it.')
        return

    if weeks is not None:
        print(f'\nLast {weeks} weeks (fh NAMES shows all)')

    print(f'\n{"Date":<12}\t{"Exercise":<15}\t{"Weight":<8}\tSets×Reps')

    sorted_history = sorted(
        history.items(),
        key=lambda item: (item[0][0], item[0][1]),
        reverse=True
    )

    for (date, exercise, weight), reps_list in sorted_history:
        print(
            f'{date:<12}\t'
            f'{exercise:<15}\t'
            f'{format_weight(weight):<8}\t'
            f'{group_reps(reps_list)}'
        )


def show_weekly_exercise_history(exercise_name):
    weekly_sets = {}
    weekly_volume = {}

    for row in read_log_rows():
        try:
            date = parse_date(row[0])
            exercise = row[2].strip()
            weight = float(row[3])
            reps = float(row[4])
        except ValueError:
            continue

        if exercise != exercise_name:
            continue

        week_start = start_of_week(date)

        weekly_sets[week_start] = (
            weekly_sets.get(week_start, 0) + 1
        )

        weekly_volume[week_start] = (
            weekly_volume.get(week_start, 0)
            + weight * reps
        )

    print_report_header(
        f'{exercise_name} Weekly History'
    )

    if not weekly_sets:
        print(f'    No history found for {exercise_name}.')
        return

    for week_start in sorted(
        weekly_sets,
        reverse=True
    ):
        sets = weekly_sets[week_start]
        volume = weekly_volume[week_start]

        set_word = 'set' if sets == 1 else 'sets'

        print(
            f'{week_start}   '
            f'{sets:>2} {set_word}, '
            f'{volume:>7,.0f} lbs'
        )


def show_volume_for_range(label, start_date, end_date):
    volume_sets, volume_total = get_volume_for_range(
        start_date,
        end_date
    )

    print_report_header(label.title())

    if not volume_total:
        print('    No workouts logged.')
        return

    print_categorized_volume(
        volume_sets,
        volume_total
    )


def show_this_week_volume():
    today = today_date()

    show_volume_for_range('Weekly volume', start_of_week(today), today)


def show_two_weeks_ago_volume():
    week_start = start_of_week(today_date())

    show_volume_for_range(
        'Two weeks ago volume',
        days_before(week_start, 14),
        days_before(week_start, 8)
    )


def show_rolling_7_day_volume():
    today = today_date()

    show_volume_for_range('7-Day Rolling Volume', days_before(today, 6), today)


def show_average_sets(weeks):
    today = today_date()
    days = weeks * 7
    total_sets = count_sets_for_range(days_before(today, days - 1), today)

    print_report_header(f'{weeks}-Week Average Sets')

    if not total_sets:
        print(f'    No workouts logged in the previous {days} days.')
        return

    def format_line(item):
        exercise, average_sets = item

        if average_sets.is_integer():
            sets_display = int(average_sets)
        else:
            sets_display = round(average_sets, 1)

        set_word = 'set/week' if average_sets == 1 else 'sets/week'

        return (
            f'    {exercise:<22}'
            f'{sets_display:>5} {set_word}'
        )

    print_by_category(
        [(exercise, sets / weeks) for exercise, sets in total_sets.items()],
        sort_key=lambda item: item[1],
        format_line=format_line,
    )


def print_volume_comparison(
    title,
    current_sets,
    current_volume,
    comparison_sets,
    comparison_volume
):
    print_report_header(title)

    all_exercises = set(current_sets) | set(comparison_sets)

    if not all_exercises:
        print('    No workouts available to compare.')
        return

    items = []

    for exercise in all_exercises:
        set_difference = (
            current_sets.get(exercise, 0)
            - comparison_sets.get(exercise, 0)
        )

        volume_difference = (
            current_volume.get(exercise, 0)
            - comparison_volume.get(exercise, 0)
        )

        items.append((exercise, set_difference, volume_difference))

    def format_line(item):
        exercise, set_difference, volume_difference = item

        return (
            f'    {exercise:<18}'
            f'{format_set_difference(set_difference):>6} sets, '
            f'{format_volume_difference(volume_difference)} lbs'
        )

    print_by_category(
        items,
        sort_key=lambda item: (item[1], item[2]),
        format_line=format_line,
    )


def compare_to_last_week():
    today = today_date()
    week_start = start_of_week(today)
    start_of_last_week = days_before(week_start, 7)
    end_of_last_week = days_before(week_start, 1)

    current_sets, current_volume = get_volume_for_range(
        week_start,
        today
    )

    last_sets, last_volume = get_volume_for_range(
        start_of_last_week,
        end_of_last_week
    )

    print_volume_comparison(
        'Current Week vs Last Week',
        current_sets,
        current_volume,
        last_sets,
        last_volume
    )


def compare_to_4_week_average():
    today = today_date()
    start_of_28_days = days_before(today, 27)

    current_sets, current_volume = get_volume_for_range(
        start_of_week(today),
        today
    )

    total_sets, total_volume = get_volume_for_range(
        start_of_28_days,
        today
    )

    average_sets = {
        exercise: sets / 4
        for exercise, sets in total_sets.items()
    }

    average_volume = {
        exercise: volume / 4
        for exercise, volume in total_volume.items()
    }

    print_volume_comparison(
        'Current Week vs 4-Week Average',
        current_sets,
        current_volume,
        average_sets,
        average_volume
    )


def print_reports():
    show_this_week_volume()


# ======================================================================
# EXERCISE CATEGORIES
# Sorting exercises into Push / Pull / Legs/Other.
# ======================================================================

def singularize_exercise_name(exercise):
    if exercise.endswith('ies'):
        return exercise[:-3] + 'y'

    if exercise.endswith('s') and not exercise.endswith('ss'):
        return exercise[:-1]

    return exercise


def categorize_new_exercises(new_exercises, exercise_categories):
    if not new_exercises:
        return

    answer = input('\nCategorize new exercises? y/n: ').strip().lower()

    if answer != 'y':
        return

    category_choices = {
        '1': 'Push',
        'push': 'Push',

        '2': 'Pull',
        'pull': 'Pull',

        '3': 'Legs/Other',
        'legs': 'Legs/Other',
        'other': 'Legs/Other',
        'legs/other': 'Legs/Other',
    }

    for exercise in new_exercises:
        while True:
            print(f'\n{exercise}')
            print('1) Push')
            print('2) Pull')
            print('3) Legs/Other')
            print('4) Singularize')

            choice = input('Category: ').strip().lower()

            if choice == 'done':
                return

            if choice in ['4', 'singularize', 's']:
                new_exercise = singularize_exercise_name(exercise)

                if new_exercise == exercise:
                    print(f'{exercise} is already singular.')
                    continue

                rename_exercise_in_log(exercise, new_exercise)

                if exercise in new_exercises:
                    new_exercises.remove(exercise)

                if new_exercise not in new_exercises:
                    new_exercises.append(new_exercise)

                exercise = new_exercise
                print(f'Renamed to {exercise}.')
                continue

            if choice not in category_choices:
                print('Enter 1, 2, 3, 4, or done.')
                continue

            category = category_choices[choice]

            exercise_categories[exercise] = category
            save_exercise_category(exercise, category)

            print(f'{exercise} = {category}.')
            break


def find_uncategorized_exercises(exercise_categories):
    uncategorized = []

    for row in read_log_rows():
        exercise = row[2].strip()

        if not exercise:
            continue

        if (
            exercise not in exercise_categories
            and exercise not in uncategorized
        ):
            uncategorized.append(exercise)

    return uncategorized


def categorize_uncategorized_exercises(exercise_categories):
    uncategorized = find_uncategorized_exercises(
        exercise_categories
    )

    if not uncategorized:
        print('No uncategorized exercises.')
        return

    categorize_new_exercises(
        uncategorized,
        exercise_categories
    )


# ======================================================================
# WORKOUT MENU
# The numbered exercise list from 'workout push/pull/legs'.
# ======================================================================

def select_workout_menu(category_name, exercise_categories):
    categories = {
        'push': 'Push',
        'pull': 'Pull',
        'legs': 'Legs/Other',
        'other': 'Legs/Other',
        'legs/other': 'Legs/Other',
    }
    category = categories.get(category_name.strip().lower())

    if not category:
        print('Use: workout push/pull/legs')
        return None, []

    exercises = [
        exercise
        for exercise, exercise_category in exercise_categories.items()
        if exercise_category == category
    ]

    if not exercises:
        print(f'No {category} exercises.')
        return None, []

    total_sets = get_4_week_set_totals()
    exercises.sort(
        key=lambda exercise: (
            -total_sets.get(exercise, 0),
            exercise.lower(),
        )
    )
    return category, exercises


def show_workout_menu(category, exercises):
    if not category:
        print('No workout selected.')
        return

    print(f'\n{category}:')

    for number, exercise in enumerate(exercises, start=1):
        print(f'{number}. {exercise}')

    print()


# ======================================================================
# REHAB REMINDER
# ======================================================================

def show_rehab():
    today = datetime.now()
    day = today.day

    if day % 2 == 0:
        print('Even-day prehab:')
        for exercise in EVEN_REHAB:
            print(f'- {exercise}')
        print('\n')

    else:
        print('Odd-day prehab:')
        for exercise in ODD_REHAB:
            print(f'- {exercise}')
        print('\n')


# ======================================================================
# MAIN PROGRAM
# The input loop: commands and set entry.
# ======================================================================

class Session:
    """What the program remembers while a workout is running."""

    def __init__(self):
        self.exercise_categories = load_exercise_categories()
        self.new_exercises = []
        self.last_entries = []
        self.active_category = None
        self.active_exercises = []
        self.reports = []
        self.message = ''

    def add_report(self, text):
        if text:
            self.reports.append(text)
            self.reports = self.reports[-REPORTS_ON_SCREEN:]

    def remember_set(self, entry):
        self.last_entries.append(entry)
        self.last_entries = self.last_entries[-10:]


def repeat_set(session, entry):
    log_set(
        entry['exercise'],
        entry['weight'],
        entry['reps'],
        entry['note']
    )

    session.remember_set(entry.copy())

    print(
        f"> {entry['exercise']}, "
        f"{format_weight(entry['weight'])}, "
        f"{entry['reps']}, {entry['note']}"
    )


def parse_set_entry(session, entry):
    """Turn 'exercise,weight,reps[,note]' into a set, or print why not.

    Returns a dict with exercise, weight, reps and note, or None.
    """
    parts = entry.split(',')

    if len(parts) < 3:
        print(
            'Enter a set as exercise,weight,reps '
            'or add an optional note as a fourth value. '
            'Example: bench,185,8'
        )
        return None

    exercise = parts[0].strip()

    if exercise.isdigit():
        exercise_number = int(exercise)

        if not session.active_exercises:
            print('Select a workout first.')
            return None

        if not 1 <= exercise_number <= len(session.active_exercises):
            print(
                f'Exercise number must be 1-'
                f'{len(session.active_exercises)}.'
            )
            return None

        exercise = session.active_exercises[exercise_number - 1]

    if not exercise:
        print('Exercise name cannot be blank.')
        return None

    weight_text = parts[1].strip()
    reps_text = parts[2].strip()

    try:
        weight = float(weight_text)
    except ValueError:
        print('Weight must be a number. Example: bench,185,8')
        return None

    try:
        reps_value = float(reps_text)
    except ValueError:
        print('Reps must be a whole number. Example: bench,185,8')
        return None

    if not reps_value.is_integer():
        print('Reps must be a whole number. Example: bench,185,8')
        return None

    if len(parts) > 3:
        note = parts[3].strip()
    else:
        note = ''

    return {
        'exercise': exercise,
        'weight': weight,
        'reps': int(reps_value),
        'note': note,
    }


def log_entered_set(session, entry):
    new_set = parse_set_entry(session, entry)

    if new_set is None:
        return

    log_set(
        new_set['exercise'],
        new_set['weight'],
        new_set['reps'],
        new_set['note']
    )

    exercise = new_set['exercise']

    if (
        exercise not in session.exercise_categories
        and exercise not in session.new_exercises
    ):
        session.new_exercises.append(exercise)

    session.remember_set(new_set)


# ----------------------------------------------------------------------
# Command handlers. Each takes the session and whatever was typed after
# the command word ('' for commands without one). Returning True ends
# the program.
# ----------------------------------------------------------------------

def command_done(session, argument):
    categorize_new_exercises(
        session.new_exercises,
        session.exercise_categories
    )

    print_reports()
    return True


def command_workout(session, argument):
    category, exercises = select_workout_menu(
        argument,
        session.exercise_categories,
    )

    if category:
        session.active_category = category
        session.active_exercises = exercises


def command_menu(session, argument):
    # The menu is always on screen; this just redraws it.
    if not session.active_category:
        print('No workout selected.')


def command_today(session, argument):
    # Today's sets are always on screen; this just redraws them.
    pass


def command_repeat(session, argument):
    if not session.last_entries:
        print('No previous set to repeat.')
        return

    repeat_set(session, session.last_entries[-1])


def command_repeat_two(session, argument):
    if len(session.last_entries) < 2:
        print('Need at least two previous sets.')
        return

    for entry in session.last_entries[-2:]:
        repeat_set(session, entry)


def command_last(session, argument):
    show_copy_mode(argument.strip())


def command_history(session, argument):
    show_exercise_history(*argument.split(), weeks=HISTORY_WEEKS)


def command_full_history(session, argument):
    show_exercise_history(*argument.split())


def command_weekly_history(session, argument):
    show_weekly_exercise_history(argument.strip())


def command_categorize(session, argument):
    categorize_uncategorized_exercises(session.exercise_categories)


def command_help(session, argument):
    show_command_menu()


# What you type, the help text, and the function that runs.
# 'a / b' means either word works. A capitalized word (NAME, NAMES)
# means the command takes the rest of the line as its argument.
# Commands marked ignore_case also work in capitals.
COMMANDS = [
    ('done', 'Finish workout and print reports', command_done),
    ('workout NAME', 'Select a workout', command_workout),
    ('menu', 'Show workout exercises', command_menu),
    ('r', 'Repeat last set', command_repeat),
    ('r2', 'Repeat last 2 sets', command_repeat_two),
    ('w / week', 'Show current week volume', lambda session, argument: show_this_week_volume()),
    ('today', "Show today's logged sets", command_today),
    ('last NAME', 'Show last workout for exercise', command_last),
    ('show NAME', 'Same as last NAME', command_last),
    ('history NAMES', 'Show last 8 weeks for exercises', command_history),
    ('fh NAMES', 'Show full history for exercises', command_full_history),
    ('weekly history NAME', 'Show weekly sets and volume for an exercise', command_weekly_history),
    ('w-2', 'Show volume from two weeks ago', lambda session, argument: show_two_weeks_ago_volume()),
    ('avg4', 'Show 4-week average sets', lambda session, argument: show_average_sets(4)),
    ('avg8', 'Show 8-week average sets', lambda session, argument: show_average_sets(8)),
    ('compare last', 'Compare current week to last week', lambda session, argument: compare_to_last_week(), 'ignore_case'),
    ('compare avg4', 'Compare current week to 4-week average', lambda session, argument: compare_to_4_week_average(), 'ignore_case'),
    ('cat', 'Categorize uncategorized exercises', command_categorize),
    ('help', 'Show commands', command_help),
]


def find_command(entry):
    """Return (handler, argument) for a typed line, or (None, None)."""
    prefix_matches = []

    for usage, description, handler, *options in COMMANDS:
        ignore_case = 'ignore_case' in options
        typed = entry.lower() if ignore_case else entry

        for alias in usage.split(' / '):
            words = alias.split(' ')

            if words[-1].isupper():
                prefix = ' '.join(words[:-1]) + ' '
                prefix_matches.append((prefix, handler))
            elif typed == alias:
                return handler, ''

    for prefix, handler in prefix_matches:
        if entry.startswith(prefix):
            return handler, entry.replace(prefix, '', 1)

    return None, None


def show_command_menu():
    width = max(len(usage) for usage, *rest in COMMANDS) + 1

    print('\nCommands:')

    for usage, description, *rest in COMMANDS:
        print(f'  {usage:<{width}}{description}')

    print()


# ----------------------------------------------------------------------
# The screen. After every entry the console is cleared and redrawn as:
#   the last two reports, the workout menu, today's sets, then any
#   short message (an error, or the set that 'r' repeated).
# ----------------------------------------------------------------------

# Commands whose output is a short message, not a report.
MESSAGE_COMMANDS = [
    command_workout,
    command_menu,
    command_today,
    command_repeat,
    command_repeat_two,
]

# Commands that ask questions with input(), so their output can't be held back.
INTERACTIVE_COMMANDS = [command_done, command_categorize]


def clear_screen():
    if console is not None and hasattr(console, 'clear'):
        console.clear()
    else:
        # Not in Pythonista (for example the PC test): mark where it would clear.
        print('\n' + '~' * 40 + ' (screen cleared)')


def capture_output(function, *args):
    """Run function and return (its return value, what it printed)."""
    buffer = io.StringIO()

    with contextlib.redirect_stdout(buffer):
        result = function(*args)

    return result, buffer.getvalue().strip('\n')


def draw_screen(session):
    clear_screen()

    print('\n\n'.join(session.reports))

    if session.active_category:
        show_workout_menu(session.active_category, session.active_exercises)

    show_today_workout()

    if session.message:
        print()
        print(session.message)

    print()


def handle_entry(session, entry):
    """Run one typed line. Returns True when the program should end."""
    handler, argument = find_command(entry)

    if handler is None:
        _, session.message = capture_output(log_entered_set, session, entry)
        return False

    if handler in INTERACTIVE_COMMANDS:
        return handler(session, argument)

    finished, output = capture_output(handler, session, argument)

    if handler in MESSAGE_COMMANDS:
        session.message = output
    else:
        session.add_report(output)

    return finished


def main():
    session = Session()

    _, rehab = capture_output(show_rehab)
    session.add_report(rehab)

    while True:
        draw_screen(session)
        entry = input('> ').strip()
        session.message = ''

        if not entry:
            continue

        if handle_entry(session, entry):
            break


if __name__ == '__main__':
    main()
