"""Provides functions to import scenes and sequence them."""
import importlib


def begin_sequence(scene_func):
    """Begin a sequence from a scene function.

    When a sequence function returns an uncallable object,
    the sequence ends and that object is returned.

    An exception is raised if `scene_func` is not callable.

    """
    current_sequence = scene_func

    if not callable(current_sequence):
        raise TypeError('Starting sequence is uncallable: '
                        f'{current_sequence!r}')

    while callable(current_sequence):
        current_sequence = current_sequence()

    return current_sequence



def begin_sequence_module(module, scene):
    """Import a module and start off at a given scene.

    When a sequence function returns an uncallable object,
    the sequence ends and that object is returned.

    An exception is raised if getattr(module, scene) is not callable.

    Args:
        module (str): The path of the module to load, starting
            at the project directory.
            Ex. "src.sequencer.test_sequencer2"
            Ex. ".sequencer.test_sequencer2"
        scene (str): The scene function to execute.

    """
    module = importlib.import_module(
        module, package=__package__.split('.')[0])

    current_sequence = getattr(module, scene)

    if not callable(current_sequence):
        raise TypeError('Starting sequence is uncallable: '
                        f'{current_sequence!r}')

    while callable(current_sequence):
        current_sequence = current_sequence()

    return current_sequence
