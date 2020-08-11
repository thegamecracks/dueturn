import collections
import pprint
import random

from .booldetailed import BoolDetailed
from .bound import Bound
from .move import Move
from src import logs  # Creating logs
from src.ai import goapy
from src.utility import custom_divide, dict_copy

logger = logs.get_logger()


class FighterAIGeneric:
    """Base Fighter AI.

    Methods used by Fighter:
        analyseMove(self, user, target):
            Called when the user needs to decide what move to use
            during user.move().
            Should return a Move object, whether it can be successfully
            used by the user or not.
        analyseMoveCounter(self, user, move, sender=None):
            Called when the Fighter needs to decide what counter to use
            during user.move_receive().
            Should return a counter within user.counters.
        analyse_move_receive(self, user, move, sender=None, info=None):
            Called when the Fighter has received a move.
            This method does not need to return anything; it is only
            required if you want your AI to consider details about
            the opponent's attacks.

    Args:
        state: The current AI's state.
            Utility is similar to a Finite State Machine.
            Typically a string but can be any data type.
        data (Optional[dict]): A dictionary for storing any values either
            as settings, for caching, or for calculations
            in other functions. If None, will use DEFAULT_DATA.

    """

    DEFAULT_DATA = {
        'hpValueBias': 1,  # Utilized for weighted value calculations
        'stValueBias': 1,
        'mpValueBias': 1,
        'counterSelectionMargin': 5,  # Determines selection of best counters
        'counterWeightData': {},

        'lastTargetMove': Move({'name': 'None'})
    }

    def __init__(self, state=None, data=None):
        logger.debug(f'Initialized AI: {self.__class__.__name__}')

        if state is None:
            self.state = ''
        else:
            self.state = state

        self.data = dict_copy(self.DEFAULT_DATA)
        if data is not None:
            self.data.update(data)

    def __repr__(self):
        return (
                '{}(state={state!r}, data={data!r})'
        ).format(
            self.__class__.__name__,
            state=self.state,
            data=self.data
        )

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def moveCostAverage(move, stat):
        """Get a stat cost from a move and call it's average attribute
        if provided, then return the cost."""
        cost = move.values.get(f'{stat}Cost')
        if cost is not None:
            if hasattr(cost, 'average'):
                return cost.average()
            return cost
        return 0

    @classmethod
    def analyseMoveCostBoolean(cls, user, move, stats=None):
        """Return True if a user has enough stat to use a move.

        Args:
            user (Fighter): The Fighter using the move.
            move (Move): The move to analyse.
            stats (Iterable[str]): A set of stats to check.
                If None, defaults to user.stats.

        """
        if stats is None:
            stats = user.stats
        # For each stat
        for stat in stats:
            cost = cls.moveCostAverage(move, stat)
            stat_value = getattr(user, stat)
            # NOTE: For Bound, if the maximum bound exceeds the amount of
            # stat that the user has, it is possible that the generated
            # cost could be insufficient. However, this method
            # only considers the average cost.
            if stat_value + cost > 0:
                continue
            else:
                return False

        # All stats can be paid for, return True
        return True

    @classmethod
    def analyseMoveCostValue(cls, user, move, stats=None):
        """Return a number based on the user and cost, using an algorithm.
user - The Fighter using the move.
move - The move to analyse.
stats - An iterable of stats to check. If None, defaults to user.stats."""
        if stats is None:
            stats = user.stats

        totalCost = 0

        for stat in stats:
            if f'{stat}Cost' in move:
                # In case a move explictly states a cost of 0:
                # If the stat's cost is 0, skip calculations
                if move[f'{stat}Cost'] == 0:
                    continue
                # If move is impossible to use
                if getattr(user, f'user.{stat}_bound').upper == 0:
                    return False

                # Cost starts at average move stat cost to stat ratio
                cost = custom_divide(
                    -cls.moveCostAverage(move, stat), eval(f'user.{stat}'),
                    True, -cls.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to stat_max percent ratio
                cost *= custom_divide(
                    eval(f'user.{stat}') * 100,
                    getattr(user, f'user.{stat}_bound').upper,
                    True, -cls.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to rate ratio
                cost *= custom_divide(
                    eval(f'user.{stat}'), eval(f'user.{stat}_rate'),
                    True, -cls.moveCostAverage(move, stat) * 2)

                totalCost += cost

        logger.debug(
            f'Returned non-weighted cost of {move} at {cost}')
        return totalCost

    def analyseMoveCostValueWeighted(self, user, move, stats=None):
        """Return a number based on the user, algorithmic cost, and affect
the total by the calculated weight of each cost.
user - The Fighter using the move.
move - The move to analyse.
stats - An iterable of stats to check. If None, defaults to user.stats."""
        if stats is None:
            stats = user.stats

        totalCost = 0

        for stat in stats:
            if f'{stat}Cost' in move:
                # If the move explictly states a cost of 0, skip calculations
                if move[f'{stat}Cost'] == 0:
                    continue
                # If user cannot ever pay for the stat, return False
                if isinstance(move[f'{stat}Cost'], Bound):
                    if (
                            (stat_max := getattr(
                                user, f'user.{stat}_bound').upper)
                            < move[f'{stat}Cost'].lower
                            ):
                        logger.debug(f"""\
Returned False for {stat} in {move};
user maximum {stat} is {stat_max}, and minimum move cost \
({move[f'{stat}Cost'].__class__.__name__}) is move[f'{stat}Cost'].lower""")
                        return False
                elif stat_max < move[f'{stat}Cost']:
                    logger.debug(f"""\
Returned False for {stat} in {move};
user maximum {stat} is {stat_max}, and minimum move cost \
({move[f'{stat}Cost'].__class__.__name__}) is move[f'{stat}Cost']""")
                    return False

                # Cost starts at average move stat cost to stat ratio
                # If the result is 0, use 100 times the average cost
                cost = custom_divide(
                    -self.moveCostAverage(move, stat), eval(f'user.{stat}'),
                    failValue=-self.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat * 100 to statMax percent ratio
                # If the result is 0, multiply instead
                # by 100 times the average cost
                cost *= custom_divide(
                    eval(f'user.{stat}') * 100, eval(f'user.{stat}Max'),
                    failValue=-self.moveCostAverage(move, stat) * 100)
                # Multiply cost by stat to rate ratio porportional to
                # the amount of stat used
                # If the result is 0, multiply instead
                # by 2 times the average cost
                cost *= custom_divide(
                    eval(f'user.{stat}'), eval(f'user.{stat}Rate'),
                    failValue=(
                        -self.moveCostAverage(move, stat) * 2
                        * (
                            1 - eval(f'user.{stat}')
                            / eval(f'user.{stat}Max')
                        )
                    )
                ) + 1

                logger.debug(
                    f'Calculated non-weighted {stat} cost of {move} at {cost}')

                # Multiply cost by weight
                cost *= self.analyseValueWeighted(user, cost, stat)

                totalCost += cost

        logger.debug(f'Returned weighted total cost of {move} at {totalCost}')
        return totalCost

    @classmethod
    def analyseLowestCostingMove(cls, user, moves=None):
        """Analyses and determines the cheapest move to use."""
        if moves is None:
            moves = user.available_moves()
        move = cls.returnNoneMove(user)
        cost = None
        for m in moves:
            mCost = cls.analyseMoveCostValue(user, m)
            if mCost is False:
                # False = Unusable
                continue
            # Else if there is no move/cost, replace with new move
            # Should trigger only at the start
            if move['name'] == 'None' or cost is None:
                move, cost = m, int(mCost)
            # If current move cost is lower than current move cost
            elif mCost < cost:
                move, cost = m, int(mCost)

        return move

    @classmethod
    def noMove(cls, user):
        move = user.find_move({'name': 'None'})
        if isinstance(move, Move):
            return move
        else:
            return BoolDetailed(
                False, 'NoneNotAvailable', f'{user} has no None move')

    def analyseLowestCostingMoveWeighted(self, user, moves=None):
        """Analyses and determines the cheapest move to use with AI weights."""
        if moves is None:
            moves = user.available_moves()
        move = self.returnNoneMove(user)
        cost = None
        for m in moves:
            mCost = self.analyseMoveCostValueWeighted(user, m)
            if mCost is False:
                # False means move is unusable for the user
                continue
            # Else if there is no move/cost, replace with new move
            # Should trigger only for the first accepted move
            if move['name'] == 'None' or cost is None:
                move, cost = m, int(mCost)
            # If current move cost is lower than current move cost
            elif mCost < cost:
                move, cost = m, int(mCost)

        return move

    @classmethod
    def returnNoneMove(cls, user):
        """Returns the None move if available or otherwise a random move."""
        move = cls.noMove(user)
        if isinstance(move, Move):
            return move
        else:
            return random.choice(user.available_moves())

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        moves = user.available_moves()

        # Randomly choose a move and test if it's likely to work
        if len(moves) == 0:
            # No moves to use
            return self.returnNoneMove(user)
        for _ in range(10):
            # If no moves left from popping, trigger for-else statement
            if (len_moves_forloop := len(moves)) == 0:
                continue
            move = moves.pop(random.randint(0, len_moves_forloop - 1))
            # Skip None move
            if move['name'] == 'None':
                continue
            # Use move if possible
            if self.analyseMoveCostBoolean(user, move):
                logger.debug(f'{self} randomly picked {move}')
                break
            continue
        else:
            # Finding lowest costing move should be a last resort
            # Lowest costing move is typically the weakest, and if it's
            # possible to use a stronger attack, that should be used
            move = self.analyseLowestCostingMoveWeighted(user, moves)

            # If move is still unlikely to work (<50% average cost), do nothing
            if move is not None:
                if not self.analyseMoveCostBoolean(user, move):
                    move = self.returnNoneMove(user)

        return move

    def avgMoveValuesWeighted(self, user, move, key_format):
        """Calculates the average value for each stat in a set of key values
found by move.average_values(keySubstring), scales them by the internal
AI data values, and returns the sum.
Variables provided for key_format:
    stat - The current stat being iterated through
Example usage: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')"""
        total = 0
        for stat in user.stats:
            key = eval("f'''" + key_format + "'''")
            if key in move:
                # Obtain value, and get average if it is a Bound
                value = move[key]
                if isinstance(value, Bound):
                    value = value.average()
                total += value * self.data.get(f'{stat}ValueBias', 1)

        return total

    def analyseValueWeighted(self, user, value, stat):
        # FIXME: This documentation needs to be clarified.
        """Calculates the average value a stat in a set of key values
        found by move.average_values(keySubstring), scales them by the internal
        AI data values modified by an algorithm, and returns the value.

        Args:
            user (Fighter): The user whom the value is being applied to.
            value (int): The stat value.
            stat (str): The int_short name of the stat.

        """
        if stat == 'hp':
            hp, hp_max = user.hp, user.hp_bound.upper
            hpRatio = (1 - hp / hp_max) * 100
            # Ratio Graph
            # 25.6                #
            #                    #
            #                   #
            #                  #
            #                 #
            #               #
            #            #
            #       #
            #1# # # # # # # # # # # max - stat
            weight = custom_divide(10, hp_max * (hpRatio / 25) ** 4) + 1
            weight *= self.data.get(f'{stat}ValueBias', 1)
            logger.debug(
                f"{value} is of stat 'hp', multiplying by {weight:05f}")

            newValue = value * weight
        else:
            stat_value = getattr(user, stat)
            stat_max = getattr(user, f'{stat}_bound').upper
            ratio = (1 - stat_value / stat_max) * 100
            # Ratio Graph
            # 4.85                #
            #                    #
            #                   #
            #                 #
            #               #
            #             #
            #          #
            #     #
            #1# # # # # # # # # # # max - stat
            weight = custom_divide(10, stat_max * (ratio / 25) ** 2.8) + 1
            weight *= self.data.get(f'{stat}ValueBias', 1)
            logger.debug(
                f"Multiplying {stat_value}{stat.upper()} by {weight:05f}")

            newValue = value * weight

        logger.debug(
            f'Analysed value {value} of stat {stat!r} '
            f'for {user.name_decolored}, returning {newValue}')
        return newValue

    def analyseMoveValuesWeighted(self, user, move, key_format):
        """Calculates the average value for each stat in a set of key values
        found by move.average_values(keySubstring), scales them by the internal
        AI data values modified by an algorithm, and returns the sum.

        key_format will be formated with:
            stat: Each of the user's stats.

        Example: AIobj.averageMoveValuesWeighted(user, move, '{stat}Value')

        """
        total = 0
        for stat in user.stats:
            key = eval("f'''" + key_format + "'''")
            if key in move:
                # Obtain value, and get average if it is a Bound
                value = move[key]
                if isinstance(value, Bound):
                    value = value.average()
                total += self.analyseValueWeighted(user, value, stat)

        logger.debug(
            f'Analysed weighted values for {user.name_decolored} '
            f'against "{move}", returning a total of {total}')
        return total

    def analyseCounter(self, user, move):
        """Select a user counter by weighing each counter based on the move's
data. Any counter weights within the highest weight by a margin of
self.data['counterSelctionMargin'] will be a potential counter.
Currently considers:
    Average normal values (not countered)
    Chance of counter succeeding
    Average counter values
    Average failed counter values
    Average failed critical counter values
        Chance of critical
    Internal data"""
        logger.debug(f'{self}: Analysing counter for '
                     f'{user.name_decolored} against "{move}".')

        # Generate counter from previous calculated weights if available
        if id(move) in self.data['counterWeightData']:
            data = self.data['counterWeightData'][id(move)]
            # counters = data  # for reusing data in calculations
            # If data is a tuple of counters and weights, parse and return
            # biased choice
            if isinstance(data, dict):
                counterSelection = list(data.keys())
                counterWeights = list(data.values())
                randomCounter = random.choices(
                    population=counterSelection,
                    weights=counterWeights,
                    k=1)[0]
                logger.debug(f"""{self} has previous data on {move},
with counters {counterSelection} and respective weights {counterWeights}.
Picked counter {randomCounter!r}""")
                return randomCounter
            else:
                logger.debug(
                    f'{self} has previous data on {move}, using {data!r}')
                return data
        # Create score for all counters
        else:
            counters = collections.OrderedDict({
                counter: 0 for counter in user.counters if counter != 'none'})

        normalDamage = self.analyseMoveValuesWeighted(
            user, move, '{stat}Value')
        criticalDamage = self.analyseMoveValuesWeighted(
            user, move, 'critical{stat.upper()}Value')

        logger.debug(
            f'Normal Damage: {normalDamage}, '
            f'Critical Damage: {criticalDamage}')

        totals = dict.fromkeys(
            ['cCritChance', 'cChance', 'cDamage', 'cFailDamage',
             'cFailCritDamage', 'c_damage_reduction', 'c_fail', 'c_fail_crit'],
            0)
        for counter in counters:
            criticalChance = move.values['criticalChance']
            counterChance = move.values.get(f'{counter}Chance', 0)
            counterDamage = self.analyseMoveValuesWeighted(
                user, move, counter + '{stat.upper()}Value')
            counterFailDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'Fail{stat.upper()}Value')
            counterFailCritDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'FailCritical{stat.upper()}Value')

            # Generate damage reduction for use in totals and avg
            counter_damage_reduction = -(normalDamage - counterDamage)
            # Increase confidence of using counters when low on health
            counter_damage_reduction *= custom_divide(
                user.hp_bound.upper - user.hp, 25)
            # Decrease score if the the counter has high negative
            # consequences for failing, porportional to the chance of
            # the move failing
            counter_fail_consequences = (
                - abs(counterFailDamage - counterDamage)
                * (100 - counterChance)
                / 100
            )
            counters[counter] += counter_fail_consequences
            # Decrease score if the the counter has high negative
            # consequences for failing with critical, porportional to
            # the chance of the move failing and the chance of critical
            counter_fail_crit_consequences = (
                - abs(counterFailCritDamage - counterDamage)
                * (100 - counterChance)
                * criticalChance
                / 10000
            )
            counters[counter] += counter_fail_crit_consequences

            logger.debug(
                f'{counter}: '
                f'Counter Damage: {counterDamage}, '
                f'Counter Fail Damage: {counterFailDamage}'
            )

            totals['cChance'] += counterChance
            totals['cCritChance'] += criticalChance
            totals['cDamage'] += counterDamage
            totals['cFailDamage'] += counterFailDamage
            totals['cFailCritDamage'] += counterFailCritDamage
            totals['c_damage_reduction'] += counter_damage_reduction
            totals['c_fail'] += counter_fail_consequences
            totals['c_fail_crit'] += counter_fail_crit_consequences

        logger.debug(f'Total values:\n{pprint.pformat(totals)}')

        len_counters = len(counters)
        avg = {k: v / len_counters
               for k, v in totals.items()}

        logger.debug(f'Average values:\n{pprint.pformat(avg)}')

        for counter in counters:
            criticalChance = move.values['criticalChance']
            counterChance = move.values.get(f'{counter}Chance', 0)
            counterDamage = self.analyseMoveValuesWeighted(
                user, move, counter + '{stat.upper()}Value')
            counterFailDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'Fail{stat.upper()}Value')
            counterFailCritDamage = self.analyseMoveValuesWeighted(
                user, move, counter + 'FailCritical{stat.upper()}Value')

            # Increase score by average damage reduction relative to
            # other counters, porportional to the chance of failing and
            # porportional to the difference between its own chance
            # and exclusive average counter chance
            average_damage_exclusive = \
                custom_divide(
                    totals['cDamage'] - counterDamage,
                    len_counters - 1
                )
            average_chance_exclusive = custom_divide(
                totals['cChance'] - counterChance,
                len_counters - 1
            ) / 100
            # Relative to other counters
            average_damage_reduction = -(
                average_damage_exclusive - counterDamage)
            # Porportional to the chance of failing that is porportional
            # to the other counter chances
            chance_porportional = (100 - counterChance) / 100
            chance_porportional *= (
                average_chance_exclusive
                - (100 - counterChance)
                / 100
            )
            average_damage_reduction *= chance_porportional
            counters[counter] += average_damage_reduction

        if 'none' in user.counters:
            counters['none'] = 0
            counters.move_to_end('none', last=False)
            counters['none'] -= avg['c_damage_reduction']
            # Decrease score if not countering has high negative consequences
            # for failing, porportional to the chance of critical and
            # porportional to other counter chances
            none_fail_crit_consequences = (
                - abs(criticalDamage - normalDamage)
                * move['criticalChance'] / 100
                * (100 - avg['cCritChance']) / 100
            )
            counters['none'] += none_fail_crit_consequences

        # Get the counter with the highest score
        bestCounter = max(
            [(k, v) for k, v in counters.items()],
            key=lambda x: x[1])
        # Randomly choose a counter within acceptable margins, weighted
        # by their scores
        counterSelection = [
            k for k, v in counters.items()
            if bestCounter[1] - v <= self.data['counterSelectionMargin']]
        # If only one counter is selected, return it
        if len(counterSelection) == 1:
            counterSelection = counterSelection[0]
            logger.debug(
                f"""{self} determined that {bestCounter[0]!r} is the \
best counter for "{move}" (margin={self.data['counterSelectionMargin']}).
Calculated scores:
{pprint.pformat(dict(counters))}""")
            # self.data['counterWeightData'][id(move)] = counterSelection
            return counterSelection

        counterWeights = [counters[k] for k in counterSelection]
        counterWeights = self.make_weights_relative(counterWeights)

        # # Store counter weights
        # self.data['counterWeightData'][id(move)] = {
        #     counter: weight
        #     for counter, weight in zip(counters, counterWeights)}
        # Choose counter
        randomCounter = random.choices(
            population=counterSelection,
            weights=counterWeights,
            k=1)[0]

        debugWeight = '\n'.join(
            f'({counter!r}: {weight})'
            for counter, weight in zip(counters, counterWeights))
        logger.debug(
            f'{self} determined that {bestCounter[0]!r} is the best counter '
            f'for "{move}", and the acceptable counters are {counterSelection}'
            f" (margin={self.data['counterSelectionMargin']}).\n"
            f'Picked counter {randomCounter!r}\n'
            f'Calculated scores:\n{pprint.pformat(dict(counters))}\n'
            f'Calculated weights:{debugWeight}'
        )
        return randomCounter

    def analyse_move_receive(self, user, move, sender=None, info=None):
        """Analyses the results of a received move."""
        if 'senderFail' not in info:
            self.data['lastTargetMove'] = move

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return self.analyseCounter(user, move)

    @staticmethod
    def make_weights_relative(iterable):
        # If a weight is negative, compensate by increasing all weights
        # and making the lowest weight equal 1, required to properly make
        # relative weights
        lowestWeight = min(iterable)
        if lowestWeight <= 0:
            iterable = [
                w - lowestWeight * 2 + 1
                for w in iterable]
        # Make weights relative
        weightSum = sum(iterable)
        weights = [
            custom_divide(w, weightSum) for w in iterable]
        return weights


class FighterAIDummy(FighterAIGeneric):
    """Fighter AI - Will not attack or counter."""

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        return self.returnNoneMove(user)

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return 'none'


class FighterAIMimic(FighterAIGeneric):
    """Fighter AI - Will not attack or counter."""

    def analyseRandomMove(self, user, target):
        """Analyses and returns a random move to use."""
        moves = user.available_moves()

        # Randomly choose a move and test if it's likely to work
        if len(moves) == 0:
            # No moves to use
            return self.returnNoneMove(user)
        for _ in range(10):
            # If no moves left from popping, trigger for-else statement
            if (len_moves_forloop := len(moves)) == 0:
                continue
            move = moves.pop(random.randint(0, len_moves_forloop - 1))
            # Use move if possible
            if self.analyseMoveCostBoolean(user, move):
                logger.debug(f'{self} randomly picked {move}')
                break
            continue
        else:
            # Finding lowest costing move should be a last resort
            # Lowest costing move is typically the weakest, and if it's
            # possible to use a stronger attack, that should be used
            move = self.analyseLowestCostingMoveWeighted(user, moves)

            # If move is still unlikely to work (<50% average cost), do nothing
            if move is not None:
                if not self.analyseMoveCostBoolean(user, move):
                    move = self.returnNoneMove(user)

        return move

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        move = self.data['lastTargetMove']

        if move['name'] == 'None':
            # Target didn't move; pick a random move
            return self.analyseRandomMove(user, target)
        elif move not in (moves := user.available_moves()):
            # Move is not available; pick a random move
            return self.analyseRandomMove(user, target)
        elif not self.analyseMoveCostBoolean(user, move):
            # Move is unlikely to work; pick a random move
            return self.analyseRandomMove(user, target)
        else:
            # Reuse the target's move
            return move


class FighterAISwordFirst(FighterAIGeneric):
    """Fighter AI - Uses the dominant strategy found in the early stages of
development."""

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        # Fire Ball as a panic attack
        moveFireBall = user.find_move({'name': 'Fire Ball'}, raiseIfFail=True)
        costFireBall = int(
            moveFireBall['mpCost'].upper
            * user.battle_env.base_energies_cost_multiplier_percent
            * user.battle_env.base_energy_cost_mana_multiplier_percent
            / 10000)
        if user.hp <= 10 and user.mp >= -costFireBall and target.hp >= 20:
            return moveFireBall
        # Jab to finish off target if very low
        else:
            moveJab = user.find_move({'name': 'Jab'}, raiseIfFail=True)
            costJab = int(
                moveJab['stCost'].average()
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if target.hp <= 10 and user.st >= -costJab:
            return moveJab
        # Use sword if more than enough stamina available
        else:
            moveSword = user.find_move({'name': 'Sword'}, raiseIfFail=True)
            costSword = int(
                moveSword['stCost'].upper
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if user.st >= -costSword:
            return moveSword
        # Use Kick as medium attack
        else:
            moveKick = user.find_move({'name': 'Kick'}, raiseIfFail=True)
            costKick = int(
                moveKick['stCost'].average()
                * user.battle_env.base_energies_cost_multiplier_percent
                * user.battle_env.base_energy_cost_stamina_multiplier_percent
                / 10000)
        if user.st >= -costKick:
            return moveKick
        # Fire Ball to finish off target if low
        elif target.hp <= 20 and user.mp >= -costFireBall:
            return moveFireBall
        # Jab as last resort if possible
        elif user.st >= -costJab:
            return moveJab
        # Do nothing
        elif user.mp >= costFireBall:
            return moveFireBall
        else:
            return self.returnNoneMove(user)


class FighterAIFootsies(FighterAIGeneric):
    """Fighter AI - Designed for fighting in the Footsies gamemode."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        brain = goapy.Planner(
            'target_can_attack',
            'target_has_died',
            'has_energy',
            'low_on_health'
        )
        brain.set_goal_state(
            target_can_attack=False,
            target_has_died=True,
            low_on_health=False
        )

        actions = goapy.Action_List()
        actions.add_condition(
            'attack',
            has_energy=True
        )
        actions.add_reaction(
            'attack',
            target_has_died=True
        )
        actions.add_condition(
            'get_energy',
            has_energy=False
        )
        actions.add_reaction(
            'get_energy',
            has_energy=True
        )
        actions.add_condition(
            'retreat',
            target_can_attack=True
        )
        actions.add_reaction(
            'retreat',
            target_can_attack=False
        )
        actions.add_condition(
            'heal',
            low_on_health=True
        )
        actions.add_reaction(
            'heal',
            low_on_health=False
        )
        actions.set_weight('attack', 100)
        actions.set_weight('get_energy', 15)
        actions.set_weight('retreat', 100)
        actions.set_weight('heal', 100)

        brain.set_action_list(actions)

        self.brain = brain
        self.brain_actions = actions

    @staticmethod
    def get_attacks(user):
        """Return a list of attacks that deal "hp" stat damage."""
        attacks = []

        for move in user.moves:
            value = move.values.get('hpValue')
            if value is not None:
                if hasattr(value, 'average'):
                    value = value.average()
                if value < 0:
                    attacks.append(move)

        return attacks

    def get_available_attacks(self, user):
        """Get the user's attacks that the user has enough energy for.

        The returned list will be sorted by strongest move.

        """
        attacks = self.get_attacks(user)
        usable = []
        for move in attacks:
            if self.analyseMoveCostBoolean(user, move):
                usable.append(move)

        def sort_key(move):
            # Sort moves by their damage
            # NOTE: Moves that damage will have negative value, not positive
            return self.analyseMoveValuesWeighted(user, move, '{stat}Value')

        return sorted(usable, key=sort_key)

    def analyseMove(self, user, target):
        """Analyses and determines a move to use."""
        # Provide information to brain
        attacks = self.get_available_attacks(user)

        energy_percent = int(user.st / user.st_bound.upper * 100)
        target_health_float = target.hp / target.hp_bound.upper
        target_health_scalar = 0.3 + (target_health_float * 0.7)
        attack_weight = int((100 - energy_percent)
                            * target_health_scalar // 2)
        self.brain_actions.set_weight(
            'attack', attack_weight
        )
        self.brain_actions.set_weight(
            'get_energy', attack_weight
        )

        target_attacks = self.get_available_attacks(target)
        target_can_attack = bool(target_attacks)
        target_energy_float = target.st / target.st_bound.upper
        retreat_weight = 100 - int(target_energy_float * 100) + 15
        self.brain_actions.set_weight(
            'retreat', retreat_weight
        )

        has_energy = False
        if attacks and attack_weight < retreat_weight:
            has_energy = True

        low_on_health = user.hp < user.hp_bound.upper
        health_percent = int(user.hp / user.hp_bound.upper * 100)
        heal_weight = health_percent * max(1 - target_energy_float, 0.4)
        self.brain_actions.set_weight('heal', health_percent)

        self.brain.set_start_state(
            target_can_attack=target_can_attack,
            target_has_died=False,
            has_energy=has_energy,
            low_on_health=low_on_health
        )

        # Debug: displays weights
        logger.debug(
            'attack, retreat, and heal weights: {}'.format(
                ', '.join(
                    map(str, (attack_weight, retreat_weight, heal_weight))
                )
            )
        )

        # Get action
        plan = self.brain.calculate()
        action = plan[0]['name'] if plan else None

        # Debug: displays the calculated path and the costs
        debug_msg = []
        for a in plan:
            debug_msg.append(f"{a['name']}: {a['g']}")
        debug_msg = '\n'.join(debug_msg)
        logger.debug('Plan:\n{}'.format(debug_msg))

        # Execute action
        if action == 'attack':
            # Use strongest attack needed
            return attacks[0]
        elif action == 'get_energy':
            return user.find_move({'name': 'Advance'}, raiseIfFail=True)
        elif action == 'heal':
            return user.find_move({'name': 'Hold'}, raiseIfFail=True)
        elif action == 'retreat':
            return user.find_move({'name': 'Retreat'}, raiseIfFail=True)
        else:
            return self.returnNoneMove(user)
            # raise RuntimeError(
            #     f'unknown action in FighterAIFootsies: {action!r}')

    def analyseMoveCounter(self, user, move, sender=None):
        """Analyses and determines a counter to use."""
        return 'none'
