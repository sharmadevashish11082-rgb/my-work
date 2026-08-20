"""Headless smoke test for the Freebuff Arcade.

Boots the launcher and every game with the SDL dummy video driver, runs
simulated frames with synthetic keyboard/mouse input, and asserts nothing
crashes. Run with:

    python test_games.py
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from games.engine import App  # noqa: E402
from games.launcher import Launcher  # noqa: E402
from games.dashboard import Dashboard  # noqa: E402
from games import GAME_CLASSES  # noqa: E402

FRAMES = 120
DT = 1 / 60

MOVES = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
         pygame.K_SPACE, pygame.K_j, pygame.K_e, pygame.K_1, pygame.K_2,
         pygame.K_RETURN, pygame.K_x, pygame.K_w, pygame.K_s, pygame.K_a,
         pygame.K_d, pygame.K_u, pygame.K_r]


def key_event(etype, key):
    return pygame.event.Event(etype, key=key)


def run_frames(app, game, frames=FRAMES):
    for i in range(frames):
        if i % 5 == 0:
            key = MOVES[(i // 5) % len(MOVES)]
            game.handle_event(key_event(pygame.KEYDOWN, key))
            game.handle_event(key_event(pygame.KEYUP, key))
        if i % 17 == 0:
            game.handle_event(pygame.event.Event(
                pygame.MOUSEMOTION, pos=(200 + i % 300, 100 + i % 200)))
            game.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=(200 + i % 300, 100 + i % 200)))
            game.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONUP, button=1, pos=(200 + i % 300, 100 + i % 200)))
        game.update(DT)
        game.draw(app.screen)


def test_menu(app, menu_cls, name, key_seq):
    app.set_game(menu_cls(app))
    run_frames(app, app.game, frames=60)
    for key in key_seq:
        app.game.handle_event(key_event(pygame.KEYDOWN, key))
    app.game.handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(30, 30)))
    app.game.update(DT)
    app.game.draw(app.screen)
    assert app.game is not app.menu_cls, f"{name} failed to launch a game"
    app.quit_to_menu()
    print(f"{name}: OK")


def test_launcher(app):
    test_menu(app, Launcher, "launcher", [pygame.K_DOWN, pygame.K_RIGHT,
                                          pygame.K_RETURN])


def test_dashboard(app):
    test_menu(app, Dashboard, "dashboard", [pygame.K_TAB, pygame.K_DOWN,
                                            pygame.K_RETURN])


def test_game(app, cls):
    game = cls(app)
    app.set_game(game)
    run_frames(app, game)
    # exercise the pause / game-over menu path if one is open
    if getattr(game, "menu", None) is not None:
        for _ in range(3):
            game.handle_event(key_event(pygame.KEYDOWN, pygame.K_DOWN))
            game.handle_event(key_event(pygame.KEYDOWN, pygame.K_RETURN))
            game.update(DT)
            game.draw(app.screen)
    app.quit_to_menu()
    print(f"{cls.name}: OK")


def main():
    app = App(Dashboard)
    try:
        test_launcher(app)
        test_dashboard(app)
        for cls in GAME_CLASSES:
            test_game(app, cls)
        print(f"\nAll {len(GAME_CLASSES)} games passed the smoke test.")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
