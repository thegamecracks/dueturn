import pprint
import random

from src.engine import fighter_ai


class MissileAI(fighter_ai.FighterAIDummy):
    DEFAULT_DATA = {'cache': {}}

    def get_track(self, user):
        """Get a track move either from the user or cache."""
        cache = self.data['cache']
        user_cache = cache.get(id(user))

        if user_cache is not None:
            track = user_cache.get('move_track')

            if track is not None:
                return track

        track = user.find_move({'name': 'Track'}, raiseIfFail=True)

        if user_cache is None:
            cache[id(user)] = {'move_track': track}
        else:
            cache[id(user)]['move_track'] = track

        return track

    def analyseMove(self, user, target):
        return self.get_track(user)


class JetAI(fighter_ai.FighterAIDummy):
    DEFAULT_DATA = {'planned_attack': None,
                    'cache': {}}

    def get_lockon(self, user):
        """Get a lockon move either from the user or cache."""
        cache = self.data['cache']
        user_cache = cache.get(id(user))

        if user_cache is not None:
            lockon = user_cache.get('move_lockon')

            if lockon is not None:
                return lockon

        lockon = user.find_move({'name': 'Aim'}, raiseIfFail=True)

        if user_cache is None:
            cache[id(user)] = {'move_lockon': lockon}
        else:
            cache[id(user)]['move_lockon'] = lockon

        return lockon

    def get_missiles(self, user, available_only=True):
        attacks = []

        for move in user.moves:
            if 'missile_type' in move:
                if available_only:
                    if user.available_items_in_move(move):
                        attacks.append(move)
                else:
                    attacks.append(move)

        return attacks

    def analyseMove(self, user, target):
        # Get the planned missile being used
        attack = self.data['planned_attack']

        if attack is None or not user.has_move(attack):
            missiles = self.get_missiles(user)
            if missiles:
                attack = random.choice(missiles)
            else:
                # COMBAK: No missiles left; there's no retreat
                # option so just pretend to fire missiles
                missiles = self.get_missiles(user, available_only=False)
                return random.choice(missiles)
            self.data['planned_attack'] = attack

        required_lockon = -attack['loCost']

        if user.lo >= required_lockon:
            # Ready to fire missile
            self.data['planned_attack'] = None
            return attack
        # Continue gaining a lock
        return self.get_lockon(user)


class JetEvadingAI(fighter_ai.FighterAIDummy):
    DEFAULT_DATA = {
        'CM_to_use': None,
        'CM_last_used': None,
        'CM_last_missile_id': None,
        'CM_last_missile_error': 0,
        'cache': {}
    }

    def get_evade_move(self, user):
        """Get an evade move either from the user or cache."""
        cache = self.data['cache']
        user_cache = cache.get(id(user))

        if user_cache is not None:
            evade = user_cache.get('move_evade')

            if evade is not None:
                return evade

        evade = user.find_move({'name': 'Evade'}, raiseIfFail=True)

        if user_cache is None:
            cache[id(user)] = {'move_evade': evade}
        else:
            cache[id(user)]['move_evade'] = evade

        return evade

    def get_countermeasures(self, user):
        moves = []

        for move in user.moves:
            if 'flCost' in move or 'chCost' in move:
                moves.append(move)

        return moves

    def analyseMove(self, user, target):
        if id(target) == self.data['CM_last_missile_id']:
            # Calculate change in error from previous attempt
            # to know if the countermeasures were effective
            error_change = (
                target.er - self.data['CM_last_missile_error']
            )
        else:
            # New missile fighter; clear previous data
            self.data['CM_to_use'] = None
            self.data['CM_last_missile_id'] = id(target)
            self.data['CM_last_missile_error'] = 0
            error_change = 0

        effectiveness = error_change > 0

        # If there's a known effective countermeasure, use it
        last_used = self.data['CM_last_used']
        if last_used is not None and effectiveness:
            return last_used

        countermeasures = self.data['CM_to_use']

        if countermeasures is None:
            # First missile being received; get available CMs
            countermeasures = self.get_countermeasures(user)
        elif not len(countermeasures):
            # None of the countermeasures were effective; evade
            return self.get_evade_move(user)

        # Pick a random usable countermeasure that wasn't used before
        selected_countermeasure = countermeasures.pop(
            random.randrange(0, len(countermeasures)))

        # Check usability and select another countermeasure if unusable
        while len(countermeasures):
            if self.analyseMoveCostBoolean(user, selected_countermeasure):
                break

            selected_countermeasure = countermeasures.pop(
                random.randrange(0, len(countermeasures)))
        else:
            if not self.analyseMoveCostBoolean(user, selected_countermeasure):
                # No more countermeasures left; evade
                return self.get_evade_move(user)

        self.data['CM_to_use'] = countermeasures
        self.data['CM_last_used'] = selected_countermeasure
        # Record missile error to see after CM usage if it increased error
        self.data['CM_last_missile_error'] = target.er

        # Countermeasure works; use it
        return selected_countermeasure
