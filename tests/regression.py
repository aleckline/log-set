"""Before/after check for refactoring log-set.

Runs log_set.py against made-up workout data with the clock frozen,
feeds it a fixed list of commands, and compares everything it prints
(plus the CSV files it leaves behind) to tests/golden.txt.

    python tests/regression.py           # compare with golden.txt
    python tests/regression.py --record  # save current output as golden.txt

This is a development tool only; log_set.py never imports it.
"""

import datetime as datetime_module
import difflib
import io
import os
import runpy
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, 'log_set.py')
GOLDEN = os.path.join(HERE, 'golden.txt')

# Thursday, so "this week" has a few days of data in it.
FROZEN_NOW = datetime_module.datetime(2026, 10, 29, 18, 30)

CATEGORIES = [
    ('bench', 'Push'),
    ('ohp', 'Push'),
    ('dip', 'Push'),
    ('pullup', 'Pull'),
    ('row', 'Pull'),
    ('curl_iso', 'Pull'),
    ('squat', 'Legs/Other'),
    ('deadlift', 'Legs/Other'),
    ('odd', 'Not A Category'),
]

COMMANDS = [
    'help',
    'today',
    'w',
    'week',
    'w-2',
    'avg4',
    'avg8',
    'compare last',
    'compare avg4',
    'last bench',
    'show squat',
    'last nothing',
    'history bench squat',
    'history nothing',
    'weekly history bench',
    'weekly history curl_iso',
    'weekly history nothing',
    'menu',
    'workout dance',
    'workout push',
    'menu',
    '1,100,5',
    '9,100,5',
    '',
    'bench',
    ',100,5',
    'bench,abc,5',
    'bench,100,abc',
    'bench,100,5.5',
    'r',
    'r2',
    'bench,185,8,felt good',
    'r',
    'r2',
    'curl_iso,30,12',
    'lunges,50,10,left knee ok',
    'today',
    'w',
    'cat',
    'y',
    'banana',
    'done',
    'done',
    'y',
    '4',
    '4',
    '3',
]


def build_log():
    rows = []
    start = FROZEN_NOW.date() - datetime_module.timedelta(days=62)

    for offset in range(63):
        day = start + datetime_module.timedelta(days=offset)
        date = day.isoformat()
        week = offset // 7

        if offset % 7 == 0:
            for reps in (8, 8, 6):
                rows.append([date, '17:00', 'bench', 185 + 5 * week, reps, ''])
            rows.append([date, '17:20', 'dip', 0, 12, 'bodyweight'])
            rows.append([date, '17:30', 'ohp', 95.5, 5, ''])

        if offset % 7 == 2:
            for reps in (10, 9, 9):
                rows.append([date, '18:00', 'pullup', 200, reps, ''])
            rows.append([date, '18:15', 'row', 135, 10, 'strap'])
            rows.append([date, '18:20', 'curl_iso', 25, 12, ''])

        if offset % 7 == 4:
            for reps in (5, 5, 5):
                rows.append([date, '19:00', 'squat', 275 + 10 * week, reps, ''])
            rows.append([date, '19:30', 'deadlift', 315, 3, 'belt'])
            rows.append([date, '19:40', 'calves', 90, 15, ''])

        if offset % 11 == 0:
            rows.append([date, '20:00', 'odd', 10, 10, ''])

    # A few bad or old-format rows the reader must skip.
    rows.insert(5, ['2026-09-01', '10:00', 'bench', 135, 5])
    rows.insert(9, ['not-a-date', '10:00', 'bench', 135, 5, ''])
    rows.insert(12, ['2026-09-02', '10:00', 'bench', 'heavy', 5, ''])
    rows.append([FROZEN_NOW.date().isoformat(), '07:00', 'bench', 200, 3, 'am'])

    lines = [','.join(str(value) for value in row) for row in rows]
    # No trailing newline, to exercise log_set's newline repair.
    return '\n'.join(lines)


def build_categories():
    return '\n'.join(f'{name},{category}' for name, category in CATEGORIES) + '\n'


def child(workdir):
    """Run log_set.py in this process with a frozen clock."""

    class FrozenDatetime(datetime_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return FROZEN_NOW

    datetime_module.datetime = FrozenDatetime

    os.chdir(workdir)
    sys.path.insert(0, REPO)
    sys.stdin = io.StringIO('\n'.join(COMMANDS) + '\n')
    sys.argv = [SCRIPT]

    try:
        runpy.run_path(SCRIPT, run_name='__main__')
    except EOFError:
        print('<<EOF>>')


def run_once():
    with tempfile.TemporaryDirectory() as workdir:
        with open(os.path.join(workdir, 'gym_log.csv'), 'w', newline='') as file:
            file.write(build_log())

        with open(os.path.join(workdir, 'exercise_categories.csv'), 'w', newline='') as file:
            file.write(build_categories())

        result = subprocess.run(
            [sys.executable, os.path.abspath(__file__), '--child', workdir],
            capture_output=True,
            text=True,
            encoding='utf-8',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'},
        )

        parts = ['=== STDOUT ===', result.stdout]

        if result.stderr:
            parts += ['=== STDERR ===', result.stderr]

        for name in ('gym_log.csv', 'exercise_categories.csv'):
            with open(os.path.join(workdir, name), newline='') as file:
                parts += [f'=== {name} ===', file.read()]

        return '\n'.join(parts)


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--child':
        child(sys.argv[2])
        return

    output = run_once()

    if '--record' in sys.argv:
        with open(GOLDEN, 'w', encoding='utf-8', newline='\n') as file:
            file.write(output)
        print(f'Recorded {GOLDEN}')
        return

    with open(GOLDEN, encoding='utf-8', newline='') as file:
        expected = file.read()

    if output == expected:
        print('OK: output matches golden.txt')
        return

    sys.stdout.writelines(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            output.splitlines(keepends=True),
            'golden.txt',
            'current',
        )
    )
    sys.exit(1)


if __name__ == '__main__':
    main()
