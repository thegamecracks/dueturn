from .missile_evasion import missile_evasion
from src import engine
from src.engine.battle_env import Autoplay


def begin_jet_battle(a, a_evading, b, b_evading):
    with engine.BattleEnvironment(fighters=(a, b)) as battle:
        def step_battle(results=None):
            results = {} if results is None else results
            return battle.begin_battle(
                a, b, stop_after_move=True, autoplay=Autoplay.SLEEP,
                **results
            )

        results = step_battle()
        while isinstance(results, dict):
            move_result = results.pop('move_result')
            if move_result is None:
                # Move failed due to unsatisfied requirements
                results = step_battle(results)
                continue

            sender = move_result['sender']
            move, costs = move_result['move'], move_result['costs']

            target = b if sender == a else a

            target.print_move(sender, move, None, costs, 'fastMessage')

            missile_type = move.values.get('missile_type')

            if missile_type is not None:
                # Fighter used a missile; go into missile evasion
                if target == a:
                    evader = a_evading
                    side = 'left'
                else:
                    evader = b_evading
                    side = 'right'
                value = missile_evasion(evader, move, side)
                target.hp += value

            results = step_battle(results)
