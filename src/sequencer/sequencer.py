"""Provides functions to import scenes and sequence them."""


def begin_sequence(scene_func):
    """Begin a sequence from a scene function.

    The sequence ends when the scene function returns None.

    """
    current_sequence = scene_func

    while current_sequence is not None:
        current_sequence = current_sequence()



def begin_sequence_module(module, scene):
    """Import a module and start off at a given scene.

    The sequence ends when the scene function returns None.

    Args:
        module (str): The path of the module to load.
        scene (str): The scene function to execute.

    """
    try:
        module = __import__(module)
    except ImportError:
        # For now, re-raise error
        raise

    current_sequence = eval('module.' + scene)

    while current_sequence is not None:
        current_sequence = current_sequence()
