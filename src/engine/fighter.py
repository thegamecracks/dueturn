import random
from typing import List, Optional, Tuple, Union

from . import interface
from . import util
from .booldetailed import BoolDetailed
from .bound import Bound
from .data import fighter_stats
from .move import Move
from src import logs
from src import settings
from src.textio import (  # Color I/O
    ColoramaCodes, cr, format_color, input_color, print_color
)

logger = logs.get_logger()

# Load settings
cfg_engine = settings.load_config('engine')

INDENT = '\t' if cfg_engine.GAME_DISPLAY_USE_TABS \
    else ' ' * cfg_engine.GAME_DISPLAY_TAB_LENGTH
# The standard indentation to use for printing based on game settings.


class Fighter:
    """The base Fighter class.

    Args:
        name (str): The name of the Fighter.
        battle_env (Optional[src.engine.battle_env.BattleEnvironment]):
            The BattleEnvironment that the Fighter will be fighting inside.
            This can be left as None so it can be provided after the
            creation of the Fighter.
        stats (Optional[Dict[str, Stat]]): A dictionary containing
            the Fighter's stats. If left as None, it will use
            `src.engine.data.fighter_stats.get_defaults()`.
        status_effects (Optional[List[StatusEffect]]):
            A list of `StatusEffect` that the Fighter is affected by.
            If None, defaults to an empty list.
        skills (Optional[List[Skill]]):
            A list of `Skill` that the Fighter has.
            If None, defaults to an empty list.
        moveTypes (Optional[List[MoveType]]):
            A list of `MoveType` that the Fighter has.
            If None, defaults to an empty list.
        moves (Optional[List[Move]]):
            A list of `Move` that the Fighter has.
            If None, defaults to an empty list.
        counters (Optional[Dict[str, str]]):
            A dictionary of counters that the Fighter has.
            If None, defaults to a shallow copy of Fighter.allCounters.
        inventory (Optional[List[Item]]):
            A list of `Item` that the Fighter has.
            If None, defaults to an empty list.
        isPlayer (bool): If True, provides an interface for the user to
            command the Fighter with during a battle.
            If False, uses `AI` to command the Fighter.
        AI (Optional[Any]): The AI that the Fighter uses if not `isPlayer`.
        battleShellDict (Optional[dict]): A dictionary used by the user's
            interface when battling. If None, defaults to a dictionary
            specifying to the shell that it is the user's first time.

    """
    allCounters = {  # Footnote 1
        'none': 'none',
        'block': 'block',
        'evade': 'evade'
    }

    def __init__(
            self, name: str, battle_env=None,
            stats=None,
            status_effects=None,
            skills=None,
            moveTypes=None,
            moves=None,
            counters=None,
            inventory=None,
            isPlayer=False,
            AI=None,
            battleShellDict=None):

        self.name = name

        self.battle_env = battle_env

        if stats is None: self.stats = fighter_stats.get_defaults()
        else: self.stats = stats
        # Create properties for each stat
        # See https://gist.github.com/Wilfred/49b0409c6489f1bdf5a5c98a488b31b5
        # on how to dynamically define properties
        properties = {}

        def generate_properties(int_short):
            def fget_stat(self):
                return self.stats[int_short].value

            def fset_stat(self, value):
                self.stats[int_short].value = value

            doc_stat = f'Property for "{int_short}" stat.'

            def fget_bound(self):
                return self.stats[int_short].bound

            def fset_bound(self, value):
                self.stats[int_short].bound = value

            doc_bound = f'Property for "{int_short}" stat Bound.'

            def fget_rate(self):
                return self.stats[int_short].rate

            def fset_rate(self, value):
                self.stats[int_short].rate = value

            doc_rate = f'Property for "{int_short}" stat rate of change.'

            properties[int_short] = property(
                fget_stat, fset_stat, doc=doc_stat)
            properties[int_short + '_bound'] = property(
                fget_bound, fset_bound, doc=doc_bound)
            properties[int_short + '_rate'] = property(
                fget_rate, fset_rate, doc=doc_rate)

        for int_short, stat_obj in self.stats.items():
            generate_properties(int_short)
        if len(properties):
            # Change class name to indicate that its a child class
            # class_name = self.__class__.__name__ + int_short.upper()
            child_class = type(
                self.__class__.__name__,  # class_name,
                (self.__class__,),
                properties
            )

            self.__class__ = child_class

        # Status Effects default is an empty list
        if status_effects is None: self.status_effects = []
        else: self.status_effects = status_effects

        # Skills default is an empty list
        if skills is None: self.skills = []
        else: self.skills = skills

        # Move Type default is an empty list
        if moveTypes is None: self.moveTypes = []
        else: self.moveTypes = moveTypes

        # Moves default is an empty list
        if moves is None: self.moves = []
        else: self.moves = moves

        # Counters default are all counters
        if counters is None: self.counters = self.allCounters.copy()
        else: self.counters = counters

        # Inventory default is an empty list
        if inventory is None: self.inventory = []
        else: self.inventory = inventory

        # isPlayer default is False
        self.isPlayer = isPlayer

        # AI default is FighterAIGeneric()
        # if AI is None: self.AI = FighterAIGeneric()
        # else: self.AI = AI
        self.AI = AI

        if battleShellDict is None:
            self.battleShellDict = {
                # Autorun on start of playerTurnMove Shell
                'moveCMD': ['first_time']
            }
        else:
            self.battleShellDict = battleShellDict

        logger.debug(f'Created {self!r}')

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                [
                    repr(x) for x in (
                        self.name,
                        self.stats,
                        self.skills, self.moveTypes,
                        self.moves, self.counters,
                        self.inventory, self.isPlayer
                    )
                ]
            )
        )

    def __str__(self):
        return format_color(self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self._decoloredName = format_color(name, no_color=True)

    @property
    def decoloredName(self):
        return self._decoloredName

    @decoloredName.setter
    def decoloredName(self, name):
        raise AttributeError(
            'This attribute cannot be changed directly; use self.name')

    @staticmethod
    def get_move_info_default(move):
        """Return an informational string about a move using `ALL_STAT_INFOS`.

        The description will be formatted with an environment containing:
            move: The instance of Move that the description is in.
            *ALL_STAT_INFOS: All StatInfo objects specified in
            `src/engine/data/fighter_stats.py`.
        It will also format color placeholders using `format_color()`.

        """
        namespace = fighter_stats.ALL_STAT_INFOS.copy()
        namespace['move'] = move
        return format_color(move['description'], namespace=namespace)

    def get_move_info(self, move):
        """Return an informational string about a move using a Fighter.

        The description will be formatted with an environment containing:
            move: The instance of Move that the description is in.
            *self.stats: All Stat objects the Fighter has.
        It will also format color placeholders using `format_color()`.

        """
        namespace = {k: v.value for k, v in self.stats.items()}
        namespace['move'] = move
        return format_color(move['description'], namespace=namespace)

    def updateStatusEffectsDuration(self):
        """Update all durations and remove completed status effects.

        Returns:
            list: A list of wearoff messages.

        """
        effects = self.status_effects
        messages = []
        i = 0
        while i < len(effects):
            if effects[i]['duration'] <= 0:
                if 'wearoffMessage' in effects[i]:
                    messages.append((effects[i], 'wearoffMessage'))
                del effects[i]
            else:
                effects[i]['duration'] -= 1
                i += 1

        return messages

    def applyStatusEffectsValues(self, changeRandNum=True):
        """Apply status effect values."""
        messages = []
        for effect in self.status_effects:
            for stat, stat_info in self.stats.items():
                key = f'{stat}Value'
                if key in effect and hasattr(self, stat):
                    statConstant = stat_info.int_full
                    value = Bound.call_random(effect[key])
                    value *= (
                        self.battle_env.base_values_multiplier_percent / 100
                    )
                    value *= getattr(self.battle_env,
                        f'base_value_{statConstant}_multiplier_percent'
                    ) / 100
                    if changeRandNum and isinstance(effect[key], Bound):
                        effect[key].randNum = value
                    setattr(self, stat, getattr(self, stat) + int(value))
            if 'applyMessage' in effect:
                messages.append((effect, 'applyMessage'))
        return messages

    def printStatusEffectsMessages(self, messages, printDelay=0):
        for effect, message in messages:
            self.printStatusEffect(effect, message, end=None)
            util.pause(printDelay)

    def updateStats(self, stats=None):
        """Calls self.updateStat for each stat the Fighter has."""
        if stats is None:
            stats = self.stats
        for stat in stats:
            # Update stat
            if not hasattr(self, stat):
                raise ValueError(f'No property exists for {stat} in '
                                 f'{self.decoloredName} (Stats: {stats})')
            self.updateStat(stat)

    def updateStat(self, stat):
        value = getattr(self, f'{stat}_rate')

        value *= getattr(self.battle_env, f'{stat}_rate_percent') / 100

        value *= self.battle_env.regen_rate_percent / 100

        value = round(value)

        setattr(self, stat, getattr(self, stat) + value)

    def printMove(self, sender, move, message='moveMessage'):
        """Formats a move's message and prints it.

        This method should be called by the target.

        An environment is provided to be used for formatting:
            sender: The Fighter sending the move.
            target: The Fighter receiving the move.
            move: The Move being used.
            *self.stats: The target's stats.
        There are other variables available but are not intended for use:
            cls: The Fighter class.
            message: The message that was extracted from `move`.

        """
        namespace = {k: v for k, v in self.stats.items()}
        namespace['sender'] = sender
        namespace['target'] = self
        namespace['move'] = move
        print_color(move[message], namespace=namespace)

    def printStatusEffect(self, effect, message='applyMessage', **kwargs):
        """Formats a status effect's message and prints it.

        An environment is provided to be used for formatting:
            self: The Fighter receiving the effect.
            effect: The StatusEffect being applied.
            hp, st, mp: The respective StatInfo objects.
        If the status effect has a *Value, it will be available
        for formatting.
        There are other variables available but are not intended for use:
            message: The message that was extracted from `move`.

        """
        if message in effect:
            namespace = {k: v for k, v in self.stats.items()}
            namespace['self'] = self
            namespace['effect'] = effect
            for stat in self.stats:
                value = f'{stat}Value'
                if value in effect:
                    namespace[value] = util.num(float(effect[value]))
            print_color(effect[message], namespace=namespace, **kwargs)

    @staticmethod
    def findDict(objects, values,
                 exactSearch=True, detailedFail=False):
        """Find the first matching object in a list of objects by values.

        Args:
            objects (Iterable): A list of objects to search through.
            values (dict): A dictionary of values to compare.
            exactSearch (bool): If True, match strings exactly.
                When exactSearch is True:
                    'foo' == 'foo'
                    'foo' != 'foobar'
                    'Foo' != 'foo'
                When exactSearch is False:
                    'foo' in 'foo'
                    'foo' in 'foobar'
                        'Foo'.casefold() in 'foo'.casefold()
            detailedFail (bool): If True, return a BoolDetailed
                instead of None when the search fails.

        Note: Do not pass in an iterator for `objects`;
        this function requires more than one iteration (logging message)
        and will silently fail with an iterator,
        returning no results.

        """
        logger.debug(f'Finding {values} in {[str(o) for o in objects]}')
        if len(values) == 0:
            logger.debug(f'{values} is empty, returning objects')
            return objects
        results = []
        # resultsAreExact for unexact search
        # If a search returns an exact find, dump unexact results and look
        # for any other exact matches to confirm that there is only one
        resultsAreExact = False
        for obj in objects:
            # Note: Cannot use dict().items() bitwise AND, doesn't work with
            # moves containing itemRequired or other values containing
            # a dictionary
            if exactSearch:
                for value in values.items():
                    if value not in obj.values.items():
                        logger.debug(
                            f'{obj} has no exact key-value pair {value}')
                        break  # Missing value; continue with next object
                else:
                    logger.debug(f'{obj} exactly matched {values}')
                    return obj  # Found all values; return object
            else:
                # Unexact search
                unexactMatchExists = False
                exactMatchExists = True
                for value in values.items():
                    # Do exact matching before unexact matching
                    if value in obj.values.items():
                        continue
                    else:
                        exactMatchExists = False
                    if value[0] in obj.values.keys():
                        # Do substring checking for strings
                        if isinstance(obj.values[value[0]], str):
                            if value[1].casefold() \
                                    in obj.values[value[0]].casefold():
                                unexactMatchExists = True
                            else:
                                logger.debug(f"{obj} doesn't have superstring "
                                             f"of {value}")
                                break  # Missing superstring; go to next object
                        # Do exact matching for non-string key-value pairs
                        elif value not in obj.values.items():
                            logger.debug(
                                f'{obj} has no exact key-value pair {value}')
                            break  # Missing value; continue with next object
                    else:
                        logger.debug(f'{obj} has no key-value pair {value}')
                        break  # Missing value; continue with next object
                else:
                    if exactMatchExists:
                        logger.debug(f'{obj} exactly matched {values}')
                        if not resultsAreExact:
                            results.clear()
                            resultsAreExact = True
                        results.append(obj)
                    elif unexactMatchExists and not resultsAreExact:
                        logger.debug(
                            f'{obj} unexactly matched {values}')
                        results.append(obj)
                    elif unexactMatchExists and resultsAreExact:
                        logger.debug(
                            f'{obj} unexactly matched {values} but already '
                            'found an exact(s) match')
                    else:
                        raise RuntimeError(
                            'Unknown results from search\n'
                            f'exactMatchExists = {exactMatchExists}\n'
                            f'unexactMatchExists = {unexactMatchExists}\n'
                            f'resultsAreExact = {resultsAreExact}'
                        )
        if (len_res := len(results)) == 1:
            # Found one object (unexact search)
            return results[0]
        elif len_res == 0:
            # Ran through objects; found nothing
            if detailedFail:
                return BoolDetailed(
                    False,
                    'NoResults',
                    'Did not find any results')
            return None
        if len_res > 1:
            # Ran through objects; found too many results
            if detailedFail:
                return BoolDetailed(
                    False,
                    'TooManyResults',
                    f'Found {len_res} results')
            return None

    class findDict_Object:
        """Convert non-move like objects into move-like objects
        that supports being searched by findDict."""

        def __init__(self, values):
            self.values = values

        def __repr__(self):
            return '{}({})'.format(
                self.__class__.__name__,
                self.values)

        def __str__(self):
            return self['name']

        def __len__(self):
            return len(self.values)

        def __getitem__(self, key):
            return self.values[key]

        def __setitem__(self, key, value):
            self.values[key] = value

        def __iter__(self):
            return iter(self.values)

        def __contains__(self, key):
            return key in self.values

    def findItem(self, values, *,
                 raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching item in the Fighter's inventory.

        Args:
            values (dict): A dictionary of values to match.
            raiseIfFail (bool): If no item matching `values` was found,
                throw an exception.
            exactSearch (bool):

        """
        item = self.findDict(
            self.inventory, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if item is None:
                raise ValueError(
                    f'{self} failed to find an item with values {values}')
            elif isinstance(item, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find an item with values {values}\n'
                    f'Details: {item!r}')

        logger.debug(f"{self.decoloredName}'s Item search "
                     f'returned "{item}"')
        return item

    def findMove(
            self, values: dict, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False,
            showUnsatisfactories=False, **kwargs) -> \
                Union[None, Move, BoolDetailed,
                      Tuple[Optional[Move], List[BoolDetailed]]]:
        """Find the first matching move in the Fighter's moves.

        Args:
            values (Dict): A dictionary of values to compare.
            raiseIfFail (bool): Raise ValueError if a move is not found.
            exactSearch (bool): Match strings exactly instead of by membership.
            detailedFail (bool): Return BoolDetailed when failing a search.
            showUnsatisfactories (bool): Return a tuple containing the search
                result and a list of BoolDetailed objects describing
                unsatisfactories.
                This should only be True when an ignore* keyword argument is
                passed to availableMoves(), and will raise a ValueError
                if it isn't.

        Returns:
            None: Failed to find a result and detailedFail is False.
            Move: A Move was found.
            BoolDetailed: Failed to find a result and detailedFail is True.
            Union[None, Move, BoolDetailed,
                  Tuple[Optional[Move], Optional[BoolDetailed]]]:
                showUnsatisfactories is True and is returning a tuple;
                it contains the search result and a list of
                BoolDetailed objects describing missing dependencies
                of the move. If there are no missing dependencies,
                the list will be empty.

        """
        if showUnsatisfactories:
            # Check if there's a valid reason to have this True
            for key in kwargs:
                if 'ignore' in key:
                    break
            else:
                raise ValueError(
                    'showUnsatisfactories is True but no ignore* keyword '
                    f'argument was passed into findMove ({kwargs!r})'
                )

        # Search for move
        move = self.findDict(
            self.availableMoves(**kwargs), values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if move is None:
                raise ValueError(
                    f'{self} failed to find a move with values {values}')
            elif isinstance(move, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find a move with values {values}\n'
                    f'Details: {move!r}')

        if showUnsatisfactories:
            unsatisfactories = []

        if showUnsatisfactories \
                and isinstance(move, Move):
            def req_plural(req, req_name):
                """Create the missing requirement message."""
                length = len(req[1])
                plur = 's are' if length != 1 else ' is'
                return f'{length} {req_name} requirement{plur} not satisfied'

            # Get search with all requirements
            MoveTypeReq = self.availableMoveCombinationMoveType(
                move, verbose=showUnsatisfactories)
            if MoveTypeReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGMOVETYPE',
                    req_plural(MoveTypeReq, 'MoveType'),
                    MoveTypeReq[1]
                ))
            SkillReq = self.availableMoveCombinationSkill(
                move, verbose=showUnsatisfactories)
            if SkillReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGSKILL',
                    req_plural(SkillReq, 'Skill'),
                    SkillReq[1]
                ))
            InventoryReq = self.availableMoveCombinationInventory(
                move, verbose=showUnsatisfactories)
            if InventoryReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGITEM',
                    req_plural(InventoryReq, 'Item'),
                    InventoryReq[1]
                ))

        logger.debug(f"{self.decoloredName}'s Move search "
                     f'returned "{move}"')
        if showUnsatisfactories:
            return move, unsatisfactories
        return move

    def findCounter(
            self, values, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching counter in the Fighter's counters.

values - A dictionary of values to compare.
raiseIfFail - If True, raise ValueError if a counter is not found.
exactSearch - If True, match strings exactly instead of by membership.
detailedFail - If True, return BoolDetailed when failing a search."""
        counters = [
            self.findDict_Object({'name': i}) for i in self.counters.values()]
        counter = self.findDict(
            counters, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if counter is None:
                raise ValueError(
                    f'{self} failed to find a counter with values {values}')
            elif isinstance(counter, BoolDetailed):
                raise ValueError(
                    f'{self} failed to find a counter with values {values}\n'
                    f'Details: {counter!r}')

        logger.debug(f"{self.decoloredName}'s Counter search "
                     f'returned "{counter}"')
        return counter

    def formatCounters(self):
        """Return a string showing the available counters."""
        return ', '.join([str(c) for c in self.counters.values()])

    def formatMoves(self, **kwargs):
        """Return a string showing the available moves."""
        return ', '.join([str(move) for move in self.availableMoves(**kwargs)])

    def moveCost(self, move, stat, failMessage):
        """If possible, apply costs onto Fighter and return True."""
        if move['name'] == 'None':
            return None
        # If stat cost in move exists
        if f'{stat}Cost' in move:
            # If Fighter can pay stat cost
            if getattr(self, stat) \
                    + self.genCost(move, stat, 'normal') >= 0:
                setattr(self, stat, getattr(self, stat)
                        + round(float(move[f'{stat}Cost'])))
                return True
            else:
                # Print not enough stat message
                stat_obj = self.stats[stat]
                namespace = {
                    'self': self,
                    'move': move,
                    'int_short': stat_obj.int_short,
                    'int_full': stat_obj.int_full,
                    'ext_short': stat_obj.ext_short,
                    'ext_full': stat_obj.ext_full
                }
                print_color(failMessage, namespace=namespace)
                return False
        # Stat cost doesn't exist: return None
        return None

    def useMoveItems(self, move_or_combination=None, return_string=True):
        """Find the combination of items to be used, and subtract them from
        the Fighter's inventory. Will fail if no combination
        was found that worked.

        Args:
            move_or_combination (Union[Move, Iterable[Item]]):
                Either a combination of items to use, or a move
                to gather requirements from.
            return_string (bool): If True, will return a string of
                items that were used and their new count.

        Returns:
            None
            str: A string of items used, if `return_string` is True.

        """
        if isinstance(move_or_combination, Move):
            combination = self.availableMoveCombinationInventory(
                move_or_combination
            )
        else:
            combination = move_or_combination

        # Return detailed booleans if that was given
        if isinstance(combination, BoolDetailed):
            return combination

        if return_string:
            strings = []

        for itemDict in combination:
            invItem = self.findItem({'name': itemDict['name']})

            # If required, find item in inventory and subtract from it
            if 'count' in itemDict:
                invItem['count'] -= itemDict['count']

            # Make sure item count is not negative
            if invItem['count'] < 0:
                raise RuntimeError(f'Item {invItem} count '
                                   f"has gone negative: {invItem['count']}")

            # Else if item count is 0, delete it from inventory
            elif invItem['count'] == 0:
                index = self.inventory.index(invItem)
                del self.inventory[index]

            # Conditionally print out the item used
            if return_string:
                name = invItem['name']
                if 'count' in itemDict:
                    used = itemDict.get('count', 0)
                    newCount = invItem['count']
                    strings.append(
                        format_color(
                            f'{used:,} {name}{util.plural(used)} used '
                            f'({newCount:,} left)'
                        )
                    )
                else:
                    strings.append(format_color(f'{name} used'))

        if return_string:
            return '\n'.join(strings)

    def playerTurnMove(self, target, cmdqueue=None):
        """Obtains a move from the player."""
        logger.debug(f"{self.decoloredName} is moving")
        if cmdqueue is None:
            cmdqueue = [self.battleShellDict['moveCMD']]
        namespace = dict()

        # Get user interaction and use the changes in `namespace`
        # to know which move to use next
        interface.FighterBattleMainShell(
            self, target, namespace, cmdqueue
        ).cmdloop()
        print()

        self.battleShellDict['moveCMD'] = namespace['newMoveCMD']

        return namespace['shell_result']

    def playerCounter(self, move, sender):
        """Obtains a counter from the player.
Note: No counter shell has been created so the placeholder interface code
below is being used."""
        print_color(f'{INDENT}\
{sender} is using {move}, but {self} is able to use a counter!')

        countersMessage = self.formatCounters()

        prompt = (
            f'{INDENT}Counter to attempt performing '
            f'({countersMessage}): '
        )

        while True:
            # TODO: Create shell in separate file to use here
            user_input = input(prompt).lower().strip()

            if user_input == '':
                prompt = (
                    f'{INDENT}Type one of the counters '
                    f'({countersMessage}): '
                )
                continue

            search = self.findCounter(
                {'name': user_input},
                exactSearch=False, detailedFail=True)

            # If search worked, return the counter
            if not isinstance(search, (type(None), BoolDetailed)):
                # Return name since that's how counters work
                return search['name']

            # Else request for a counter again
            elif search is None:
                # Search failed (detailedFail=False)
                prompt = f'{INDENT}Did not find counter, type again: '
            elif isinstance(search, BoolDetailed):
                # Search failed (detailedFail=True)
                if search.name == 'TooManyResults':
                    counterCount = int(search.description.split()[1])
                    prompt = (
                        f'{INDENT}Found {counterCount:,} '
                        'different counters, type again: '
                    )
                elif search.name == 'NoResults':
                    prompt = f'{INDENT}Did not find counter, type again: '

    def move(self, target, move=None):
        logger.debug(f'{self.decoloredName} is moving against {target}')

        # Don't move if an effect has noMove
        for effect in self.status_effects:
            if 'noMove' in effect:
                self.printStatusEffect(effect, 'noMove')
                return

        # If a move is not given, give control to AI/player
        if not move:
            if not self.isPlayer:
                logger.debug(f"{self.decoloredName}'s AI {self.AI} "
                             'is choosing a move')
                move = self.AI.analyseMove(self, target)
            else:
                move = self.playerTurnMove(target)

        logger.debug(f'{self.decoloredName} chose the move "{move}"')

        if move['name'] == 'None':
            print_color(f'{self} did not move.')
            logger.debug(f'{self.decoloredName} sent "{move}" to {target}')
            target.moveReceive(move, sender=self)
            return

        # Combinations available to use move
        if not self.availableMoveCombinationSkill(move):
            logger.debug(f'{self.decoloredName} failed to move; '
                         'lack of skills')
            print_color(f'\
{self} tried using {move} but did not have the needed skills.')
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    target, move, self, info=('senderFail', 'missingSkills'))
            return
        itemRequirements = self.availableMoveCombinationInventory(move)
        if not itemRequirements:
            logger.debug(f'{self.decoloredName} failed to move; '
                         'lack of items')
            print_color(f'\
{self} tried using {move} but did not have the needed items.')
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    target, move, self, info=('senderFail', 'missingItems'))
            return

        # Stat Costs
        for int_short in self.stats:
            # If move failed due to low stats, stop
            if self.moveCost(
                    move, int_short, '{self} tried using {move} '
                    'but the {ext_full} cost was {move:{int_short}C neg}.') \
                    is False:
                logger.debug(f'{self.decoloredName} failed to move; '
                             'lack of {int_short}')
                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        target, move, self, info=(
                            'senderFail', 'lowStats', int_short))
                return

        # Use any items and display the usage if Fighter is a player
        items_used_str = self.useMoveItems(
            itemRequirements, return_string=self.isPlayer)
        if isinstance(items_used_str, str):
            print_color(items_used_str, end='\n\n')

        # Finished, send move
        logger.debug(f'{self.decoloredName} sent "{move}" to {target}')
        target.moveReceive(move, sender=self)

    def receiveEffect(self, effect, stackDuration=True):
        """Receive a StatusEffect.

        If the name of `effect` matches the name of another effect,
        that current effect is replaced with the new effect.

        Args:
            effect (StatusEffect): The effect to add.
            stackDuration (bool): If there is another effect
                with the same name, replace that effect but add its duration
                onto the new `effect`.

        """
        for i, current_effect in enumerate(self.status_effects):
            if str(current_effect) == str(effect):
                if stackDuration:
                    effect['duration'] += self.status_effects[i]['duration']
                self.status_effects[i] = effect
                break
        else:
            self.status_effects.append(effect)

        if 'receiveMessage' in effect and self.hp > 0:
            # Print receive message so long as the fighter has enough health
            # Footnote 3
            self.printStatusEffect(effect, 'receiveMessage')

    def moveReceiveEffects(self, move, info=None, sender=None):
        logger.debug(f'{self} receiving effects from {move}')

        def apply_effect(target, effect):
            logger.debug(f'Applying effect {effect}')

            def chance_to_apply(chance):
                result = (
                    random.uniform(1, 100) <= chance
                    * self.battle_env.base_status_effects_chance_multiplier
                    / 100
                )
                if result:
                    target.receiveEffect(effect.copy())
                return result

            def check_uncountered():
                if chance[1] == 'uncountered':
                    # Conditional syntax: If move was not countered
                    # (100, 'uncountered')
                    result = False
                    if 'normal' in info or 'critical' in info \
                            or 'fail' in info:
                        result = chance_to_apply(chance[0])
                    return {'applied': result}

            default_chance = None

            for chance in effect['chances']:
                logger.debug(f'Effect chance {chance}')
                if len(chance) == 1:
                    # Default; triggers only if all other chances failed
                    # and the move itself did not fail
                    # (100,)
                    default_chance = chance[0]
                elif check_uncountered():
                    return
                elif chance[1] == 'failure':
                    # If move failed
                    if 'senderFail' in info and chance_to_apply(chance[0]):
                        return
                elif chance[1] == 'fast':
                    # If move was fast
                    if 'fast' in info and chance_to_apply(chance[0]):
                        return
                elif chance[1] == 'critical':
                    # If move was critical
                    if 'critical' in info and chance_to_apply(chance[0]):
                        return
                else:
                    # Counters
                    situation_found = False
                    for counter in self.allCounters:
                        if chance[1] == counter and counter in info:
                            # If counter was attempted
                            logger.debug(f'{counter} attempted chance '
                                         f'of {chance[0]}')
                            if chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                        elif chance[1] == f'{counter}Success':
                            # If counter was successful
                            logger.debug(f'{counter}Success chance '
                                         f'of {chance[0]}')
                            if counter in info and 'success' in info \
                                    and chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                        elif chance[1] == f'{counter}Failure':
                            # If counter failed
                            logger.debug(f'{counter}Failure chance '
                                         f'of {chance[0]}')
                            if counter in info and (
                                        'fail' in info or 'critical' in info
                                    ) and chance_to_apply(chance[0]):
                                return
                            situation_found = True
                            break
                    if situation_found:
                        # Found correct situation for counter
                        # but chance_to_apply failed
                        continue
                    else:
                        raise ValueError(
                            f'Unknown chance format {chance!r}')

            if default_chance is not None and 'senderFail' not in info:
                chance_to_apply(default_chance)

        if 'effects' in move:
            for effect in move['effects']:
                if effect['target'] == 'target':
                    apply_effect(self, effect)
                elif effect['target'] == 'sender' and sender is not None:
                    apply_effect(sender, effect)

    def moveReceive(self, move, sender=None):
        logger.debug(f'{self.decoloredName} is receiving "{move}" '
                     f'from {sender.decoloredName}')
        if move['name'] == 'None':
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=('noneMove',))
            return
        # If move fails by chance
        if random.uniform(1, 100) <= self.genChance(move, 'failure'):
            logger.debug(f'"{move}" failed against {self.decoloredName}')
            if sender is not None:
                logger.debug(f'{sender.decoloredName} is receiving '
                             'failure values')
                sender.genFailureValues(move)
                self.printMove(sender, move, 'failureMessage')
                sender._moveReceive(move, values='failure')

                info = ('senderFail', 'chance')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
                return
        # If move counter is possible
        if sender is not None \
                and random.uniform(1, 100) <= self.genChance(move, 'speed'):
            # Don't counter if an effect has noCounter
            def hasNoCounterStatusEffect():
                for effect in self.status_effects:
                    if 'noCounter' in effect:
                        logger.debug(f'{self.decoloredName} has noCounter '
                                     f'status effect from "{effect}"')
                        # Footnote 3
                        self.printStatusEffect(effect, 'noCounter')
                        return True
                return False

            if hasNoCounterStatusEffect():
                counter = 'none'
            elif not self.isPlayer:
                logger.debug(f"{self.decoloredName}'s AI {self.AI} "
                             f'is countering "{move}"')
                counter = self.AI.analyseMoveCounter(self, move, sender)
            else:
                logger.debug(f"{self.decoloredName}'s player "
                             f'is countering "{move}"')
                counter = self.playerCounter(move, sender)

        # If move counter failed
        else:
            if sender is not None:
                logger.debug(f'{self.decoloredName} cannot counter the move')
            counter = False

        logger.debug(f'{self.decoloredName} is using counter {counter!r}')

        # Counter System
        if counter == 'block':
            self.moveReceiveCounterBlock(move, sender)
        elif counter == 'evade':
            self.moveReceiveCounterEvade(move, sender)
        elif counter == 'none':
            self.moveReceiveCounterNone(move, sender)
        elif counter is False:
            self.moveReceiveCounterFalse(move, sender)
        else:
            raise RuntimeError(
                'During moveReceive while countering, '
                f'an unknown counter was given: {counter!r}')

    def moveReceiveCounterNone(self, move, sender):
        # If move is critical
        if random.uniform(1, 100) <= self.genChance(move, 'critical'):
            logger.debug(f'"{move}" against {self.decoloredName} '
                         'is a critical')
            self.genValues(move)
            self.genCriticalValues(move)
            self.printMove(sender, move, 'criticalMessage')
            self._moveReceive(move, values='critical')
            # Apply status effects
            info = ('none', 'critical')
            self.moveReceiveEffects(move, info, sender)
            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.decoloredName} is normal')
            self.genValues(move)
            self.printMove(sender, move)
            self._moveReceive(move, values='none')

            info = ('none', 'normal')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)

    def moveReceiveCounterFalse(self, move, sender):
        # If move is critical
        if random.uniform(1, 100) <= self.genChance(move, 'critical'):
            logger.debug(f'"{move}" against {self.decoloredName} '
                         'is a fast critical')
            self.genCriticalValues(move)
            self.printMove(sender, move, 'fastCriticalMessage')
            self._moveReceive(move, values='critical')

            info = ('fast', 'critical')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.decoloredName} is fast')
            self.genValues(move)
            self.printMove(sender, move, 'fastMessage')
            self._moveReceive(move, values='none')

            info = ('fast', 'normal')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)

    def moveReceiveCounterBlock(self, move, sender):
        # If move is blocked
        if random.uniform(1, 100) <= self.genChance(move, 'block'):
            logger.debug(f'"{move}" against {self.decoloredName} is blocked')
            self.genCounterValues(move, 'block')
            self.printMove(sender, move, 'blockMessage')
            self._moveReceive(move, values='block')

            info = ('block', 'success')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed block
            if random.uniform(1, 100) <= self.genChance(move, 'critical'):
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed block critical')
                self.genCounterFailCriticalValues(move, 'block')
                self.printMove(sender, move, 'blockFailCriticalMessage')
                self._moveReceive(move, values='blockFailCritical')

                info = ('block', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed block')
                self.genCounterFailValues(move, 'block')
                self.printMove(sender, move, 'blockFailMessage')
                self._moveReceive(move, values='blockFail')

                info = ('block', 'fail')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)

    def moveReceiveCounterEvade(self, move, sender):
        # If move is evaded
        if random.uniform(1, 100) <= self.genChance(move, 'evade'):
            logger.debug(f'"{move}" against {self.decoloredName} is evaded')
            self.genCounterValues(move, 'evade')
            self.printMove(sender, move, 'evadeMessage')
            self._moveReceive(move, values='evade')

            info = ('evade', 'success')
            self.moveReceiveEffects(move, info, sender)

            if not self.isPlayer:
                self.AI.analyseMoveReceive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed evade
            if random.uniform(1, 100) <= self.genChance(move, 'critical'):
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed evade critical')
                self.genCounterFailCriticalValues(move, 'evade')
                self.printMove(sender, move, 'evadeFailCriticalMessage')
                self._moveReceive(move, values='evadeFailCritical')

                info = ('evade', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.decoloredName} '
                             'is failed evade')
                self.genCounterFailValues(move, 'evade')
                self.printMove(sender, move, 'evadeFailMessage')
                self._moveReceive(move, values='evadeFail')

                info = ('evade', 'critical')
                self.moveReceiveEffects(move, info, sender)

                if not self.isPlayer:
                    self.AI.analyseMoveReceive(
                        self, move, sender, info=info)

    def _moveReceive(self, move,
                     values='none',
                     sender=None):
        """Private method for applying a move onto Fighter.
Pass in a tuple of stats to apply their corresponding values."""
        logger.debug(f'{self.decoloredName} is receiving values {values}')

        originalValues = values
        if values == 'none':
            values = [f'{stat}Value' for stat in self.stats]
        # If 'failure' is given, use all failure stats
        elif values == 'failure':
            values = [f'failure{stat.upper()}Value' for stat in self.stats]
        # If 'critical' is given, use all critical stats
        elif values == 'critical':
            values = [f'critical{stat.upper()}Value' for stat in self.stats]
        else:
            for counter in self.allCounters:
                # If a counter is given, use all counter stats
                if values == counter:
                    values = [
                        f'{counter}{stat.upper()}Value'
                        for stat in self.stats]
                # If a counter + 'Fail' is given,
                # use all counter fail stats
                elif values == counter + 'Fail':
                    values = [
                        f'{counter}Fail{stat.upper()}Value'
                        for stat in self.stats]
                # If a counter + 'FailCritical' is given,
                # use all counter fail critical stats
                elif values == counter + 'FailCritical':
                    values = [
                        f'{counter}FailCritical{stat.upper()}Value'
                        for stat in self.stats]
        if not isinstance(values, (tuple, list)):
            raise ValueError(
                f'Received {originalValues} but could not parse it')

        logger.debug(f'Parsed {originalValues!r} as {values}')

        original_stats = ', '.join(
            [f'{k}: {v.value}' for k, v in self.stats.items()])

        for stat in self.stats:
            statUpper = stat.upper()
            value = stat + 'Value'
            criticalValue = 'critical' + statUpper + 'Value'
            failValue = 'failure' + statUpper + 'Value'

            for counter in self.allCounters:
                cVal = counter + statUpper + 'Value'
                cFailVal = counter + 'Fail' + statUpper + 'Value'
                cFailCritVal = counter + 'FailCritical' + statUpper + 'Value'
                if cVal in values and cVal in move:
                    setattr(self, stat, getattr(self, stat)
                            + round(float(move[cVal])))
                if cFailVal in values and cFailVal in move:
                    setattr(self, stat, getattr(self, stat)
                            + round(float(move[cFailVal])))
                if cFailCritVal in values and cFailCritVal in move:
                    setattr(self, stat, getattr(self, stat)
                            + round(float(move[cFailCritVal])))
            if value in values and value in move:
                setattr(self, stat, getattr(self, stat)
                        + round(float(move[value])))
            if criticalValue in values and criticalValue in move:
                setattr(self, stat, getattr(self, stat)
                        + round(float(move[criticalValue])))
            if failValue in values and failValue in move:
                setattr(self, stat, getattr(self, stat)
                        + round(float(move[failValue])))

        new_stats = ', '.join(
            [f'{k}: {v.value}' for k, v in self.stats.items()])
        logger.debug(f"{self.decoloredName}'s _moveReceive changed stats "
                     f'from:\n{original_stats}\n'
                     f'to {new_stats}')

    @staticmethod
    def availableMoveCombination(move, requirement, objects,
                                 membership_func=None, verbose=False):
        """Returns True if objects has the requirements for a move.

        When no combination is required or the move is NoneMove,
        True is returned.
        When the first available combination is found, it is returned.
        If no combinations match, False is returned.
        Note: Returned booleans are of type BoolDetailed.

        Args:
            move (Move): The move to check.
            requirement:
                The requirements key from move to check in `objects`.
            objects:
                The container of prerequisites.
            membership_func (Optional[Callable]): The function to use to
                determine if an object in `objects` matches the requirement.
                Takes the objects and an object in a combination
                from requirement.

                def membership_func(objects, obj):
                    ...

                If None, will use `obj in objects`.
            verbose (bool): For moves with one combination of requirements, if
                items are missing, show them in the BoolDetailed description.

        Returns:
            BoolDetailed:
            Tuple[BoolDetailed, List]: verbose is True and there is only
                one combination of requirements, so a tuple is returned
                with the BoolDetailed and a list of the objects that were not
                in `objects`, if there were any.
            Tuple[BoolDetailed, None]: verbose is True but there is more than
                one combination of requirements, so no missing objects are
                returned. This could be programmed in to map the missing
                objects to each combination.

        """
        missing = []

        if move['name'] == 'None':
            result = BoolDetailed(
                True, 'NONEMOVE',
                'NoneMove was given.')
            if verbose:
                return result, missing
            return result

        if requirement in move:
            requirements = move[requirement]
            for combination in requirements:
                for obj in combination:
                    if membership_func is not None:
                        if membership_func(objects, obj):
                            continue  # Object matched, continue combination
                    # No membership_func was given, test for membership
                    elif obj in objects:
                        continue  # Object matched, continue combination

                    if verbose and len(requirements) == 1:
                        # Store the missing objects for verbose
                        missing.append(obj)
                        continue
                    else:
                        break  # Skip combination, object missing
                else:
                    if verbose:
                        return combination, missing
                    return combination
            else:
                result = BoolDetailed(
                    False, 'NOCOMBINATIONFOUND',
                    'Did not find any matching combination.')
                if verbose:
                    return result, missing
                return result
        else:
            result = BoolDetailed(
                True, 'NOREQUIREMENTS',
                'No requirements found.')
            if verbose:
                return result, missing
            return result

    def availableMoveCombinationMoveType(self, move, verbose=False):
        """Returns True if Fighter has the MoveType requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        return self.availableMoveCombination(
            move, 'moveTypes', self.moveTypes, verbose=verbose)

    def availableMoveCombinationSkill(self, move, verbose=False):
        """Returns True if Fighter has the Skill requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        def membership_func(objects, combSkill):
            return any(
                selfSkill >= combSkill
                if type(selfSkill) == type(combSkill) else False
                for selfSkill in objects
            )

        return self.availableMoveCombination(
            move, 'skillRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def availableMoveCombinationInventory(self, move, verbose=False):
        """Returns True if Fighter has the Item requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Use availableMoveCombination with verbose enabled.

        """
        def membership_func(objects, itemDict):
            search = self.findItem({'name': itemDict['name']})
            if search is None:
                # Item not found
                return False
            if 'count' in itemDict:
                # Item needs to be depleted
                if search['count'] >= itemDict['count']:
                    # Item can be depleted
                    return True
                else:
                    # Item cannot be depleted
                    return False
            else:
                # Item doesn't need to be depleted
                return True

        return self.availableMoveCombination(
            move, 'itemRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def availableMove(
            self, move, *,
            ignoreMoveTypes=False, ignoreSkills=False, ignoreItems=False):
        """Returns True if a move can be available in the Fighter's moveset.

        The attributes that can influence this search are:
            self.moveTypes
            self.skills
            self.inventory

        Args:
            move (Move): The move to verify usability.
            ignoreMoveTypes (bool): Ignore checking for MoveTypes.
            ignoreSkills (bool): Ignore checking for Skills.
            ignoreItems (bool): Ignore checking for Items.

        """
        # MoveType Check
        if not ignoreMoveTypes \
                and not self.availableMoveCombinationMoveType(move):
            return BoolDetailed(
                False, 'MISSINGMOVETYPE',
                'Missing required move types.')
        # Skill Check
        if not ignoreSkills \
                and not self.availableMoveCombinationSkill(move):
            return BoolDetailed(
                False, 'MISSINGSKILL',
                'Missing required skills.')
        # Item Check
        if not ignoreItems \
                and not self.availableMoveCombinationInventory(move):
            return BoolDetailed(
                False, 'MISSINGINVENTORY',
                'Missing required items.')

        return True

    def availableMoves(self, moves=None, **kwargs):
        """Returns a list of available moves from a list of moves.
moves - The list to filter. If None, will use self.moves."""
        if moves is None:
            moves = self.moves
        return [move for move in moves if self.availableMove(
            move, **kwargs)]

    # Value Generators
    def genValue(self, move, stat, changeRandNum=True):
        """Generate a Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        statName = stat + 'Value'
        constantName = self.stats[stat].int_full

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(self.battle_env,
            f'base_value_{constantName}_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genValues(self, move, changeRandNum=True):
        """Generate values for every stat in a move.
Returns None if there is no value for a stat."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genValue(
                move, stat, changeRandNum)

        return values

    # Cost Generators
    def genCost(self, move, stat, case, changeRandNum=True):
        """Generate a Cost from a move.
move - The move to generate/extract the cost from.
stat - The stat cost that is being generated/extracted.
case - The situation that the failure value is being taken from.
    failure - When failing the move.
changeRandNum - If True, change the move's randNum
    to the generated cost if available."""
        cases = ('normal', 'failure')
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if case not in cases:
            raise ValueError(
                f'{case} is not a valid situation '
                f"({', '.join([repr(c) for c in cases])})")

        statConstant = self.stats[stat].int_full

        # Parse case into statName
        if case == 'normal':
            statName = stat + 'Cost'
        elif case == 'failure':
            statName = 'failure' + stat.upper() + 'Cost'
        else:
            raise RuntimeError(
                f'Could not parse case {case!r}, possibly no switch case')

        if statName not in move:
            return None

        cost = Bound.call_random(move[statName])

        cost *= self.battle_env.base_energies_cost_multiplier_percent / 100
        cost *= getattr(self.battle_env,
            f'base_energy_cost_{statConstant}_multiplier_percent'
        ) / 100

        cost = round(cost)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = cost

        return cost

    def genChance(self, move, chanceType):
        """Generate a chance from a move.
move - The move to extract chance from.
chanceType - The type of the chance to extract.
    Accepts counter names, 'speed', 'failure', and 'critical'."""
        validChancesNonCounter = ['speed', 'failure', 'critical']
        validChancesCounter = [counter for counter in self.allCounters]
        validChances = validChancesNonCounter + validChancesCounter
        if chanceType not in validChances:
            raise ValueError(
                f'{chanceType} is not a valid chance '
                f"({', '.join([repr(s) for s in validChances])})")

        chanceName = chanceType + 'Chance'

        if chanceType == 'speed':
            chance = 100 - move['speed']

            chance = util.divi_zero(
                chance, self.battle_env.base_speed_multiplier_percent / 100)

            return chance

        elif chanceType in validChancesNonCounter:
            chance = Bound.call_random(move[chanceName])

            chance *= getattr(self.battle_env,
                f'base_{chanceType}_chance_percent') / 100

            return chance

        elif chanceType in validChancesCounter:
            chanceConstant = self.allCounters[chanceType]

            chance = Bound.call_random(move[chanceName])

            chance *= getattr(self.battle_env,
                f'base_{chanceConstant}_chance_percent') / 100

            return chance

        else:
            raise RuntimeError(f'Failed to parse chanceType {chanceType}.')

    # Critical Generators
    def genCriticalValue(self, move, stat, changeRandNum=True):
        """Generate a Value from a move affected by its critical multiplier.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")

        statName = 'critical' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(self.battle_env,
            f'base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCriticalValues(self, move, changeRandNum=True):
        """Generate critical values for every stat in a move.
Returns None if there is no critical value for a stat."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genCriticalValue(
                move, stat, changeRandNum)

        return values

    # Counter Generators

    def genCounterValue(self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
counter - The counter's fail value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full
        counterConstant = self.allCounters[counter]

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(self.battle_env,
            f'base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= getattr(self.battle_env,
            f'base_{counterConstant}_values_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterValues(self, move, counter, changeRandNum=True):
        """Generate counter values for every stat in a move.
Returns None if there is no counter value for a stat."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genCounterValue(
                move, stat, counter, changeRandNum)

        return values

    def genCounterFailValue(self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Fail Value from a move.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
counter - The counter's fail value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + 'Fail' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full
        counterConstant = self.allCounters[counter]

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(self.battle_env,
            f'base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= getattr(self.battle_env,
            f'base_{counterConstant}_fail_value_multiplier_percent'
        ) / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterFailValues(self, move, counter, changeRandNum=True):
        """Generate counter failure values for every stat in a move.
Returns None if there is no failure value for a stat."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genCounterFailValue(
                move, stat, counter, changeRandNum)

        return values

    def genCounterFailCriticalValue(
            self, move, stat, counter, changeRandNum=True):
        """Generate a Counter Fail Value from a move affected by
its critical multiplier.
move - The move to generate/extract the value from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's randNum
    to the generated value if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.allCounters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.allCounters])})")

        statName = counter + 'FailCritical' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(self.battle_env,
            f'base_value_{statConstant}_multiplier_percent'
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    def genCounterFailCriticalValues(self, move, counter, changeRandNum=True):
        """Generate critical values for every stat in a move.
Returns None if there is no critical value for a stat."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genCounterFailCriticalValue(
                move, stat, counter, changeRandNum)

        return values

    def genFailureValue(self, move, stat, changeRandNum=True):
        """Generate a failure value from a move.
move - The move to generate/extract failureValue from.
stat - The stat value that is being generated/extracted.
changeRandNum - If True, change the move's failureValue.randNum
    to the generated failureValue if available."""
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")

        statName = 'failure' + stat.upper() + 'Value'

        if statName not in move:
            return None

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= self.battle_env.base_failure_multiplier_percent / 100

        value = round(value)

        if changeRandNum and isinstance(move[statName], Bound):
            move[statName].randNum = value

        return value

    # Failure Generator
    def genFailureValues(self, move, changeRandNum=True):
        """Generate failure values for every stat in a move.
Returns None if there is no failure value for a stat.
move - The move to generate/extract failureValue from.
changeRandNum - If True, change the move's failure values' randNum
    to the generated value if available."""
        values = dict()
        for stat in self.stats:
            values[stat] = self.genFailureValue(
                move, stat, changeRandNum)

        return values
