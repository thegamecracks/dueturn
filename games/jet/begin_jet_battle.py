from .missile_evasion import missile_evasion
from src import engine


def begin_jet_battle(a, a_evading, b, b_evading):
    results = {}
    with engine.BattleEnvironment(fighters=(a, b)) as battle:
        while True:
            results = battle.begin_battle(
                a, b, stop_after_move=True,
                autoplay=True, **results
            )

            if not isinstance(results, dict):
                # Battle probably ended in victory/loss (should be a list)
                break
            move_result = results.pop('move_result')

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
