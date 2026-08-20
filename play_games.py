"""Freebuff Arcade — 21 Python games in one app.

Run this file to open the arcade dashboard, from which you can select and
play any game:

    python play_games.py

Requires pygame (pygame-ce). Browse the dashboard with the arrow keys or
mouse, press Enter (or the PLAY button) to launch the selected game, and
press Esc to return here from any game.
"""
from games.engine import App
from games.dashboard import Dashboard


def main():
    App(Dashboard).run()


if __name__ == "__main__":
    main()
