import functools

from src import engine
from src import sequencer
from src import settings

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


def select_game():
    games = {
        '1v1': 'games.1v1',
        'jet': 'games.jet',
    }

    print('Games:')
    for name in games:
        print(name.title())
    print()

    selection = input('Select a game: ').casefold().strip()

    while (selection := games.get(selection)) is None:
        selection = input('Unknown game: ').casefold().strip()

    # Return a function ready to load the main function
    # from the selected module
    return functools.partial(
        sequencer.begin_sequence_module,
        selection, 'main'
    )


def main():
    settings.setup_configs()

    while True:
        game = select_game()
        print(end='\n\n')
        game()
        print(end='\n\n')


if __name__ == '__main__':
    main()
