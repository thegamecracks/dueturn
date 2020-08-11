from .gridmap import GridMap
from .pathfinding import uniform_cost_search


def test_uniform_cost_search():
    """Run a simple test to build a GridMap and generate a path with
    uniform_cost_search.

    Map:
        --- ---
        |S| | |
        --- ---
           \ |
        --- --- ---
        | |-| | | |
        --- --- ---
           X
        --- ---
        | | |E|
        --- ---
    """
    level = GridMap(3, 3)

    level.create_cell(0, 0)
    level.create_cell(0, 1, paths=['S'])
    level.create_cell(1, 0, paths=['E', 'SE'])
    level.create_cell(1, 1)
    level.create_cell(1, 2)
    level.create_cell(2, 0)
    level.create_cell(2, 1)

    level.connect_cell(0, 0, 'SE')
    level.connect_cell(1, 1, [1, -1])

    path = uniform_cost_search(
        gridmap=level,
        source=(0, 0),
        target=(2, 1)
    )

    assert path == [(0, 0), (1, 1), (1, 0), (2, 1)]
