import functools

from src import engine
from src import sequencer
from src import settings


def select_game():
    games = {
        '1v1': 'src.engine',
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
