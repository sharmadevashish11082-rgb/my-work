#!/usr/bin/env python3
"""Simple CLI Expense Tracker

Usage:
  - add: Add an expense
  - list: List expenses
  - delete: Delete by id
  - summary: Show totals by category
  - exit: Quit and save
"""

import json
import os
import datetime

DATA_FILE = os.path.expanduser('~/.expenses.json')

def load():
	if os.path.exists(DATA_FILE):
		with open(DATA_FILE, 'r', encoding='utf-8') as f:
			return json.load(f)
	return []

def save(items):
	with open(DATA_FILE, 'w', encoding='utf-8') as f:
		json.dump(items, f, indent=2, ensure_ascii=False)

def add(items):
	try:
		amount = float(input('Amount: ').strip())
	except ValueError:
		print('Invalid amount')
		return
	category = input('Category: ').strip() or 'misc'
	note = input('Note: ').strip()
	item = {
		'id': int(datetime.datetime.now().timestamp()*1000),
		'amount': amount,
		'category': category,
		'note': note,
		'date': datetime.datetime.now().isoformat(),
	}
	items.append(item)
	print('Added')

def list_items(items):
	if not items:
		print('No expenses')
		return
	for it in items:
		print(f"{it['id']} | {it['date'][:19]} | {it['category']:10} | {it['amount']:8.2f} | {it['note']}")

def delete(items):
	idstr = input('ID to delete: ').strip()
	try:
		idv = int(idstr)
	except ValueError:
		print('Invalid id')
		return
	before = len(items)
	items[:] = [i for i in items if i.get('id') != idv]
	print('Deleted' if len(items) < before else 'Not found')

def summary(items):
	totals = {}
	for i in items:
		totals[i['category']] = totals.get(i['category'], 0) + i['amount']
	for cat, amt in sorted(totals.items()):
		print(f"{cat:10} : {amt:.2f}")
	print('Total:', sum(i['amount'] for i in items))

def main():
	items = load()
	cmds = {'add': add, 'list': list_items, 'delete': delete, 'summary': summary}
	try:
		while True:
			cmd = input('> ').strip().lower()
			if cmd in ('exit', 'quit'):
				break
			fn = cmds.get(cmd)
			if fn:
				fn(items)
			else:
				print('Commands: add, list, delete, summary, exit')
	finally:
		save(items)

if __name__ == '__main__':
	main()


