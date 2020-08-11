"""A rewrite of the Cave Johnson game by @TheLoneNade."""
import os
import random
import time

from src.sequencer import begin_sequence
from src.textio import (
    input_choice_typewriter, input_loop_if_equals_typewriter,
    input_number_typewriter, print_sleep_multiline, print_typewriter,
    textio_typewriter,
    SLEEP_CHAR_DELAY_NORMAL, SLEEP_CHAR_DELAY_SPECIFICS
)

player_name = '<Your Name Here>'
aep_voice_line_type = None


# ===== Scenes =====
def intro():
    """Scene 1"""
    global player_name

    print_typewriter(
        'Greetings software developer! My name is Cave Johnson, '
            'CEO of Aperture Science!',
        '',
        'I need you, yes you my friend, to make a, '
            'uh, "small" program for me.',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    # Get name and Title Case it
    player_name = input_loop_if_equals_typewriter(
        "Now my friend, what's your name? ",
        loop_if_equals={
            '': "What's that, I didn't hear you: ",
            'cave johnson': 'Yeah, no, tell me your actual name: '
        },
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics={',': 0.3}
    ).title()

    print_typewriter(
        f'Hello {player_name}, I need a program that will help me '
            'send automated voice lines to my employees.',
        '',
        'Not that I fire anyone on the daily, but on that note, '
        'I need three things from you:',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=1
    )
    sleep_char_specifics_dash = SLEEP_CHAR_DELAY_SPECIFICS.copy()
    sleep_char_specifics_dash.setdefault('-', 0.5)
    print_typewriter(
        "Number 1. Your code must be written in Python. If it isn't, "
            "I'm going to be very disappointed and your contract "
            "will be terminated - don't ask me why;",
        '',
        'Number 2. I require all of my voicelines to be used, '
            'and if there are any changes to these lines, note that I '
            'will not hesitate to deport you from this world;',
        '',
        "And Number 3. Don't be late. Last time someone was late, "
            'they had a very uh, "pleasant", surprise.',
        '',
        'Now off you go, I will send you what I require '
            'along with the mentioned voice lines in an email, '
            'now I have some firing to do, Cave Johnson out!',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=sleep_char_specifics_dash,
        sleep_line=1
    )

    return got_automated_email_program


def got_automated_email_program():
    """Scene 2"""
    print_typewriter(
        '',
        'Upon coming back from your meeting with Cave Johnson, '
            'you read his email and realize you have a full 2 months '
            'to finish his piece of software, '
            'designed to shout pre-recorded voice lines at his employees.',
        '',
        'You think to yourself that you have all the time in the world, '
            'BUT there is a problem:',
        '',
        "You don't know Python! Now, you're a lazy programmer, "
            "a good one, but don't like to put in a lot of effort.",
        '',
        'So you consider either:',
        "1. Quitting entirely, thinking it's too much of a hassle;",
        'or 2. Spend the next month learning Python',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    choice = input_choice_typewriter(
        'Pick the number for the corresponding option you wish to pick: ',
        ('1', '2'),
        reprompt="That isn't an option: ",
        sleep_char=SLEEP_CHAR_DELAY_NORMAL
    )
    if choice == '1':
        return automated_email_program__quit
    elif choice == '2':
        return automated_email_program__learn_python


def automated_email_program__quit():
    """Scene 2-FailQuit"""
    print_typewriter(
        'You decide to quit, disappointing all of Aperture Science, '
            'your dignity, and Cave Johnson himself.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL * 2,
        sleep_char_specifics={',': 0.6},
        sleep_line=1
    )


def automated_email_program__learn_python():
    """Scene 3"""
    print_typewriter(
        '',
        '',
        '',
        'You learn as much Python as you can, very good stuff,',
        "but however, you realize Mr. Johnson didn't send you "
            'his voice lines required for the program.',
        '',
        "Now in a battle against your own laziness, do you:",
        '1. Choose to quit now;',
        '2. Grab voice lines from Cave Johnson\'s game, "Portal 2";',
        'or 3. Contact him so he can send his voice lines?',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    choice = input_choice_typewriter(
        'Select an option: ',
        ('1', '2', '3'),
        reprompt="That isn't an option: ",
        sleep_char=SLEEP_CHAR_DELAY_NORMAL
    )
    if choice == '1':
        return aep__voice_lines__quit
    elif choice == '2':
        return aep__voice_lines__portal
    elif choice == '3':
        return aep__voice_lines__contact_cave


def aep__voice_lines__quit():
    """Scene 3-FailQuit"""
    print_typewriter(
        'You quit right then and there with all that time wasted.',
        'No socializing with anyone has left you alone,',
        'and the fact that you realized you ran out of orange juice '
            "not only disappoints you, but you've now disappointed "
            'all of Aperture Science and Mr. Johnson himself.',
        'Goodbye.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL * 2,
        sleep_char_specifics={',': 0.6, '.': 0.3},
        sleep_line=1
    )


def aep__voice_lines__portal():
    """Scene 3-PortalVoiceLines"""
    global aep_voice_line_type
    aep_voice_line_type = 'portal'
    print_typewriter(
        '',
        '',
        '',
        'Although the voice lines are weird, you manage to make it work, '
            'and now have a proper functioning "shout at your employees "'
            'because they\'re misbehaving" software.',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    time.sleep(2 / GAME_SPEED)
    return aepvl_get_error


def aep__voice_lines__contact_cave():
    """Scene 3-EmailVoiceLines"""
    global aep_voice_line_type
    aep_voice_line_type = 'email'
    print_typewriter(
        '',
        '',
        '',
        'You decide to send an email and less then a day later, '
            'you get a response with the required voice lines '
            'and start to work on your code.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    time.sleep(2 / GAME_SPEED)
    return aepvl_get_error


def aepvl_get_error():
    """Scene 4"""
    print_typewriter(
        "Oh no! Upon realizing 3 days before you're supposed to meet up "
            'with Mr. Johnson and show him your program, '
            'you realize that it has a problem!',
        'Do you: 1. Inspect the code;',
        '2. Leave it be and show it to Mr. Johnson as it is;',
        'or 3. Quit right then and there?',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    choice = input_choice_typewriter(
        'Select an option: ',
        ('1', '2', '3'),
        reprompt="That isn't an option: ",
        sleep_char=SLEEP_CHAR_DELAY_NORMAL
    )
    if choice == '1':
        # Select a random error scene
        aepvl_error = random.randint(1, 2)
        if aepvl_error == 1:
            return aepvl__error1
        elif aepvl_error == 2:
            return aepvl__error2
    elif choice == '2':
        return aepvl_get_error__show_as_is
    elif choice == '3':
        return aepvl_get_error__quit


def aepvl_get_error__quit():
    """Scene 4-FailQuit"""
    print_typewriter(
        'Realizing that not only are you lazy at your job, '
            "you can't even fix a bug, maybe being a programmer "
            "isn't a career that you want to pursue.",
        'Now not only have you lost your dignity, '
            "you've now disappointed both a whole science facility "
            'and Mr. Johnson himself.',
        'Goodbye.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL * 2,
        sleep_char_specifics={',': 0.6, '.': 0.3},
        sleep_line=1
    )


def aepvl_get_error__show_as_is():
    """Scene 4-ShowAsIs"""
    print_typewriter(
        'The day comes that you have to show Mr. Johnson your code.',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=2
    )
    print_typewriter(
        f'Well {player_name}.',
        'Now, using your code was fine,',
        'Until I started to hear voice lines from my own game,',
        'And the shouting comes from only one line!',
        "Now, it's not to say I'm disappointed, "
            "but now I'm afraid I will have to let you go.",
        sleep_char=SLEEP_CHAR_DELAY_NORMAL * 2,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=1
    )
    print_typewriter(
        'OUT!',
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL * 3,
        sleep_line=1
    )


def aepvl__error1():
    print_typewriter(
        'Upon further inspection of the code, '
            'you determine that the function that randomly picks '
            'a shout line is broken, but is still able to run.',
        '',
        'The code is as follows...',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )

    print_sleep_multiline(
        '001: """Play a random voice line."""',
        '002: import math',
        '003: import os',
        '004: import random',
        '005: ',
        '006: import pygame',
        '007: ',
        '008: cjList = [',
        '009:     "cjshout1.wav",',
        '010:     "cjshout2.wav",',
        '011:     "cjshout3.wav",',
        '012:     "cjshout4.wav",',
        '013:     "cjshout5.wav",',
        '014:     "cjREEEEE.wav",',
        '015: ]',
        '     ...',
        '060: def getDiceRoll():',
        '061:     """Use complex algorithmic decision-making to select an',
        '062:     appropriate voice line.',
        '063:     """',
        '064:     sum = 0',
        '065:     for roll in range(len(cjList)):',
        '066:         sum >= random.randint(1, 6)',
        '067:     return sum % len(cjList)',
        '     ...',
        '070: pygame.mixer.init()',
        '071: pygame.mixer.music.load(cjList[getDiceRoll()])',
        '072: pygame.mixer.music.play()',
        sleep=0.1
    )
    time.sleep(2 / GAME_SPEED)

    guesses = 6
    prompt = 'Which line has the error? '
    seems_fine_list = [
        'nothing seems wrong about it: ',
        'it seems fine: '
    ]
    seems_fine = lambda: random.choice(seems_fine_list)

    while guesses > 0:
        choice = input_number_typewriter(
            prompt,
            invalid_prompt="That's not a valid line number: ",
            low_bound=1,
            high_bound=72,
            low_bound_prompt='That line does not exist: ',
            high_bound_prompt='You know that the error is within lines 1-72: ',
            integer_only=True,
            sleep_char=SLEEP_CHAR_DELAY_NORMAL
        )
        # Correct answer
        if choice == 66:
            break
        # Responses for lines that are obscured
        elif choice > 15 and choice < 60 \
                or choice > 67 and choice < 70:
            prompt = 'You know the error is within the code shown above: '
            continue  # Does not deduct from guesses
        # Responses for specific lines
        elif choice == 1:
            prompt = "That's the program docstring, " \
                     "the problem can't be there: "
        elif choice in (2, 3, 4, 6):
            prompt = 'Those are module imports; ' \
                     f'{seems_fine()}'
        elif choice in (5, 7):
            prompt = "That's an empty line, " \
                     "the problem can't be there: "
        elif choice >= 8 and choice <= 15:
            prompt = "That's the list of sound files; " \
                     f'{seems_fine()}'
        elif choice == 60:
            prompt = "That's the function definition; " \
                     f'{seems_fine()}'
        elif choice in (61, 62, 63):
            prompt = "That's the function docstring, " \
                     "the problem can't be there: "
        elif choice == 64:
            prompt = 'That assigns 0 to "sum"; ' \
                     f'{seems_fine()}'
        elif choice == 65:
            prompt = 'That for-loop just runs the code below 6 times; ' \
                     f'{seems_fine()}'
        elif choice == 67:
            prompt = 'This should return a number to randomly pick ' \
                     f'a sound file; {seems_fine()}'
        elif choice == 70:
            prompt = 'This sets up the audio system; ' \
                     f'{seems_fine()}'
        elif choice == 71:
            prompt = 'This should pick a random sound file and load it; ' \
                     f'{seems_fine()}'
        elif choice == 72:
            prompt = 'This should play the loaded sound file, ' \
                     f'{seems_fine()}'
        guesses -= 1
    else:
        # Took too many guesses
        return aepvl_error1__does_not_know

    print_typewriter(
        'Something looks off about line 66...'
        '',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    time.sleep(1 / GAME_SPEED)

    return aepvl_error1__found_line


def aepvl_error1__found_line():
    guesses = 6
    prompt = 'That ">=", it should be something else: '
    should_add = 'but it should be adding onto sum: '

    while guesses > 0:
        choice = input_loop_if_equals_typewriter(
            prompt,
            loopPrompt='What should ">=" be replaced with: ',
            loopBreak=(),
            sleep_char=SLEEP_CHAR_DELAY_NORMAL
        )
        # Correct answer
        if choice == '+=':
            break
        # Responses for comparisons
        elif choice == '>':
            prompt = 'That means a "greater than" comparison, ' \
                     f'{should_add}'
        elif choice == '>=':
            prompt = 'That means a "greater or equal to" comparison, ' \
                     f'{should_add}'
        elif choice == '<':
            prompt = 'That means a "less than" comparison, ' \
                     f'{should_add}'
        elif choice == '<=':
            prompt = 'That means a "less or equal to" comparison, ' \
                     f'{should_add}'
        elif choice == '==':
            prompt = 'That means an "equal to" comparison, ' \
                     f'{should_add}'
        # Responses for arithmetic
        elif choice == '+':
            prompt = 'That adds the value and variable together, ' \
                     "but doesn't actually store the new value: "
        # Responses for assignments
        elif choice == '=':
            phrase = random.choice([
                "but it erases what's left over: ",
                'but I need to augment it to add onto sum: '
            ])
            prompt = 'That assigns the value to the variable ' \
                     f'{phrase}'
        elif choice == '-=':
            prompt = 'That assigns the difference to the variable, ' \
                     f'{should_add}'
        elif choice == '/=':
            prompt = 'That assigns the quotient to the variable, ' \
                     f'{should_add}'
        elif choice == '*=':
            prompt = 'That assigns the product to the variable, ' \
                     f'{should_add}'
        # Response for unknown input
        else:
            prompt = 'No, that won\'t work replacing ">=": '
        guesses -= 1
    else:
        # Took too many guesses
        return aepvl_error1__does_not_know

    print_typewriter(
        'Right, that should fix the problem!',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    time.sleep(1)
    return aepvl_error1__solved


def aepvl_error1__does_not_know():
    return aepvl_get_error__quit  # Placeholder ending


def aepvl_error1__solved():
    print('This pathway is incomplete')
    time.sleep(3)


def aepvl__error2():
    return aepvl__error1

    print('This pathway is incomplete')
    time.sleep(3)


# ===== Sequencing =====
def main(loop=True):
    global GAME_SPEED
    GAME_SPEED = input_number_typewriter(
        'Set the speed of the game (higher is faster): ',
        'That is not a valid number: ',
        low_bound=0.1,
        low_bound_prompt='Cannot be lower than 0.1: ',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL
    )

    textio_typewriter.TYPEWRITER_SPEED = GAME_SPEED

    if loop:
        while True:
            begin_sequence(intro)
            input('=====Game Ended; press Enter to restart===== ')
            os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    main()
