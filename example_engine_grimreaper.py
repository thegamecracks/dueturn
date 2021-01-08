import time

from src import textio
from src import engine as dueturn
from src.engine import fighter_ai
from src.textio import input_boolean
from src.utility import list_copy


def main():
    # Load list of moves
    moveList = dueturn.json_handler.load(
        'src/engine/data/moves.json', encoding='utf-8')

    player_stats = dueturn.fighter_stats.create_default_stats(
        hp=(300, 300, 10),
        st=(200, 200, 10),
        mp=(200, 200, 10)
    )
    player_fighter = dueturn.Fighter(
        name='{Fgreen}Ned{RA}',
        battle_env=None,  # Set this when its needed
        stats=player_stats,
        skills=[dueturn.Skill('Acrobatics', 1),
                dueturn.Skill('Knife Handling', 2),
                dueturn.Skill('Bow Handling', 1)],
        movetypes=[dueturn.MoveType('Physical'), dueturn.MoveType('Magical')],
        # Use moves provided by game engine in sorted order
        moves=sorted(moveList, key=lambda x: x['name']),
        counters=dueturn.Fighter.all_counters.copy(),  # Give all counters
        inventory=list_copy(
            dueturn.BattleEnvironment.DEFAULT_PLAYER_SETTINGS['inventory']
        ),  # Copies the inventory from the BattleEnvironment's constants
        is_player=True,  # Gives control to user when required
        AI=None,  # The AI is only needed when is_player is False
        interface_shell_dict=None  # Auto-generates data for the battle interface
    )

    boss_moves = [
        dueturn.noneMove,
        dueturn.Move({
            'name': 'Grim Strike',
            'movetypes': ([dueturn.MoveType('Physical')],),
            'description': 'A downwards strike with the Scythe.',
            'moveMessage': """\
{sender}{FLred} strikes down {target}{FLred} with the Scythe \
for {-hpValue} damage!""",
            'hpValue': dueturn.Bound(-100, -200),
            'stCost': dueturn.Bound(-1000, -4000),
            'speed': 0,
            'blockChance': 0,
            'blockFailHPValue': dueturn.Bound(-120, -220),
            'blockFailMessage': """\
{target}{FLred} fails to block {sender}{FLred}'s Grim Strike, \
dealing {-hpValue} damage!""",
            'evadeChance': 0,
            'evadeFailHPValue': dueturn.Bound(-140, -240),
            'evadeFailMessage': """\
{target}{FLred} fails to evade {sender}{FLred}'s Grim Strike, \
dealing {-hpValue} damage!""",
            'criticalChance': 0,
            'failureChance': 0,
            }
        )
    ]
    boss_stats = dueturn.fighter_stats.create_default_stats(
        hp=(432000, 450000, 50),
        st=(42000, 42000, 814),
        mp=(96000, 96000, 312)
    )
    boss = dueturn.Fighter(
        battle_env=None,  # Set this when its needed
        name='{FLred}The Grim Reaper{RA}',
        stats=boss_stats,
        movetypes=[dueturn.MoveType('Physical')],
        moves=boss_moves,
        counters=dueturn.Fighter.all_counters.copy(),
        AI=fighter_ai.FighterAIGeneric(),
        interface_shell_dict=False
    )

    if input_boolean(
            'Do you want to fight the final boss? ',
            false=('no', 'n')):
        # Turn default color to red
        textio.update_colorama_reset('{Snorma}{Fred}{Bblack}', auto_reset=True)
        dueturn.print_color(
            'So you have chosen death,', f'{player_fighter}...')
        time.sleep(1.5)

        with dueturn.BattleEnvironment(
                    # Automatically set and reset the fighters' battle_env
                    fighters=[player_fighter, boss],
                    random_player_names=None,  # No random names will be used
                    base_values_multiplier_percent=300  # Triple damage
                ) as battle:
            battle.begin_battle(player_fighter, boss,
                                autoplay=True, return_end_message=False)
            time.sleep(1.5)
            if player_fighter.hp > 0:
                dueturn.print_color('{FLgree}You have lost- wait you won ',
                                    end=dueturn.ColoramaCodes.RESET_ALL)
            else:
                dueturn.print_color('{FLred}You have lost. ',
                                    end=dueturn.ColoramaCodes.RESET_ALL)
            input()
    else:
        print(f"{player_fighter}: Yeah I ain't fighting that")
        time.sleep(1.5)


if __name__ == '__main__':
    main()
