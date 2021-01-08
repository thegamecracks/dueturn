import time

from . import ai
from . import moves
from . import stats
from src import engine
from src import settings
from src.engine.battle_env import Autoplay
from src.textio import (print_color, print_typewriter, SLEEP_CHAR_DELAY_NORMAL)

cfg_engine = settings.load_config('engine')


def missile_evasion(evader, missile, side='left'):
    """Start a missile evasion.

    Args:
        evader (Fighter): The fighter evading the missile.
        missile (str): The move that the missile is being used from.
        side (Union["left", "right"]): The fighter's side
            to display on. The missile moves first regardless.

    """
    missile_type = missile['missile_type']
    speed = missile['missile_speed']
    field_of_regard = missile['field_of_regard']
    track_rate = missile['track_rate']
    base_damage = missile['base_damage']
    blast_radius = missile['blast_radius']

    missile_fighter = engine.Fighter(
        name='{FLmage}Missile{RA}',
        stats=stats.get_defaults(stats.missile_stats),
        moves=moves.missile_moves,
        counters={},
        AI=ai.MissileAI()
    )
    with engine.BattleEnvironment(
            fighters=(evader, missile_fighter)) as battle:
        def step_battle(results=None):
            results = {} if results is None else results
            return battle.begin_battle(
                a, b, stop_after_move=True, autoplay=Autoplay.SLEEP,
                **results
            )

        results = {'starting_turn': 2 + int(side == 'left')}

        if side == 'left':
            a, b = evader, missile_fighter
        elif side == 'right':
            a, b = missile_fighter, evader
        else:
            raise ValueError(f'Unknown side {side!r}')

        results = step_battle(results)
        while isinstance(results, dict):
            move_result = results.pop('move_result')
            if move_result is None:
                results = step_battle(results)
                continue

            sender, move = move_result['sender'], move_result['move']

            if sender == evader:
                effect = move['effect']
                if isinstance(effect, dict):
                    actual_effect = effect.get(missile_type, 0)
                else:
                    actual_effect = effect

                missile_fighter.er += actual_effect
            elif sender == missile_fighter:
                missile_fighter.di -= speed
                if missile_fighter.er < field_of_regard:
                    # Missile can still see evader
                    weight = max(
                        0,
                        min(
                            1 - missile_fighter.er / (1.5 * field_of_regard),
                            1 - (missile_fighter.er / field_of_regard) ** 10,
                        )
                    )
                    error_correction = int(track_rate * weight)

                    missile_fighter.er -= error_correction

            if missile_fighter.di == 0:
                # Detonation
                sleep = (cfg_engine.GAME_AUTOPLAY_AI_DELAY
                         / cfg_engine.GAME_DISPLAY_SPEED)

                print_color('\nThe missile makes its last adjustments!',
                            end='\n\n\n')

                time.sleep(sleep)

                print(battle.fightChartTwo(
                    a, b,
                    statLogA=results['statLogA'],
                    statLogB=results['statLogB'],
                    tabs=cfg_engine.GAME_DISPLAY_USE_TABS,
                    color_mode=cfg_engine.GAME_DISPLAY_STATS_COLOR_MODE
                ), end='\n\n\n')

                value = -int(
                    base_damage
                    * (1 - max(0, missile_fighter.er / blast_radius))
                )
                if value < 0:
                    print_typewriter(
                        '... Hit!',
                        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
                        sleep_char_specifics={'.': 0.5}
                    )
                else:
                    print_typewriter(
                        '... Miss!',
                        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
                        sleep_char_specifics={'.': 0.5}
                    )
                return value
            else:
                target = b if sender == a else a
                target.print_move(sender, move, None, None, 'fastMessage')

            results = step_battle(results)
