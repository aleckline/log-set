import csv
from datetime import datetime, timedelta

filename = 'logset.csv'

odd_rehab = ['Wrist Curls', 'Wall Stretch', 'Glute Bridge']
even_rehab = ['Copenhagen Plank', 'Calves', 'Hamstrings']

def show_rehab():
	day = datetime.now().day
	if day % 2 == 1:
		print('Odd-day Rehab:')
		for exercise in odd_rehab:
			print('- ' + exercise.title())
	else:
		print('Even-day Rehab:')
		for exercise in even_rehab:
			print('- ' + exercise.title())

show_rehab()

print('\n')

def log_set(exercise, weight, reps):
	now = datetime.now()
	
	with open(filename, 'a', newline = '') as file:
		writer = csv.writer(file)
		writer.writerow([
			now.date(),
			now.strftime('%H:%M'),
			exercise,
			weight,
			reps
		])

last_entries = []

def calculate_volume(exercise, weight, reps):
	if exercise.endswith('iso'):
		reps = reps / 2
		
	return weight * reps

def format_weight(weight):
	weight = float(weight)

	if weight.is_integer():
		return int(weight)

	return weight

def show_weekly_volume():
	today = datetime.now().date()
	start_of_week = today - timedelta(days=today.weekday())

	weekly_volume = {}
	weekly_sets = {}

	with open(filename) as file:
		reader = csv.reader(file)

		for row in reader:
			if len(row) < 5: 
				continue
				
			date = datetime.strptime(row[0], '%Y-%m-%d').date()
			exercise = row[2]
			weight = format_weight(row[3])
			reps = int(row[4])
		
			if date >= start_of_week:
				volume = calculate_volume(exercise, weight, reps)
				weekly_volume[exercise] = weekly_volume.get(exercise, 0) + volume
				weekly_sets[exercise] = weekly_sets.get(exercise, 0) + 1

	for exercise in weekly_volume:
		sets = weekly_sets[exercise]
		volume = format_weight(weekly_volume[exercise])
		print(f'{exercise.title()}: {sets} sets, {volume} lbs')


while True:
	entry = input('Enter exercise, weight, reps: ')
	if entry == 'done':
		break
		
	if entry == 'r':
		if not last_entries:
			print('No previous entries from session.')
		
		last = last_entries[-1]
		
		last['Exercise'] = exercise
		last['Weight'] = weight
		last['reps'] = reps

		log_set(exercise, weight, reps)
		
		continue
		
	parts = entry.split(',')

	exercise = parts[0].strip()
	weight = parts[1].strip()
	reps = parts[2].strip()
	
	log_set(exercise, weight, reps)

	last_entries.append({
		'Exercise': exercise,
		'Weight': weight,
		'Reps': reps
		})
		
show_weekly_volume()
