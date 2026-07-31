import csv
from datetime import datetime

filename = 'logset.csv'

odd_rehab = ['Wrist Curls', 'Wall Stretch', 'Glute Bridge']
even_rehab = ['Copenhagen Plank', 'Calves', 'Hamstrings']

def show_rehab():
	day = datetime.now().day
	if day % 2 == 1:
		print(odd_rehab)
	else:
		print(even_rehab)

show_rehab()

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
		
while True:
	completed_set = input('Enter exercise, weight, reps: ')
	if completed_set == 'done':
		break
		
	parts = completed_set.split(',')

	exercise = parts[0].strip()
	weight = parts[1].strip()
	reps = parts[2].strip()
	
	log_set(exercise, weight, reps)



