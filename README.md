# Expense Tracker — Pure Python

A desktop expense tracker built with **pure Python**: Tkinter GUI, SQLite storage,
EasyOCR receipt scanning, and matplotlib charts. No web frameworks, no Electron —
just Python.

## Features

### Expense management
- Add / edit / delete expenses (automatic ID, amount & date validation)
- View all, search, and filter by category, month, amount range, date range,
  shop and notes
- 10 categories with automatic keyword-based categorisation
  (DMart → Groceries, Uber → Transport, Netflix → Entertainment, ...)

### Receipt scanner (OCR)
- Upload a receipt image or capture one with the camera
- EasyOCR extracts shop name, date, total, currency and (best-effort) line items
- Review and correct the extracted fields before saving
- The receipt image is saved into `receipts/` and linked to the expense —
  view it later from the expense list
- OCR confidence indicator (green / orange / red)

### Dashboard (fintech design)
- Premium fintech look: dark-teal page (#173D40) with a large centered white
  container, header navigation, greeting, filter/utility row
- Income card, Expense Strategy (top categories + change badge), Overview
  (budget donut: available / planned / other), Money Flow (spend trend)
- My Finances: virtual credit card (add/remove cards) and an expandable
  Wealth Overview tree
- Key stats strip: today, this week, this month, transactions, avg daily,
  top category — all re-filtered by the period selector
- Interactions: period filter + custom range, search (jumps to Expenses),
  CSV download, "New Payments", notification & settings dropdowns
- The three-column grid stacks into one column on narrow windows

### Charts & Analytics
- Spending by category (pie), monthly spending (bar), daily spending (line),
  category comparison (actual vs budget), period comparison (this vs previous),
  top merchants (bar), spending trend (cumulative line)

### Time-based analysis & budgets
- Period selector: Today, Yesterday, Last 7 days, This month, Last month,
  This year, All time, Custom range — filters every stat, chart and budget
- Overall + per-category monthly budgets with remaining amount, % used,
  and warnings when approaching (≥ 80%) or exceeding (> 100%)

## Requirements

The core app (dashboard + expense tracking) needs only the Python standard
library — tkinter and sqlite3 come bundled with Python on Windows/macOS.

Optional extras:

| Feature                    | Install                                     |
|----------------------------|---------------------------------------------|
| Charts                     | `pip install matplotlib`                    |
| Receipt OCR                | `pip install easyocr`                       |
| Receipt preview / camera   | `pip install pillow opencv-python`          |

Install everything at once:

```
pip install -r requirements.txt
```

## Run

```
python main.py
```

On Windows you can also double-click **`run.bat`** (and run **`install_deps.bat`**
once to install the optional packages).

## Sample data

To see the dashboard, charts and budgets populated right away:

```
python demo_data.py            # seeds sample data only if the DB is empty
python demo_data.py --reset    # clears expenses/budgets, then reseeds
```

## Tests

Pure-Python unit tests (no third-party packages needed):

```
python -m unittest test_core -v
```

## Project layout

| File          | Purpose                                              |
|---------------|------------------------------------------------------|
| `main.py`     | Tkinter GUI: Dashboard, Expenses, Receipt, Charts    |
| `dashboard.py`| The fintech home screen (header, cards, donut/line charts, dialogs) |
| `database.py` | SQLite storage: CRUD, search/filters, budgets, settings, cards, CSV |
| `expense.py`  | Validated Expense model                              |
| `utils.py`    | Categories, currency detection, date parsing, validation |
| `ocr.py`      | EasyOCR receipt scanning                            |
| `charts.py`   | matplotlib chart helpers (incl. dashboard mini-charts) |
| `theme.py`    | Light fintech palette + ttk styles                  |
| `demo_data.py`| Seeds sample expenses, budgets, income + a card     |
| `backup.py`   | Back up / restore the database + receipts to a zip  |
| `run.bat`     | Windows double-click launcher (with `install_deps.bat`) |
| `test_core.py`| Unit tests for the pure logic                       |
| `test_dashboard.py` | Unit tests for dashboard helpers + new DB features |

Note: the dashboard's Income history and Wealth Overview show sample values
(the app tracks expenses, not income or assets) — set your monthly income by
clicking the Income number.

## Backups

```
python backup.py                  # create backup_YYYYMMDD_HHMMSS.zip
python backup.py --restore x.zip  # restore (asks before overwriting)
```


Note: the first receipt scan downloads the EasyOCR model and can take a while —
subsequent scans are fast.

---

# 🕹️ Freebuff Arcade — 21 games in one Python app

A second project in this repo: **21 playable games in a single Python app**,
built with pygame (pygame-ce is already installed in this environment).

## Run

```
python play_games.py        # open the arcade dashboard (or double-click play_games.bat)
python test_games.py        # headless smoke test that boots every game
```

The **dashboard** is the main menu: category tabs (Arcade, Action, RPG,
Strategy, Racing, Puzzle, Sim) filter the card grid, the bottom panel shows the
selected game's details with a big PLAY button, and session stats track how
many games you've played. Browse with the arrow keys or mouse, press Enter (or
click PLAY) to launch, digits 1-9 jump straight to a game, Tab cycles
categories, and Esc returns to the dashboard from any game.

Note: `main.py` at the repo root belongs to the Expense Tracker app — the
arcade lives in `play_games.py`.

## The games

| # | Game                | What it is                                             |
|---|---------------------|--------------------------------------------------------|
| 1 | Pac-Dash 👻         | Faithful Pac-Man: BFS ghost AI (Blinky/Pinky/Inky/Clyde), tunnel wrap, fruit |
| 2 | Quest RPG 🧙        | Top-down overworld: NPCs, slimes, quests, level-ups    |
| 3 | Turn RPG ⚔️         | Menu-driven party battles, spells, waves, boss         |
| 4 | Tower Defense 🏰    | 3 tower types, 12 waves, upgrades, muzzle velocities   |
| 5 | Bullet Hell 🚀      | Pattern bullet storms, ship momentum, boss fights      |
| 6 | Galaga Strike 🛸    | Formation waves, gravity swoop dives, UFO bonus        |
| 7 | Turbo Circuit 🏎️    | Real car physics: power curve, aero drag, grip-limited steering |
| 8 | Highway Rush 🏁     | Power-curve acceleration, real km/h and distance       |
| 9 | Zombie Outbreak 🧟  | Horde momentum & separation, stamina sprint, reloads   |
|10 | Run & Gun 🔫        | Real jump physics: variable jump, coyote time, terminal velocity |
|11 | Street Fury 🥷      | 1v1 fighting with punch/kick/block, recoil, an AI      |
|12 | Street Brawl ⚔️     | Beat-'em-up: combo chains, waves, a boss               |
|13 | Deep Dungeon 🗺️     | Roguelike: fog of war, hunger, monsters, chests, keys  |
|14 | Sokoban 🧩          | 6 push-box puzzles with undo and restart               |
|15 | Grand Chess ♟️      | FIDE rules: castling, en passant, promotion, draws, minimax AI |
|16 | Arcane Duel 🃏      | Card battle: mana, shields, poison, greedy AI          |
|17 | Rise of Kingdoms 🌎 | Civ-style: found cities, tech, armies, conquer         |
|18 | Ironclad Command 🏰 | Real-time strategy: gold mines, units, HQ assault      |
|19 | Mega Park Tycoon 💰 | Real economics: inflation, supply & demand, wear upkeep|
|20 | Harvest Hills 🌾    | Real crops & seasons, weather, soil depletion, markets |
|21 | Wilderness 🏝️      | Real vitals: kcal, water, body temp, climate, wolves   |

## Project layout

| Path              | Purpose                                              |
|-------------------|------------------------------------------------------|
| `play_games.py`   | Entry point — opens the arcade dashboard             |
| `games/engine.py` | Shared framework: loop, fonts, menus, particles, HUD + physics helpers |
| `games/dashboard.py` | The main menu: category tabs, cards, PLAY panel   |
| `games/launcher.py`| Simpler grid menu (still works as an alternative)    |
| `games/*.py`      | One module per game                                  |
| `test_games.py`   | Headless smoke test (boots every game)               |

## How the games stay true to their originals

Every game that copies a real original plays by that original's rules and
physics:

- **Pac-Dash** — the four ghosts use the authentic arcade targeting logic
  (Blinky chases you, Pinky ambushes 4 cells ahead, Inky mirrors Blinky, Clyde
  retreats when close), find you via true BFS shortest-path through the maze,
  and can't reverse mid-corridor. The maze has side tunnels that wrap around
  the screen edges, a ghost house, classic scoring (10/dot, 50/pellet,
  200/ghost), and a cherry at 70 dots and a strawberry at 170.
- **Grand Chess** — full FIDE rules, including the draws: stalemate, the
  50-move rule, threefold repetition, and insufficient material, each
  announced with its reason.
- **Galaga Strike** — divers peel off in pairs and swoop down under
  acceleration (gravity), shoot while diving, then loop back to formation.
- **Turbo Circuit / Highway Rush** — real car dynamics: engine force follows
  a power curve (P/v), air drag grows with v², rolling resistance is constant,
  so top speed *emerges* from power vs. drag, and cornering understeers as
  speed rises instead of snapping around.
- **Run & Gun** — real jump physics: gravity with terminal velocity, a
  variable jump (tap for a hop, hold for a full jump), coyote time, and input
  buffering.
- **Zombie Outbreak** — zombies carry momentum and push each other apart like
  a real horde; you sprint on a stamina bar that exhausts.
- **Wilderness** — real survival vitals: you burn ~2200 kcal/day, need water
  (carried in a canteen), and your core temperature drops toward the air
  temperature at night — no fire means hypothermia. The clock runs 24 real
  hours per day and the air follows a diurnal curve.
- **Harvest Hills** — real crop facts (wheat is spring/autumn, tomato and corn
  need summer), a daily weather forecast (rain waters fields, drought hurts),
  soil that is depleted by harvesting, and market prices that rise in winter.
- **Mega Park Tycoon** — inflation raises build costs, guest visits build
  demand that lifts income, and heavily-used rides cost more upkeep.
- **Deep Dungeon** — the classic roguelike hunger clock: every step burns
  food, and a starving adventurer dies.

The shared physics helpers (power-curve `car_dynamics`, gravity with terminal
velocity, elastic collisions, drag) live in `games/engine.py`, so any game can
opt into real-world motion.

Each game is a self-contained module that subclasses `games.engine.Game`, so any
of them can be run directly as its own standalone program:

```
python games/dashboard.py   # just the dashboard
python games/pacman.py      # just Pac-Dash
python games/chess.py       # just chess
```
