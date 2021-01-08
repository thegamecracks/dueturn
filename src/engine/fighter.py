# TODO: Standardize the Fighter's method names to follow
# lowercase_separated_with_underscores
import random

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
from src.utility import custom_divide, plural

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
        movetypes (Optional[List[MoveType]]):
            A list of `MoveType` that the Fighter has.
            If None, defaults to an empty list.
        moves (Optional[List[Move]]):
            A list of `Move` that the Fighter has.
            If None, defaults to an empty list.
        counters (Optional[Dict[str, str]]):
            A dictionary of counters that the Fighter has.
            If None, defaults to a shallow copy of Fighter.all_counters.
        inventory (Optional[List[Item]]):
            A list of `Item` that the Fighter has.
            If None, defaults to an empty list.
        is_player (bool): If True, provides an interface for the user to
            command the Fighter with during a battle.
            If False, uses `AI` to command the Fighter.
        AI (Optional[Any]): The AI that the Fighter uses if not `is_player`.
        interface_shell_dict (Optional[dict]): A dictionary used by the user's
            interface when battling. If None, defaults to a dictionary
            specifying to the shell that it is the user's first time.

    """
    all_counters = {  # Footnote 1
        'none': 'none',
        'block': 'block',
        'evade': 'evade'
    }

    def __init__(
            self, name: str, battle_env=None,
            stats=None,
            status_effects=None,
            skills=None,
            movetypes=None,
            moves=None,
            counters=None,
            inventory=None,
            is_player=False,
            AI=None,
            interface_shell_dict=None):

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
                self.stats[int_short].value = (
                    self.stats[int_short].bound.clamp(value)
                )

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
        if movetypes is None: self.movetypes = []
        else: self.movetypes = movetypes

        # Moves default is an empty list
        if moves is None: self.moves = []
        else: self.moves = moves

        # Counters default are all counters
        if counters is None: self.counters = self.all_counters.copy()
        else: self.counters = counters

        # Inventory default is an empty list
        if inventory is None: self.inventory = []
        else: self.inventory = inventory

        # is_player default is False
        self.is_player = is_player

        # AI default is FighterAIGeneric()
        # if AI is None: self.AI = FighterAIGeneric()
        # else: self.AI = AI
        self.AI = AI

        if interface_shell_dict is None:
            self.interface_shell_dict = {
                # Autorun on start of player_move Shell
                'moveCMD': ['first_time']
            }
        else:
            self.interface_shell_dict = interface_shell_dict

        logger.debug(f'Created fighter ({self.name_decolored})')

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                [
                    repr(x) for x in (
                        self.name,
                        self.stats,
                        self.skills, self.movetypes,
                        self.moves, self.counters,
                        self.inventory, self.is_player
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
        self._name_decolored = format_color(name, no_color=True)

    @property
    def name_decolored(self):
        return self._name_decolored

    @name_decolored.setter
    def name_decolored(self, name):
        raise AttributeError(
            'This attribute cannot be changed directly; use self.name')

    def apply_values(self, values, *, require_sufficiency=False):
        """Apply a dictionary of values onto Fighter.

        Args:
            values (Dict[str, Union[int, None]]): A dictionary of values.
                Dictionaries provided by `Fighter.gen_values`
                or `Fighter.gen_costs` will work with this.
            require_sufficiency (bool): If True, will return BoolDetailed
                if a given value makes its stat go below 0. Otherwise,
                simply applies the value onto stat.
                Note that the new stat is clamped to the Stat's bound
                by the property which happens only after checking
                that there is sufficient stat available, so if a Stat has a
                lower bound above 0 but the value would set the stat below 0
                ignoring that bound, that is considered insufficient.

        Returns:
            dict: A dictionary of the new stat values.
            BoolDetailed: Failed to apply stats.
                Has a value of False and the description attribute contains
                (int_short, value, new_stat), where:
                    int_short: The internal short name of the stat at issue.
                    value: The cost being applied onto stat.
                    new_stat: The result of applying cost onto the stat,
                        which should be negative.

        """
        logger.debug(f'{self.name_decolored} is receiving values {values}')

        # Take note of old stats for logging
        old_stats_str = ', '.join(
            [f'{k}: {v.value}' for k, v in self.stats.items()])

        new_stats = {}

        for stat, value in values.items():
            stat_value = getattr(self, stat, None)

            if stat_value is None:
                # This stat doesn't exist
                continue

            new_stat = stat_value
            if value is not None:
                new_stat += value

            if require_sufficiency and new_stat < 0:
                return BoolDetailed(
                    False, 'lowStat', (stat, value, new_stat))
            else:
                new_stats[stat] = new_stat

        # Applies new_stats onto Fighter
        for stat, new_stat in new_stats.items():
            setattr(self, stat, new_stat)

        new_stats_str = ', '.join(
            [f'{k}: {v.value}' for k, v in self.stats.items()])
        logger.debug(f"{self.name_decolored} changed stats "
                     f'from:\n{old_stats_str}\n'
                     f'to {new_stats_str}')

        return new_stats

    @staticmethod
    def available_combination_in_move(
            move, requirement, objects,
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

    def available_items_in_move(self, move, verbose=False):
        """Returns True if Fighter has the Item requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Provide a list of missing requirements.

        """
        def membership_func(objects, itemDict):
            search = self.find_item({'name': itemDict['name']})
            if search is None:
                # Item not found
                return False
            if 'count' in itemDict:
                # Item needs to be depleted
                if search['count'] >= itemDict['count']:
                    # Item can be depleted
                    return True
                else:
                    # Item requirement exceeds inventory quantity
                    return False
            else:
                # Item doesn't need to be depleted
                return True

        return self.available_combination_in_move(
            move, 'itemRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def available_move(
            self, move, *,
            ignore_movetypes=False, ignore_skills=False, ignore_items=False):
        """Returns True if a move can be available in the Fighter's moveset.

        The attributes that can influence this search are:
            self.movetypes
            self.skills
            self.inventory

        Args:
            move (Move): The move to verify usability.
            ignore_movetypes (bool): Ignore checking for MoveTypes.
            ignore_skills (bool): Ignore checking for Skills.
            ignore_items (bool): Ignore checking for Items.

        """
        # MoveType Check
        if not ignore_movetypes \
                and not self.available_movetypes_in_move(move):
            return BoolDetailed(
                False, 'MISSINGMOVETYPE',
                'Missing required move types.')
        # Skill Check
        if not ignore_skills \
                and not self.available_skills_in_move(move):
            return BoolDetailed(
                False, 'MISSINGSKILL',
                'Missing required skills.')
        # Item Check
        if not ignore_items \
                and not self.available_items_in_move(move):
            return BoolDetailed(
                False, 'MISSINGINVENTORY',
                'Missing required items.')

        return True

    def available_moves(self, moves=None, **kwargs):
        """Returns a list of available moves from a list of moves.

        Args:
            moves (Iterable[Moves]): Moves to filter.
                If None, will use self.moves.

        """
        if moves is None:
            moves = self.moves

        available = []

        for move in moves:
            check = self.available_move(move, **kwargs)
            if check:
                available.append(move)
            else:
                logger.debug(f'{move} not available for {self.name_decolored}:'
                             f' {check.description}')

        return available

    def available_movetypes_in_move(self, move, verbose=False):
        """Returns True if Fighter has the MoveType requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Provide a list of any missing requirements.

        """
        return self.available_combination_in_move(
            move, 'movetypes', self.movetypes, verbose=verbose)

    def available_skills_in_move(self, move, verbose=False):
        """Returns True if Fighter has the Skill requirements for a move.

        Args:
            move (Move): The move to check.
            verbose (bool): Provide a list of missing requirements.

        """
        def membership_func(objects, combSkill):
            return any(
                selfSkill >= combSkill
                if type(selfSkill) == type(combSkill) else False
                for selfSkill in objects
            )

        return self.available_combination_in_move(
            move, 'skillRequired',
            self.skills, membership_func,
            verbose=verbose
        )

    def find_counter(
            self, values, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching counter in the Fighter's counters.

values - A dictionary of values to compare.
raiseIfFail - If True, raise ValueError if a counter is not found.
exactSearch - If True, match strings exactly instead of by membership.
detailedFail - If True, return BoolDetailed when failing a search."""
        counters = [
            self.find_dict_Object({'name': i}) for i in self.counters.values()]
        counter = self.find_dict(
            counters, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if counter is None:
                raise ValueError(f'{self.name_decolored} failed to find '
                                 f'a counter with values {values}')
            elif isinstance(counter, BoolDetailed):
                raise ValueError(f'{self.name_decolored} failed to find '
                                 f'a counter with values {values}\n'
                                 f'Details: {counter!r}')

        logger.debug(f"{self.name_decolored}'s Counter search "
                     f'returned "{counter}"')
        return counter

    @staticmethod
    def find_dict(objects, values,
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
            return
        if len_res > 1:
            # Ran through objects; found too many results
            if detailedFail:
                return BoolDetailed(
                    False,
                    'TooManyResults',
                    f'Found {len_res} results')
            return

    class find_dict_Object:
        """Convert non-move like objects into move-like objects
        that supports being searched by find_dict."""

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

    def find_item(self, values, *,
                  raiseIfFail=False, exactSearch=True, detailedFail=False):
        """Find the first matching item in the Fighter's inventory.

        Args:
            values (dict): A dictionary of values to match.
            raiseIfFail (bool): If no item matching `values` was found,
                throw an exception.
            exactSearch (bool):

        """
        item = self.find_dict(
            self.inventory, values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if item is None:
                raise ValueError(f'{self.name_decolored} failed to find '
                                 f'an item with values {values}')
            elif isinstance(item, BoolDetailed):
                raise ValueError(f'{self.name_decolored} failed to find '
                                 f'an item with values {values}\n'
                                 f'Details: {item!r}')

        logger.debug(f"{self.name_decolored}'s Item search "
                     f'returned "{item}"')
        return item

    def find_move(
            self, values: dict, *,
            raiseIfFail=False, exactSearch=True, detailedFail=False,
            showUnsatisfactories=False, **kwargs):
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
                passed to available_moves(), and will raise a ValueError
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
                    f'argument was passed into find_move ({kwargs!r})'
                )

        # Search for move
        move = self.find_dict(
            self.available_moves(**kwargs), values,
            exactSearch=exactSearch, detailedFail=detailedFail)

        if raiseIfFail:
            if move is None:
                raise ValueError(f'{self.name_decolored} failed to find a move'
                                 f' with values {values}')
            elif isinstance(move, BoolDetailed):
                raise ValueError(f'{self.name_decolored} failed to find a move'
                                 f' with values {values}\n'
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
            MoveTypeReq = self.available_movetypes_in_move(
                move, verbose=showUnsatisfactories)
            if MoveTypeReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGMOVETYPE',
                    req_plural(MoveTypeReq, 'MoveType'),
                    MoveTypeReq[1]
                ))
            SkillReq = self.available_skills_in_move(
                move, verbose=showUnsatisfactories)
            if SkillReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGSKILL',
                    req_plural(SkillReq, 'Skill'),
                    SkillReq[1]
                ))
            InventoryReq = self.available_items_in_move(
                move, verbose=showUnsatisfactories)
            if InventoryReq[1]:
                unsatisfactories.append(BoolDetailed(
                    False,
                    'MISSINGITEM',
                    req_plural(InventoryReq, 'Item'),
                    InventoryReq[1]
                ))

        logger.debug(f"{self.name_decolored}'s Move search "
                     f'returned "{move}"')
        if showUnsatisfactories:
            return move, unsatisfactories
        return move

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

    # Value Generators
    def gen_value(self, move, stat):
        """Generate a Value from a move.

        If the move is missing the stat, returns None.

        Value format: {stat}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str): The stat value that is being generated/extracted.

        Returns:
            int: The generated/extracted value.
            None: The stat could not be found.
        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        statName = stat + 'Value'
        constantName = self.stats[stat].int_full

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(
            self.battle_env,
            f'base_value_{constantName}_multiplier_percent',
            100
        ) / 100

        value = round(value)

        return value

    def gen_values(self, move):
        """Generate Values for every stat in a move and return a dictionary
        of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract values from.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_value(move, stat)

        return values

    # Cost Generators
    def gen_cost(self, move, stat, case='normal'):
        """Generate a Cost from a move.

        Cost format: {stat}Cost

        Args:
            move (Move): The move to generate/extract the cost from.
            stat (str): The stat cost that is being generated/extracted.
            case (str): The situation that dictates what cost to use.
                normal: The standard "{stat}Cost".
                failure: When a move fails, this situation requires
                    "failure{stat}Cost".

        """
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
            return

        cost = Bound.call_random(move[statName])

        cost *= self.battle_env.base_stat_costs_multiplier_percent / 100
        cost *= getattr(
            self.battle_env,
            f'base_stat_cost_{statConstant}_multiplier_percent',
            100
        ) / 100

        cost = round(cost)

        return cost

    def gen_costs(self, move, case='normal'):
        """Generate Costs for every stat in a move and return a dictionary
        of the generated costs.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract costs from.
            case (str): The situation that dictates what cost to use.

        Returns:
            Dict[str, Union[int, None]]

        """
        costs = dict()
        for stat in self.stats:
            costs[stat] = self.gen_cost(move, stat, case)

        return costs

    def gen_chance(self, move, chanceType):
        """Generate a Chance from a move.

        Args:
            move (Move): The move to extract chance from.
            chanceType (str): The type of the chance to extract.
                Allowed chances:
                    'critical'
                    'failure'
                    'speed'
                    <any counter name the Fighter has>

        """
        validChancesNonCounter = ['speed', 'failure', 'critical']
        validChancesCounter = [counter for counter in self.all_counters]
        validChances = validChancesNonCounter + validChancesCounter
        if chanceType not in validChances:
            raise ValueError(
                f'{chanceType} is not a valid chance '
                f"({', '.join([repr(s) for s in validChances])})")

        chanceName = chanceType + 'Chance'

        if chanceType == 'speed':
            chance = 100 - move['speed']

            chance = custom_divide(
                chance, self.battle_env.base_speed_multiplier_percent / 100)

            return chance

        elif chanceType in validChancesNonCounter:
            chance = Bound.call_random(move[chanceName])

            chance *= getattr(
                self.battle_env,
                f'base_{chanceType}_chance_percent',
                100
            ) / 100

            return chance

        elif chanceType in validChancesCounter:
            chanceConstant = self.all_counters[chanceType]

            chance = Bound.call_random(move[chanceName])

            chance *= getattr(
                self.battle_env,
                f'base_{chanceConstant}_chance_percent',
                100
            ) / 100

            return chance

        else:
            raise RuntimeError(f'Failed to parse chanceType {chanceType}.')

    # Critical Generators
    def gen_critical_value(self, move, stat):
        """Generate a Value from a move affected by its critical multiplier.

        Value format: critical{stat.upper()}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str) The stat value that is being generated/extracted.

        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")

        statName = 'critical' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(
            self.battle_env,
            f'base_value_{statConstant}_multiplier_percent',
            100
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        return value

    def gen_critical_values(self, move):
        """Generate critical values for every stat in a move and
        return a dictionary of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract critical values from.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_critical_value(move, stat)

        return values

    # Counter Generators
    def gen_counter_value(self, move, stat, counter):
        """Generate a Counter Value from a move.

        Value format: {counter}{stat.upper()}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str) The stat value that is being generated/extracted.
            counter (str): The counter used to defend against the move.

        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.all_counters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.all_counters])})")

        statName = counter + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full
        counterConstant = self.all_counters[counter]

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(
            self.battle_env,
            f'base_value_{statConstant}_multiplier_percent',
            100
        ) / 100

        value *= getattr(
            self.battle_env,
            f'base_{counterConstant}_values_multiplier_percent',
            100
        ) / 100

        value = round(value)

        return value

    def gen_counter_values(self, move, counter):
        """Generate counter values for every stat in a move and
        return a dictionary of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract counter values from.
            counter (str): The counter used to defend against the move.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_counter_value(move, stat, counter)

        return values

    def gen_counter_fail_value(self, move, stat, counter):
        """Generate a Counter Fail Value from a move.

        Value format: {counter}Fail{stat.upper()}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str) The stat value that is being generated/extracted.
            counter (str): The counter used to defend against the move.

        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.all_counters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.all_counters])})")

        statName = counter + 'Fail' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full
        counterConstant = self.all_counters[counter]

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(
            self.battle_env,
            f'base_value_{statConstant}_multiplier_percent',
            100
        ) / 100

        value *= getattr(
            self.battle_env,
            f'base_{counterConstant}_fail_value_multiplier_percent',
            100
        ) / 100

        value = round(value)

        return value

    def gen_counter_fail_values(self, move, counter):
        """Generate counter failure values for every stat in a move and
        return a dictionary of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract counter values from.
            counter (str): The counter used to defend against the move.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_counter_fail_value(move, stat, counter)

        return values

    def gen_counter_fail_critical_value(self, move, stat, counter):
        """Generate a Counter Fail Value from a move affected by
        its critical multiplier.

        Value format: {counter}FailCritical{stat.upper()}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str) The stat value that is being generated/extracted.
            counter (str): The counter used to defend against the move.

        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")
        if counter not in self.all_counters:
            raise ValueError(
                f'{counter!r} is not a Fighter counter '
                f"({', '.join([repr(s) for s in self.all_counters])})")

        statName = counter + 'FailCritical' + stat.upper() + 'Value'
        statConstant = self.stats[stat].int_full

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= getattr(
            self.battle_env,
            f'base_value_{statConstant}_multiplier_percent',
            100
        ) / 100

        value *= self.battle_env.base_critical_value_multiplier_percent / 100

        value = round(value)

        return value

    def gen_counter_fail_critical_values(self, move, counter):
        """Generate critical failure values for every stat in a move and
        return a dictionary of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract counter values from.
            counter (str): The counter used to defend against the move.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_counter_fail_critical_value(
                move, stat, counter)

        return values

    # Failure Generators
    def gen_failure_value(self, move, stat):
        """Generate a failure value from a move.

        Value format: failure{stat.upper()}Value

        Args:
            move (Move): The move to generate/extract the value from.
            stat (str) The stat value that is being generated/extracted.

        """
        if stat not in self.stats:
            raise ValueError(
                f'{stat} is not a Fighter stat '
                f"({', '.join([repr(s) for s in self.stats])})")

        statName = 'failure' + stat.upper() + 'Value'

        if statName not in move:
            return

        value = Bound.call_random(move[statName])

        value *= self.battle_env.base_values_multiplier_percent / 100
        value *= self.battle_env.base_failure_multiplier_percent / 100

        value = round(value)

        return value

    def gen_failure_values(self, move):
        """Generate failure values for every stat in a move and
        return a dictionary of the generated values.

        If the move is missing a stat, that key will have a value of None.

        Args:
            move (Move): The move to generate/extract counter values from.

        Returns:
            Dict[str, Union[int, None]]

        """
        values = dict()
        for stat in self.stats:
            values[stat] = self.gen_failure_value(move, stat)

        return values

    def has_move(self, move, match_by_id=False):
        """Check if the fighter has a move."""
        if match_by_id:
            return id(move) in (id(m) for m in self.moves)
        return move in self.moves

    def move(self, target, move=None,
             do_not_send=False, must_have_move=True):
        """Move against a fighter.

        Args:
            target (Fighter): The opposing fighter.
            move (Optional[Move]): The move to use against target.
                If None, will ask user/AI to pick a move.
            do_not_send (bool): If True, move requirements are applied
                but `target.move_receive` is not called. Helpful for using
                custom code between this method and `target.move_receive`.
            must_have_move (bool): If True, an error is raised if
                `move`, whether passed into the method or returned by
                the user/AI, does not exist within self.moves.

        Returns:
            None: self was unable to move.
            dict: A dict containing:
                    sender: The fighter sending the move.
                    move: The move that was selected.
                    costs: The costs of using the move.
                This provides the information required to use
                `target.move_receive` outside of this method if custom
                code is being executed in the battle loop.

        """
        def send_move(move, sender_costs=None):
            if not do_not_send:
                logger.debug(f'{self.name_decolored} sent "{move}" '
                             f'to {target.name_decolored}')
                target.move_receive(
                    move, sender=self, sender_costs=sender_costs)
            else:
                logger.debug(f'{self.name_decolored} spent prerequisites for '
                             f'"{move}" but did not send '
                             f'to {target.name_decolored}')

        logger.debug(f'{self.name_decolored} is moving '
                     f'against {target.name_decolored}')

        # Don't move if an effect has noMove
        for effect in self.status_effects:
            if 'noMove' in effect:
                self.print_status_effect(effect, None, 'noMove')
                return

        # If a move is not given, give control to AI/player
        if not move:
            if not self.is_player:
                logger.debug(f"{self.name_decolored}'s AI {self.AI} "
                             'is choosing a move')
                move = self.AI.analyseMove(self, target)
            else:
                move = self.player_move(target)

        logger.debug(f'{self.name_decolored} chose the move "{move}"')

        # Enforce move requirement in the fighter
        if must_have_move and not self.has_move(move):
            raise ValueError(f'"{move}" does not exist in '
                             f"{self.name_decolored}'s moves")

        if move['name'] == 'None':
            print_color(f'{self} did not move.')
            send_move(move)
            # Return used move and an empty dict showing no stats were used
            return {
                'sender': self,
                'move': move,
                'costs': {}
            }

        # Combinations available to use move
        if not self.available_skills_in_move(move):
            logger.debug(f'{self.name_decolored} failed to move; '
                         'lack of skills')
            print_color(f'{self} tried using {move} but did not'
                        ' have the needed skills.')
            if not self.is_player:
                self.AI.analyse_move_receive(
                    target, move, self, info=('senderFail', 'missingSkills'))
            return
        itemRequirements = self.available_items_in_move(move)
        if not itemRequirements:
            logger.debug(f'{self.name_decolored} failed to move;'
                         ' lack of items')
            print_color(f'{self} tried using {move} but did not'
                        ' have the needed items.')
            if not self.is_player:
                self.AI.analyse_move_receive(
                    target, move, self, info=('senderFail', 'missingItems'))
            return

        # Stat Costs
        costs = self.gen_costs(move)
        new_stats = self.apply_values(costs, require_sufficiency=True)
        if isinstance(new_stats, BoolDetailed) and not new_stats:
            # Insufficient stat available
            stat, cost, new_stat = new_stats.description
            self.print_insufficient_cost(move, stat, cost)
            logger.debug(f'{self.name_decolored} failed to move; '
                         f'lack of {stat}')

            if not self.is_player:
                self.AI.analyse_move_receive(
                    target, move, self, info=(
                        'senderFail', 'lowStat', stat))
            return

        # Use any items and display the usage if Fighter is a player
        items_used_str = self.use_item_requirements(
            itemRequirements, return_string=self.is_player)
        if isinstance(items_used_str, str):
            print_color(items_used_str, end='\n\n')

        # Finished, send move
        send_move(move, costs)
        return {
            'sender': self,
            'move': move,
            'costs': costs
        }

    def move_receive(self, move, sender, sender_costs):
        logger.debug(f'{self.name_decolored} is receiving "{move}" '
                     f'from {sender.name_decolored}')

        if move['name'] == 'None':
            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=('noneMove',))
            return

        # If move fails by chance
        if random.uniform(1, 100) <= self.gen_chance(move, 'failure'):
            logger.debug(f'"{move}" failed against {self.name_decolored}')
            if sender is not None:
                logger.debug(f'{sender.name_decolored} is receiving '
                             'failure values')
                values = sender.gen_failure_values(move)
                self.print_move(sender, move, values, sender_costs,
                                'failureMessage')
                sender.apply_values(values)

                info = ('senderFail', 'chance')
                # Since the move failed, do not receive effects from the move
                # self.receive_status_effects_from_move(move, info, sender)

                if not self.is_player:
                    self.AI.analyse_move_receive(
                        self, move, sender, info=info)
                return
        # If move counter is possible
        if sender is not None \
                and random.uniform(1, 100) <= self.gen_chance(move, 'speed'):
            # Don't counter if an effect has noCounter
            def status_effect_has_noCounter():
                for effect in self.status_effects:
                    if 'noCounter' in effect:
                        logger.debug(f'{self.name_decolored} has noCounter '
                                     f'status effect from "{effect}"')
                        # Footnote 3
                        self.print_status_effect(effect, None, 'noCounter')
                        return True
                return False

            if status_effect_has_noCounter():
                counter = 'none'
            # TODO: Allow only certain counters based on move values,
            # and also disable countering if self.counters is empty
            elif not self.is_player:
                logger.debug(f"{self.name_decolored}'s AI {self.AI} "
                             f'is countering "{move}"')
                counter = self.AI.analyseMoveCounter(self, move, sender)
            else:
                logger.debug(f"{self.name_decolored}'s player "
                             f'is countering "{move}"')
                counter = self.player_counter(move, sender)

        # If move counter failed
        else:
            if sender is not None:
                logger.debug(f'{self.name_decolored} cannot counter the move')
            counter = False

        logger.debug(f'{self.name_decolored} is using counter {counter!r}')

        # Counter System
        if counter == 'block':
            self.move_receive_counter_block(move, sender, sender_costs)
        elif counter == 'evade':
            self.move_receive_counter_evade(move, sender, sender_costs)
        elif counter == 'none':
            self.move_receive_counter_none(move, sender, sender_costs)
        elif counter is False:
            self.move_receive_counter_false(move, sender, sender_costs)
        else:
            raise RuntimeError(
                'During move_receive while countering, '
                f'an unknown counter was given: {counter!r}')

    def move_receive_counter_none(self, move, sender, sender_costs):
        # If move is critical
        if random.uniform(1, 100) <= self.gen_chance(move, 'critical'):
            logger.debug(f'"{move}" against {self.name_decolored} '
                         'is a critical')
            values = self.gen_critical_values(move)
            self.print_move(sender, move, values, sender_costs,
                            'criticalMessage')
            self.apply_values(values)
            # Apply status effects
            info = ('none', 'critical')
            self.receive_status_effects_from_move(move, info, sender)
            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.name_decolored} is normal')
            values = self.gen_values(move)
            self.print_move(sender, move, values, sender_costs)
            self.apply_values(values)

            info = ('none', 'normal')
            self.receive_status_effects_from_move(move, info, sender)

            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)

    def move_receive_counter_false(self, move, sender, sender_costs):
        # If move is critical
        if random.uniform(1, 100) <= self.gen_chance(move, 'critical'):
            logger.debug(f'"{move}" against {self.name_decolored} '
                         'is a fast critical')
            values = self.gen_critical_values(move)
            self.print_move(sender, move, values, sender_costs,
                            'fastCriticalMessage')
            self.apply_values(values)

            info = ('fast', 'critical')
            self.receive_status_effects_from_move(move, info, sender)

            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)
        else:
            logger.debug(f'"{move}" against {self.name_decolored} is fast')
            values = self.gen_values(move)
            self.print_move(sender, move, values, sender_costs,
                            'fastMessage')
            self.apply_values(values)

            info = ('fast', 'normal')
            self.receive_status_effects_from_move(move, info, sender)

            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)

    def move_receive_counter_block(self, move, sender, sender_costs):
        # If move is blocked
        if random.uniform(1, 100) <= self.gen_chance(move, 'block'):
            logger.debug(f'"{move}" against {self.name_decolored} is blocked')
            values = self.gen_counter_values(move, 'block')
            self.print_move(sender, move, values, sender_costs,
                            'blockMessage')
            self.apply_values(values)

            info = ('block', 'success')
            self.receive_status_effects_from_move(move, info, sender)

            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed block
            if random.uniform(1, 100) <= self.gen_chance(move, 'critical'):
                logger.debug(f'"{move}" against {self.name_decolored} '
                             'is failed block critical')
                values = self.gen_counter_fail_critical_values(move, 'block')
                self.print_move(sender, move, values, sender_costs,
                                'blockFailCriticalMessage')
                self.apply_values(values)

                info = ('block', 'critical')
                self.receive_status_effects_from_move(move, info, sender)

                if not self.is_player:
                    self.AI.analyse_move_receive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.name_decolored} '
                             'is failed block')
                values = self.gen_counter_fail_values(move, 'block')
                self.print_move(sender, move, values, sender_costs,
                                'blockFailMessage')
                self.apply_values(values)

                info = ('block', 'fail')
                self.receive_status_effects_from_move(move, info, sender)

                if not self.is_player:
                    self.AI.analyse_move_receive(
                        self, move, sender, info=info)

    def move_receive_counter_evade(self, move, sender, sender_costs):
        # If move is evaded
        if random.uniform(1, 100) <= self.gen_chance(move, 'evade'):
            logger.debug(f'"{move}" against {self.name_decolored} is evaded')
            values = self.gen_counter_values(move, 'evade')
            self.print_move(sender, move, values, sender_costs,
                            'evadeMessage')
            self.apply_values(values)

            info = ('evade', 'success')
            self.receive_status_effects_from_move(move, info, sender)

            if not self.is_player:
                self.AI.analyse_move_receive(
                    self, move, sender, info=info)
        else:
            # If move is critical after failed evade
            if random.uniform(1, 100) <= self.gen_chance(move, 'critical'):
                logger.debug(f'"{move}" against {self.name_decolored} '
                             'is failed evade critical')
                values = self.gen_counter_fail_critical_values(move, 'evade')
                self.print_move(sender, move, values, sender_costs,
                                'evadeFailCriticalMessage')
                self.apply_values(values)

                info = ('evade', 'critical')
                self.receive_status_effects_from_move(move, info, sender)

                if not self.is_player:
                    self.AI.analyse_move_receive(
                        self, move, sender, info=info)
            else:
                logger.debug(f'"{move}" against {self.name_decolored} '
                             'is failed evade')
                values = self.gen_counter_fail_values(move, 'evade')
                self.print_move(sender, move, values, sender_costs,
                                'evadeFailMessage')
                self.apply_values(values)

                info = ('evade', 'critical')
                self.receive_status_effects_from_move(move, info, sender)

                if not self.is_player:
                    self.AI.analyse_move_receive(
                        self, move, sender, info=info)

    def player_counter(self, move, sender):
        """Obtains a counter from the player.
Note: No counter shell has been created so the placeholder interface code
below is being used."""
        print_color(f'{INDENT}\
{sender} is using {move}, but {self} is able to use a counter!')

        countersMessage = self.string_counters()

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

            search = self.find_counter(
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

    def player_move(self, target, cmdqueue=None):
        """Obtains a move from the player."""
        logger.debug(f"{self.name_decolored} is moving")
        if cmdqueue is None:
            cmdqueue = []
            moveCMD = self.interface_shell_dict.get('moveCMD')
            if moveCMD is not None:
                cmdqueue.append(moveCMD)
        namespace = dict()

        # Get user interaction and use the changes in `namespace`
        # to know which move to use next
        interface.FighterBattleMainShell(
            self, target, namespace, cmdqueue
        ).cmdloop()
        print()

        self.interface_shell_dict['moveCMD'] = namespace['newMoveCMD']

        return namespace['shell_result']

    def print_insufficient_cost(self, move, stat, cost):
        """Print an insufficient cost message for a stat.

        If the insufficientStatMessage key is available in the move,
        that message is used. Otherwise, uses a generic message.

        """
        stat_obj = self.stats[stat]
        namespace = {
            'self': self,
            'move': move,
            'cost': cost,
            'int_short': stat_obj.int_short,
            'int_full': stat_obj.int_full,
            'ext_short': stat_obj.ext_short,
            'ext_full': stat_obj.ext_full
        }

        message = move.values.get('insufficientStatMessage')

        if message is None:
            message = ('{self} tried using {move} but the {ext_full} cost '
                       'was {-cost}.')

        print_color(message, namespace=namespace)

    def print_move(self, sender, move, values=None, costs=None,
                   message='moveMessage', **kwargs):
        """Formats a move's message and prints it.

        This method should be called by the target.

        An environment is provided to be used for formatting:
            sender: The Fighter sending the move.
            target: The Fighter receiving the move.
            move: The Move being used.
            **self.stats: The target's Stat objects referenced using their
                `int_short`.
            **{stat}Value: The values of the move applied to target.
            **{stat}Cost: The costs of the move for sender.

        Args:
            sender (Fighter): The sender of the move.
            move (Move): The move being applied onto self.
            values (Optional[Dict[str, int]]): The values that `move`
            applied onto the Fighter.
            If not supplied, defaults to 0 for each {stat}Value.
            costs (Optional[Dict[str, int]]): The costs that sender applied
                to themselves.
                If not supplied, defaults to 0 for each {stat}Cost.
            message (str): The message in Move to print.
            **kwargs: Keyword arguments to pass into `print_color`.

        """
        namespace = {'sender': sender, 'target': self, 'move': move}

        for stat, stat_obj in self.stats.items():
            namespace[stat] = stat_obj

            value = f'{stat}Value'
            cost = f'{stat}Cost'
            if values is not None:
                namespace[value] = values.get(stat, 0)
            else:
                namespace[value] = 0
            if costs is not None:
                namespace[cost] = costs.get(stat, 0)
            else:
                namespace[cost] = 0

        print_color(move[message], namespace=namespace, **kwargs)

    def print_status_effect(self, effect, values=None, message='applyMessage',
                            **kwargs):
        """Formats a status effect's message and prints it.

        An environment is provided to be used for formatting:
            self: The Fighter receiving the effect.
            effect: The StatusEffect being applied.
            **self.stats: The Fighter's Stat objects.
            **{stat}Value: The value applied to each stat by the status effect.

        Args:
            effect (StatusEffect): The status effect using this.
            message (str): The message in StatusEffect to print.
            values (Optional[Dict[str, int]]): The values that `effect`
                applied onto the Fighter. If not supplied, defaults to
                0 for each {stat}Value.
            **kwargs: Keyword arguments to pass into `print_color`.
        """
        if message in effect:
            namespace = {'self': self, 'effect': effect}
            for stat, stat_obj in self.stats.items():
                namespace[stat] = stat_obj

                value = f'{stat}Value'
                if values is not None:
                    namespace[value] = values.get(stat, 0)
                else:
                    namespace[value] = 0

            print_color(effect[message], namespace=namespace, **kwargs)

    def print_status_effect_messages(self, messages, print_delay=0):
        for effect, message, values in messages:
            self.print_status_effect(effect, values, message, end=None)
            util.pause(print_delay)

    def receive_status_effect(self, effect, stackDuration=True):
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
            self.print_status_effect(effect, None, 'receiveMessage')

    def receive_status_effects_from_move(self, move, info=None, sender=None):
        logger.debug(f'{self.name_decolored} receiving effects from {move}')

        def apply_effect(target, effect):
            logger.debug(f'Applying effect {effect}')

            def chance_to_apply(chance):
                result = (
                    random.uniform(1, 100) <= chance
                    * self.battle_env.base_status_effects_chance_percent
                    / 100
                )
                if result:
                    target.receive_status_effect(effect.copy())
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
                    for counter in self.all_counters:
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

    def string_counters(self):
        """Return a string showing the available counters."""
        return ', '.join([str(c) for c in self.counters.values()])

    def string_moves(self, **kwargs):
        """Return a string showing the available moves."""
        return ', '.join(
            [str(move) for move in self.available_moves(**kwargs)]
        )

    def update_stat(self, stat):
        value = getattr(self, f'{stat}_rate')

        value *= getattr(self.battle_env, f'{stat}_rate_percent', 100) / 100

        value *= self.battle_env.regen_rate_percent / 100

        value = round(value)

        setattr(self, stat, getattr(self, stat) + value)

    def update_stats(self, stats=None):
        """Calls self.update_stat for each stat the Fighter has."""
        if stats is None:
            stats = self.stats
        for stat in stats:
            # Update stat
            if not hasattr(self, stat):
                raise ValueError(f'No property exists for {stat} in '
                                 f'{self.name_decolored} (Stats: {stats})')
            self.update_stat(stat)

    def update_status_effect_durations(self):
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
                    messages.append((effects[i], 'wearoffMessage', None))
                del effects[i]
            else:
                effects[i]['duration'] -= 1
                i += 1

        return messages

    def update_status_effect_values(self):
        """Apply status effect values."""
        messages = []

        for effect in self.status_effects:
            values = {}
            for stat, stat_info in self.stats.items():
                key = f'{stat}Value'

                if key not in effect:
                    continue

                statConstant = stat_info.int_full

                value = Bound.call_random(effect[key])

                value *= (
                    self.battle_env.base_values_multiplier_percent / 100
                )

                value *= getattr(
                    self.battle_env,
                    f'base_value_{statConstant}_multiplier_percent',
                    100
                ) / 100

                value = round(value)

                values.setdefault(stat, 0)
                values[stat] += value

            self.apply_values(values)

            if 'applyMessage' in effect:
                messages.append((effect, 'applyMessage', values))

        return messages

    def use_item_requirements(self, move_or_combination=None,
                              return_string=True):
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
            combination = self.available_items_in_move(
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
            invItem = self.find_item({'name': itemDict['name']})

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
                            f'{used:,} {name}{plural(used)} used '
                            f'({newCount:,} left)'
                        )
                    )
                else:
                    strings.append(format_color(f'{name} used'))

        if return_string:
            return '\n'.join(strings)
