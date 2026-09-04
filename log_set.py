import csv
from datetime import datetime

FILENAME = 'gym_log.csv'

CATEGORY_FILENAME = 'exercise_categories.csv'

ODD_REHAB = ['Wrist Curls', 'Neck', 'Quads', 'Wall Stretch', 'Glute Bridge']
EVEN_REHAB = ['Straight Leg Raise', 'Copenhagen Plank', 'Calves', 'Hamstrings']


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

def calculate_volume(exercise, weight, reps):
    if exercise.endswith('_iso'):
        reps = reps / 2

    return weight * reps

def format_weight(weight):
    weight = float(weight)

    if weight.is_integer():
        return int(weight)

    return weight

def print_report_header(title):
    print()
    print('=' * 40)
    print(title)
    print('=' * 40)
    print()

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

def print_categorized_volume(volume_sets, volume_total):
    exercise_categories = load_exercise_categories()

    category_order = [
        'Push',
        'Pull',
        'Legs/Other',
        'Uncategorized',
    ]

    categorized_exercises = {
        category: []
        for category in category_order
    }

    for exercise, volume in volume_total.items():
        category = exercise_categories.get(
            exercise,
            'Uncategorized'
        )

        if category not in categorized_exercises:
            category = 'Uncategorized'

        categorized_exercises[category].append(
            (exercise, volume)
        )

    printed_category = False

    for category in category_order:
        exercises = categorized_exercises[category]

        if not exercises:
            continue

        if printed_category:
            print()

        print(f'{category}:')

        exercises.sort(
            key=lambda item: item[1],
            reverse=True
        )

        for exercise, volume in exercises:
            sets = volume_sets[exercise]
            set_word = 'set' if sets == 1 else 'sets'

            print(
                f'    {exercise:<22}'
                f'{sets:>3} {set_word}, '
                f'{volume:>8,.0f} lbs'
            )

        printed_category = True

def show_volume_for_range(label, start_date, end_date):
    volume_sets = {}
    volume_total = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()
                weight = float(row[3])
                reps = int(float(row[4]))

            except ValueError:
                continue

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

    print_report_header(label.title())

    if not volume_total:
        print('    No workouts logged.')
        return

    print_categorized_volume(
        volume_sets,
        volume_total
    )

def show_rolling_7_day_volume():
    today = datetime.now().date()

    start_date = today.fromordinal(
        today.toordinal() - 6
    )

    rolling_sets = {}
    rolling_volume = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()
                weight = float(row[3])
                reps = int(float(row[4]))

            except ValueError:
                continue

            if start_date <= date <= today:
                volume = calculate_volume(
                    exercise,
                    weight,
                    reps
                )

                rolling_sets[exercise] = (
                    rolling_sets.get(exercise, 0) + 1
                )

                rolling_volume[exercise] = (
                    rolling_volume.get(exercise, 0)
                    + volume
                )

    print_report_header('7-Day Rolling Volume')

    if not rolling_volume:
        print('    No workouts logged.')
        return

    print_categorized_volume(
        rolling_sets,
        rolling_volume
    )

def print_reports():
    today = datetime.now().date()
    start_of_week = today.fromordinal(today.toordinal() - today.weekday())
    end_of_week = today

    start_of_last_week = start_of_week.fromordinal(start_of_week.toordinal() - 7)
    end_of_last_week = start_of_week.fromordinal(start_of_week.toordinal() - 1)

    show_volume_for_range('Weekly volume', start_of_week, end_of_week)
    #show_volume_for_range('Last week volume', start_of_last_week, end_of_last_week)

show_rehab()

last_entries = []

def show_copy_mode(exercise_name):
    entries = []

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            if row[2] == exercise_name:
                entries.append(row)

    if not entries:
        print(f'No history found for {exercise_name}.')
        return

    last_date = entries[-1][0]

    print(f'\nLast {exercise_name} workout: {last_date}\n')

    for row in entries:
        if row[0] == last_date:
            print(f'{row[2]}, {row[3]}, {row[4]}, {row[5]}')

def show_today_workout():
    today = datetime.now().date()
    entries = {}
    exercise_order = []

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()
                weight = float(row[3])
                reps = int(float(row[4]))
                note = row[5].strip()

            except ValueError:
                continue

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

    for exercise in exercise_order:
        print(f'    {exercise}')

        for (weight, note), reps_list in entries[exercise].items():
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

            weight_display = int(weight) if weight.is_integer() else weight
            reps_display = ', '.join(grouped)

            if note:
                print(
                    f'        {weight_display:>6}  '
                    f'{reps_display:<10}'
                    f'{note}'
                )
            else:
                print(
                    f'        {weight_display:>6}  '
                    f'{reps_display}'
                )

        print()

def show_exercise_history(*exercise_names):
    history = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            exercise = row[2]

            if exercise not in exercise_names:
                continue

            try:
                date = row[0]
                weight = float(row[3])
                reps = int(float(row[4]))
            except ValueError:
                continue

            key = (date, exercise, weight)

            history.setdefault(key, []).append(reps)

    if not history:
        print('No history found.')
        return

    print(f'\n{"Date":<12}\t{"Exercise":<15}\t{"Weight":<8}\tSets×Reps')

    sorted_history = sorted(
        history.items(),
        key=lambda item: (item[0][0], item[0][1]),
        reverse=True
    )

    for (date, exercise, weight), reps_list in sorted_history:

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

        weight_display = int(weight) if weight.is_integer() else weight

        print(
            f'{date:<12}\t'
            f'{exercise:<15}\t'
            f'{weight_display:<8}\t'
            f'{", ".join(grouped)}'
        )

def show_4_week_average():
    today = datetime.now().date()

    start_date = today.fromordinal(
        today.toordinal() - 27
    )

    total_sets = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()

            except ValueError:
                continue

            if start_date <= date <= today:
                total_sets[exercise] = (
                    total_sets.get(exercise, 0) + 1
                )

    print_report_header('4-Week Average Sets')

    if not total_sets:
        print('    No workouts logged in the previous 28 days.')
        return

    exercise_categories = load_exercise_categories()

    category_order = [
        'Push',
        'Pull',
        'Legs/Other',
        'Uncategorized',
    ]

    categorized_exercises = {
        category: []
        for category in category_order
    }

    for exercise, sets in total_sets.items():
        category = exercise_categories.get(
            exercise,
            'Uncategorized'
        )

        if category not in categorized_exercises:
            category = 'Uncategorized'

        average_sets = sets / 4

        categorized_exercises[category].append(
            (exercise, average_sets)
        )

    printed_category = False

    for category in category_order:
        exercises = categorized_exercises[category]

        if not exercises:
            continue

        if printed_category:
            print()

        print(f'{category}:')

        exercises.sort(
            key=lambda item: item[1],
            reverse=True
        )

        for exercise, average_sets in exercises:
            if average_sets.is_integer():
                sets_display = int(average_sets)
            else:
                sets_display = round(average_sets, 1)

            set_word = (
                'set/week'
                if average_sets == 1
                else 'sets/week'
            )

            print(
                f'    {exercise:<22}'
                f'{sets_display:>5} {set_word}'
            )

        printed_category = True

def show_8_week_average():
    today = datetime.now().date()

    start_date = today.fromordinal(
        today.toordinal() - 55
    )

    total_sets = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()

            except ValueError:
                continue

            if start_date <= date <= today:
                total_sets[exercise] = (
                    total_sets.get(exercise, 0) + 1
                )

    print_report_header('8-Week Average Sets')

    if not total_sets:
        print('    No workouts logged in the previous 56 days.')
        return

    exercise_categories = load_exercise_categories()

    category_order = [
        'Push',
        'Pull',
        'Legs/Other',
        'Uncategorized',
    ]

    categorized_exercises = {
        category: []
        for category in category_order
    }

    for exercise, sets in total_sets.items():
        category = exercise_categories.get(
            exercise,
            'Uncategorized'
        )

        if category not in categorized_exercises:
            category = 'Uncategorized'

        average_sets = sets / 8

        categorized_exercises[category].append(
            (exercise, average_sets)
        )

    printed_category = False

    for category in category_order:
        exercises = categorized_exercises[category]

        if not exercises:
            continue

        if printed_category:
            print()

        print(f'{category}:')

        exercises.sort(
            key=lambda item: item[1],
            reverse=True
        )

        for exercise, average_sets in exercises:
            if average_sets.is_integer():
                sets_display = int(average_sets)
            else:
                sets_display = round(average_sets, 1)

            set_word = (
                'set/week'
                if average_sets == 1
                else 'sets/week'
            )

            print(
                f'    {exercise:<22}'
                f'{sets_display:>5} {set_word}'
            )

        printed_category = True

def get_volume_for_range(start_date, end_date):
    volume_sets = {}
    volume_total = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()
                weight = float(row[3])
                reps = int(float(row[4]))

            except ValueError:
                continue

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

    exercise_categories = load_exercise_categories()

    category_order = [
        'Push',
        'Pull',
        'Legs/Other',
        'Uncategorized',
    ]

    categorized_exercises = {
        category: []
        for category in category_order
    }

    for exercise in all_exercises:
        set_difference = (
            current_sets.get(exercise, 0)
            - comparison_sets.get(exercise, 0)
        )

        volume_difference = (
            current_volume.get(exercise, 0)
            - comparison_volume.get(exercise, 0)
        )

        category = exercise_categories.get(
            exercise,
            'Uncategorized'
        )

        if category not in categorized_exercises:
            category = 'Uncategorized'

        categorized_exercises[category].append(
            (
                exercise,
                set_difference,
                volume_difference,
            )
        )

    printed_category = False

    for category in category_order:
        exercises = categorized_exercises[category]

        if not exercises:
            continue

        if printed_category:
            print()

        print(f'{category}:')

        exercises.sort(
            key=lambda item: (
                item[1],
                item[2],
            ),
            reverse=True
        )

        for (
            exercise,
            set_difference,
            volume_difference,
        ) in exercises:

            sets_display = format_set_difference(
                set_difference
            )

            volume_display = format_volume_difference(
                volume_difference
            )

            print(
                f'    {exercise:<18}'
                f'{sets_display:>6} sets, '
                f'{volume_display} lbs'
            )

        printed_category = True

def compare_to_last_week():
    today = datetime.now().date()

    start_of_week = today.fromordinal(
        today.toordinal() - today.weekday()
    )

    start_of_last_week = start_of_week.fromordinal(
        start_of_week.toordinal() - 7
    )

    end_of_last_week = start_of_week.fromordinal(
        start_of_week.toordinal() - 1
    )

    current_sets, current_volume = get_volume_for_range(
        start_of_week,
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
    today = datetime.now().date()

    start_of_week = today.fromordinal(
        today.toordinal() - today.weekday()
    )

    start_of_28_days = today.fromordinal(
        today.toordinal() - 27
    )

    current_sets, current_volume = get_volume_for_range(
        start_of_week,
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

def show_weekly_exercise_history(exercise_name):
    weekly_sets = {}
    weekly_volume = {}

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

            try:
                date = datetime.strptime(
                    row[0],
                    '%Y-%m-%d'
                ).date()

                exercise = row[2].strip()
                weight = float(row[3])
                reps = float(row[4])

            except ValueError:
                continue

            if exercise != exercise_name:
                continue

            week_start = date.fromordinal(
                date.toordinal() - date.weekday()
            )

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

def save_exercise_category(exercise, category):
    with open(CATEGORY_FILENAME, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([exercise, category])

def singularize_exercise_name(exercise):
    if exercise.endswith('ies'):
        return exercise[:-3] + 'y'

    if exercise.endswith('s') and not exercise.endswith('ss'):
        return exercise[:-1]

    return exercise

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

    with open(FILENAME) as file:
        reader = csv.reader(file)

        for row in reader:
            if len(row) < 6:
                continue

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

def show_command_menu():
	print('\nCommands:')
	print('  done          Finish workout and print reports')
	print('  r             Repeat last set')
	print('  r2            Repeat last 2 sets')
	print('  w / week      Show current week volume')
	print('  today         Show today\'s logged sets')
	print('  last NAME     Show last workout for exercise')
	print('  show NAME     Same as last NAME')
	print('  history NAMES Show history for one or more exercises')
	print('  w-2           Show volume from two weeks ago')
	print('  avg4          Show 4-week average sets')
	print('  compare last  Compare current week to last week')
	print('  compare avg4  Compare current week to 4-week average')
	print('  cat           Categorize uncategorized exercises')
	print('  menu          Show this menu')
	print()

exercise_categories = load_exercise_categories()
new_exercises = []

while True:
    entry = input('> ')

    entry = entry.strip()

    if entry in ['menu', 'help']:
        show_command_menu()
        continue

    if entry == 'cat':
        categorize_uncategorized_exercises(
            exercise_categories
        )
        continue

    if entry == 'done':
        categorize_new_exercises(
            new_exercises,
            exercise_categories
        )

        print_reports()
        break

    if entry == 'r':
        if not last_entries:
            print('No previous set to repeat.')
            continue

        last = last_entries[-1]

        log_set(
            last['exercise'],
            last['weight'],
            last['reps'],
            last['note']
        )

        last_entries.append(last.copy())
        last_entries = last_entries[-10:]

        print(
            f"> {last['exercise']}, "
            f"{format_weight(last['weight'])}, "
            f"{last['reps']}, {last['note']}"
        )
        continue

    if entry == 'r2':
        if len(last_entries) < 2:
            print('Need at least two previous sets.')
            continue

        entries_to_repeat = last_entries[-2:]

        for last in entries_to_repeat:
            log_set(
                last['exercise'],
                last['weight'],
                last['reps'],
                last['note']
            )

            last_entries.append(last.copy())

            print(
                f"> {last['exercise']}, "
                f"{format_weight(last['weight'])}, "
                f"{last['reps']}, {last['note']}"
            )

        last_entries = last_entries[-10:]
        continue

    if entry.startswith('show '):
        exercise_name = entry.replace('show ', '', 1).strip()
        show_copy_mode(exercise_name)
        continue

    if entry.startswith('weekly history '):
        exercise_name = entry.replace('weekly history ', '', 1).strip()
        show_weekly_exercise_history(exercise_name)
        continue
        


    if entry.startswith('last '):
        exercise_name = entry.replace('last ', '', 1).strip()
        show_copy_mode(exercise_name)
        continue

    if entry.startswith('history '):
        exercises = entry.split()[1:]
        show_exercise_history(*exercises)
        continue

    if entry in ['w', 'week']:
        today = datetime.now().date()
        start_of_week = today.fromordinal(
            today.toordinal() - today.weekday()
        )

        show_volume_for_range(
            'Weekly volume',
            start_of_week,
            today
        )
        continue

    if entry == 'today':
        show_today_workout()
        continue

    if entry == 'w-2':
        today = datetime.now().date()
        start_of_week = today.fromordinal(
            today.toordinal() - today.weekday()
        )

        start_date = start_of_week.fromordinal(
            start_of_week.toordinal() - 14
        )
        end_date = start_of_week.fromordinal(
            start_of_week.toordinal() - 8
        )

        show_volume_for_range(
            'Two weeks ago volume',
            start_date,
            end_date
        )
        continue

    if entry == 'avg4':
        show_4_week_average()
        continue
        
    if entry == 'avg8':
        show_8_week_average()
        continue

    if entry.strip().lower() == 'compare last':
        compare_to_last_week()
        continue

    if entry.strip().lower() == 'compare avg4':
        compare_to_4_week_average()
        continue

    parts = entry.split(',')
    parts = entry.split(',')

    exercise = parts[0].strip()
    weight = float(parts[1].strip())
    reps = int(float(parts[2].strip()))

    if len(parts) > 3:
        note = parts[3].strip()
    else:
        note = ''

    log_set(exercise, weight, reps, note)

    if (
        exercise not in exercise_categories
        and exercise not in new_exercises
    ):
        new_exercises.append(exercise)

    last_entries.append({
        'exercise': exercise,
        'weight': weight,
        'reps': reps,
        'note': note,
    })

    last_entries = last_entries[-10:]
