import functools

from src.engine.battle_env import Autoplay
from src.textio import (
    ColoramaCodes, input_boolean, input_loop_if_equals, print_color
)


def get_players_and_autoplay():
    """Prompt the user for the players and autoplay mode.

    Returns:
        Tuple[Union[False, str], Union[False, str], bool]:
            firstPlayer, secondPlayer, and autoplay:
            firstPlayer and secondPlayer will either be
            their names, or False for AI.
            autoplay indicates the autoplay mode begin_battle should use.

    """
    firstPlayer = None
    secondPlayer = None

    firstPlayerPrompt, secondPlayerPrompt = None, None
    autoplay = False

    # Define input functions
    def reset_color_method(s):
        print(ColoramaCodes.RESET_ALL, end='')
        return s
    print_color_without_newline = functools.partial(
        print_color, end='')
    input_boolean_color = functools.partial(
        input_boolean,
        repeat_prompt='Answer with {true} or {false}: {FLcyan}',
        false=('no', 'n'),
        apply_methods=(str.strip, str.casefold, reset_color_method),
        print_func=print_color_without_newline
    )
    input_name = functools.partial(
        input_loop_if_equals,
        repeat_prompt='Name cannot be empty: {FLcyan}',
        loop_if_equals=(''),
        apply_methods=(str.strip, str.casefold, reset_color_method),
        print_func=print_color_without_newline
    )

    # Get player options
    firstPlayerPrompt = input_boolean_color(
        'Is there a player-controlled fighter? {FLcyan}')
    if firstPlayerPrompt:
        firstPlayer = input_name('Choose your name: {FLcyan}')
        secondPlayerPrompt = input_boolean_color(
            'Is there a second player? {FLcyan}')
        if secondPlayerPrompt:
            secondPlayer = input_name('Choose your name: {FLcyan}')
    if not (firstPlayerPrompt and secondPlayerPrompt):
        if input_boolean_color('Automatically play AI turns? {FLcyan}'):
            autoplay = input_boolean_color(
                'Do you want the AI to play instantly? {FLcyan}')
            autoplay = Autoplay.INSTANT if autoplay else Autoplay.SLEEP
        else:
            autoplay = Autoplay.INPUT
    else:
        autoplay = input_boolean_color(
            'Automatically advance occurring events? {FLcyan}')
        autoplay = Autoplay.SLEEP if autoplay else Autoplay.INPUT

    return firstPlayer, secondPlayer, autoplay
