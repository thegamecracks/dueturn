from . import sequencer


def test_begin_sequence():
    sequence_log = []

    def sequence_1():
        nonlocal sequence_log
        sequence_log.append(1)

        return sequence_2

    def sequence_2():
        nonlocal sequence_log
        sequence_log.append(2)

        return sequence_3

    def sequence_3():
        nonlocal sequence_log
        sequence_log.append(3)

    sequencer.begin_sequence(sequence_1)

    assert sequence_log[0] == 1
    assert sequence_log[1] == 2
    assert sequence_log[2] == 3


def test_begin_sequence_module():
    # NOTE: Absolute imports cannot be tested in standard conditions
    # because pytest sets the __package__ name to "sequencer"
    # instead of what it normally is when executing main.py,
    # which is "src.sequencer"
    sequence_log = sequencer.begin_sequence_module(
        '.test_sequencer2',
        'sequence_1'
    )

    assert sequence_log[0] == 1
    assert sequence_log[1] == 2
    assert sequence_log[2] == 3

    # Test relative import
    sequence_log = sequencer.begin_sequence_module(
        '.test_sequencer2',
        'sequence_1'
    )

    assert sequence_log[0] == 1
    assert sequence_log[1] == 2
    assert sequence_log[2] == 3
