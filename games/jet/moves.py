from src import engine

Bound = engine.Bound
Move = engine.Move

player_moves = [
    Move({
        'name': 'Aim',
        'description': 'Gain a lock on your target.',

        'loCost': Bound(25, 30),

        'speed': 100,
        'fastMessage': "You gain {loCost}% {lo.ext_full} on {target}.",

        'criticalChance': 0,
        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Sidewinder',
        'description': 'Fire an AIM-9 Sidewinder '
                       '(short-range AA infrared-guided missile).',
        'itemRequired': ([{'name': 'AIM-9 Sidewinder', 'count': 1}],),

        'loCost': -55,

        'speed': 100,
        'fastMessage': "Fox two!",

        'criticalChance': 0,
        'failureChance': 0,

        # Custom data
        'missile_type': 'infrared',
        'missile_speed': 200,
        'field_of_regard': 1800,
        'track_rate': 120,
        'base_damage': 1500,
        'blast_radius': 15,
        }
    ),
    Move({
        'name': 'AMRAAM',
        'description': 'Fire an AIM-120 AMRAAM '
                       '(medium-range AA active radar-guided missile).',
        'itemRequired': ([{'name': 'AIM-120 AMRAAM', 'count': 1}],),

        'loCost': -100,

        'speed': 100,
        'fastMessage': "Fox three!",

        'criticalChance': 0,
        'failureChance': 0,

        'missile_type': 'active radar',
        'missile_speed': 200,
        'field_of_regard': 1400,
        'track_rate': 100,
        'base_damage': 1500,
        'blast_radius': 15,
        }
    ),
]

enemy_moves = [
    Move({
        'name': 'Aim',
        'description': 'Gain a lock on your target.',

        'loCost': Bound(10, 25),

        'speed': 100,
        'fastMessage': "{sender} gains {loCost}% {lo.ext_full} on {target}.",

        'criticalChance': 0,
        'failureChance': 0,
        }
    ),
    Move({
        'name': 'Archer',
        'description': 'Fire an AA-11 Archer '
                       '(short-range AA infrared-guided missile).',
        'itemRequired': ([{'name': 'AA-11 Archer', 'count': 1}],),

        'loCost': -55,

        'speed': 100,
        'fastMessage': "Missile launch detected!",

        'criticalChance': 0,
        'failureChance': 0,

        'missile_type': 'infrared',
        'missile_speed': 200,
        'field_of_regard': 1800,
        'track_rate': 120,
        'base_damage': 1500,
        'blast_radius': 15,
        }
    ),
    Move({
        'name': 'Adder',
        'description': 'Fire an AA-12 Adder '
                       '(medium-range AA active radar-guided missile).',
        'itemRequired': ([{'name': 'AA-12 Adder', 'count': 1}],),

        'loCost': -100,

        'speed': 100,
        'fastMessage': "Missile launch detected!",

        'criticalChance': 0,
        'failureChance': 0,

        'missile_type': 'active radar',
        'missile_speed': 200,
        'field_of_regard': 1400,
        'track_rate': 100,
        'base_damage': 1500,
        'blast_radius': 15,
        }
    ),
]

evading_moves = [
    Move({
        'name': 'Evade',
        'description': 'Attempt evading the missile.\n'
                       'More effective when the missile has high error.',

        'speed': 100,
        'fastMessage': "{sender} attempts evading!",

        'criticalChance': 0,
        'failureChance': 0,

        'effect': 50,
        }
    ),
    Move({
        'name': 'Flares',
        'description': 'Use flares.\n'
                       'Effective against infrared-guided missiles.',

        'flCost': -20,

        'speed': 100,
        'fastMessage': "{sender} deploys flares!",

        'criticalChance': 0,
        'failureChance': 0,

        'effect': {'infrared': 180,
                   'active radar': 10},
        }
    ),
    Move({
        'name': 'Chaff',
        'description': 'Use chaff.\n'
                       'Effective against radar-guided missiles.',

        'chCost': -20,

        'speed': 100,
        'fastMessage': "{sender} deploys chaff!",

        'criticalChance': 0,
        'failureChance': 0,

        'effect': {'infrared': 10,
                   'active radar': 180},
        }
    ),
]
missile_moves = [
    Move({
        'name': 'Track',
        'description': 'Track the target.',

        'speed': 100,
        'fastMessage': "The missile continues moving towards {target}.",

        'criticalChance': 0,
        'failureChance': 0,
        }
    ),
]
