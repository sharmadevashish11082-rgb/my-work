import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), 'todos.json')

def load_tasks():
	if not os.path.exists(DATA_FILE):
		return []
	try:
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		return []

def save_tasks(tasks):
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		json.dump(tasks, f, indent=2, ensure_ascii=False)

def view_tasks(tasks):
	if not tasks:
		print('No tasks.')
		return
	for i, t in enumerate(tasks, 1):
		status = '✔' if t.get('done') else ' ' 
		print(f"{i}. [{status}] {t.get('text')}")

def add_task(tasks):
	text = input('Task description: ').strip()
	if not text:
		print('Empty task not added.')
		return
	tasks.append({'text': text, 'done': False})
	save_tasks(tasks)
	print('Task added.')

def complete_task(tasks):
	view_tasks(tasks)
	try:
		idx = int(input('Complete task number: ')) - 1
		if 0 <= idx < len(tasks):
			tasks[idx]['done'] = True
			save_tasks(tasks)
			print('Task marked complete.')
		else:
			print('Invalid number.')
	except ValueError:
		print('Invalid input.')

def delete_task(tasks):
	view_tasks(tasks)
	try:
		idx = int(input('Delete task number: ')) - 1
		if 0 <= idx < len(tasks):
			removed = tasks.pop(idx)
			save_tasks(tasks)
			print(f"Removed: {removed.get('text')}")
		else:
			print('Invalid number.')
	except ValueError:
		print('Invalid input.')

def main():
	tasks = load_tasks()
	actions = {
		'1': ('Add task', add_task),
		'2': ('Complete task', complete_task),
		'3': ('Delete task', delete_task),
		'4': ('View all tasks', lambda t: view_tasks(t)),
		'5': ('Exit', None),
	}

	while True:
		print('\nTo-Do App')
		for k, (name, _) in actions.items():
			print(f"{k}. {name}")
		choice = input('Choose an option: ').strip()
		if choice == '5':
			print('Goodbye')
			break
		action = actions.get(choice)
		if not action:
			print('Invalid choice')
			continue
		action[1](tasks)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print('\nExiting')
		sys.exit(0)

