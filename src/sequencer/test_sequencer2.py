# Test relative import
from . import sequencer

sequence_log = None


def sequence_1():
    global sequence_log
    sequence_log = []
    sequence_log.append(1)

    return sequence_2


def sequence_2():
    global sequence_log
    sequence_log.append(2)

    return sequence_3


def sequence_3():
    global sequence_log
    sequence_log.append(3)

    return sequence_log
