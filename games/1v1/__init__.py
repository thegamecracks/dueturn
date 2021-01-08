import random
import time

from .create_player_fighters import create_player_fighters
from .get_players import get_players_and_autoplay
from .player_defaults import player_create_default_settings
from .setup_AI import setup_AI
from .setup_gamemode import setup_gamemode
from .update_player_names import update_player_names
from src.engine import json_handler
from src.engine.battle_env import BattleEnvironment
from src import engine
from src import logs
from src.utility import exception_message, collect_and_log_garbage
from src.textio import print_color

__copyright__ = """
    Dueturn - A text-based two-player battle engine.
    Copyright (C) 2020  thegamecracks

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

logger = logs.get_logger()


def main():
    data = {
        'randomize_moves_A': (6, 8),
        'randomize_moves_B': (6, 8),
        # Union[bool, int, Tuple[int, int]] = (6, 8)
        # If 1 or greater, or a tuple of endpoints for random size,
        # pick a random set of moves for each fighter
        # (noneMove is excluded from the count as it will always be added).
        # Examples:
        #     10      # Pick at most 10 usable moves from the move set
        #     (4, 6)  # Pick at most 4-6 usable moves from the move set
        # Disable by removing this key. Setting the key's value to False
        # also works but is not recommended.
        'sort_moves': True,
        # Sort the fighters' move set before
        # starting the battle.
        # Disable by removing this key.
    }

    logger.debug('Reading src/engine/data/moves.json')
    moveList = json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

    try:
        logger.info('Starting game loop')

        while True:
            with BattleEnvironment(data=data) as battle:
                # Gamemode and AI setup
                gamemode = setup_gamemode(battle)
                setup_AI(battle, gamemode)

                # User Setup
                firstPlayer, secondPlayer, autoplay = \
                    get_players_and_autoplay()

                # Generate Settings
                firstPlayerSettings, secondPlayerSettings = \
                    player_create_default_settings(battle)

                # Add player names
                update_player_names(
                    firstPlayerSettings, secondPlayerSettings,
                    firstPlayer, secondPlayer,
                    {
                        'abc', 'def', 'ghi', 'ned', 'led', 'med', 'red',
                        'ked', 'sed', 'ped', 'ben'
                    }
                )

                # Create the Fighters
                firstPlayer, secondPlayer = create_player_fighters(
                    battle, firstPlayerSettings, secondPlayerSettings,
                    firstPlayer, secondPlayer
                )

                # Post-fighter creation settings
                def sample_moves(fighter, amount):
                    """Randomize a fighter's moves by removing some from their
                    move set."""
                    if isinstance(amount, tuple):
                        # Range given; pick a random amount
                        # between the range
                        amount = random.randint(*amount)

                    moves = [engine.noneMove]  # Always have noneMove

                    # Filter out only moves that the fighter can use
                    moveListFilter = [
                        m for m in moveList
                        if fighter.available_move(m)
                        and m['name'] != 'None'
                    ]

                    # Sample some of the moves
                    moves += random.sample(
                        moveListFilter,
                        min(len(moveListFilter), amount))

                    # Finalize the moves onto the fighter
                    fighter.moves = moves

                # Randomization of moves
                randomize_moves_A = battle.data.get('randomize_moves_A')
                randomize_moves_B = battle.data.get('randomize_moves_B')
                if randomize_moves_A:
                    sample_moves(firstPlayer, randomize_moves_A)
                if randomize_moves_B:
                    sample_moves(secondPlayer, randomize_moves_B)

                # If enabled, sort moves from each fighter by name
                if 'sort_moves' in battle.data:
                    key = lambda x: x['name']
                    firstPlayer.moves = sorted(
                        firstPlayer.moves, key=key)
                    secondPlayer.moves = sorted(
                        secondPlayer.moves, key=key)

                # Fight
                end_message = battle.begin_battle(
                    firstPlayer, secondPlayer, autoplay=autoplay)
                battle.print_end_message(end_message)

            # Wait for player to start another game
            input()
            print()
    except Exception:
        msg = exception_message(
            header='RUNTIME ERROR', log_handler=logger)
        msg += '\n\nSee the log for more details.'

        # Print message in red
        print_color('{RA}{FLred}', end='')
        print_color(msg, do_not_format=True)
        time.sleep(2)
        input()

        logger.info('Restarting game loop')
    except SystemExit:
        logger.info('SysExit')
    finally:
        collect_and_log_garbage(logger)
        logger.info('Ending game loop')


if __name__ == '__main__':
    while True:
        main()
