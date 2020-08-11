import collections
import heapq

from .gridmap import *


class Node:
    """A node containing its key and cost, along with optional info."""

    def __init__(self, key, cost, info=None):
        self.key = key
        self.cost = cost
        if info is None:
            self.info = {}
        else:
            self.info = info

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__, self.key, self.cost)

    def copy(self):
        return self.__class__(self.key, self.cost)

    def __eq__(self, other):
        """Test for equality by comparing keys."""
        if isinstance(other, self.__class__):
            return self.key == other.key
        return NotImplemented

    def __hash__(self):
        """Return the hash of the node.

        __hash__ must be specified since __eq__ was overrided.

        https://www.asmeurer.com/blog/posts/
            what-happens-when-you-mess-with-hashing-in-python/
        In short, two objects that are equal should have the same hash.
        Since the equality works with keys, it should hash the key.
        """
        return hash(self.key)


class NavMesh(collections.UserDict):
    """A graph structure.

    To access the real dictionary, use the "data" attribute.

    Example Initialization:
    Graph(
        (Node('A', 1), ['B', 'C']),
        (Node('B', 2), ['C', 'D']),
        (Node('C', 3), ['D', 'E']),
        (Node('D', 4), ['C', 'E']),
        (Node('E', 1), ['F']),
        (Node('F', 1), ['C'])
    )

    """

    def __init__(self, *nodes_and_keys):
        super().__init__()
        for node, keys in nodes_and_keys:
            self.data[node] = keys

    @classmethod
    def from_gridmap(cls, gridmap):
        grid = gridmap.grid
        nodes_and_keys = []

        for y in range(len(grid)):
            for x in range(len(grid[0])):
                cell = grid[y][x]
                if isinstance(cell, Cell):
                    node = Node((y, x), 1)
                    neighbours = []
                    for p in cell.paths:
                        # Convert each path into their referenced coordinates
                        vy, vx = cardinal_to_vector(p)
                        py, px = y + vy, x + vx
                        neighbours.append((py, px))

                    nodes_and_keys.append((node, neighbours))

        return cls(*nodes_and_keys)

    # def __contains__(self, key):
    #     if isinstance(key, Node):
    #         return key.key in {n.key for n in self}
    #     return key in self.data

    def __getitem__(self, key):
        if isinstance(key, Node):
            return self.data[key]
        # Search through the nodes by their key
        keys = [(k.key, v) for k, v in self.items()]
        return keys[[name for name, _ in keys].index(key)][1]

    def get_node(self, key):
        """Find a node by using its key."""
        keys = [(k.key, k) for k in self]
        return keys[[name for name, _ in keys].index(key)][1]

    def adjacent(self, x, y):
        """Return True if x is adjacent (connected) to y."""
        return y in self[x]

    def copy(self):
        """Return a deep copy of itself."""
        return self.__class__(*[(k.copy() if hasattr(k, 'copy') else k,
                                 v.copy() if hasattr(v, 'copy') else v)
                                for k, v in self.items()])

    def neighbors(self, node):
        """Return all neighbours of a node."""
        return [self.get_node(key) for key in self[node]]

    def vector_path(a, b):
        """Return the vector for two Nodes/keys."""
        a = a.name if isinstance(a, Node) else a
        b = b.name if isinstance(b, Node) else b
        
        a = [int(n) for n in a.split(', ')]
        b = [int(n) for n in b.split(', ')]

        return [b[0] - a[0], b[1] - a[1]]
        


class PriorityQueue:
    """A priority queue.

    Modified from https://github.com/marcoscastro/ucs/tree/master/source/

    Note: Tuples can be compared.
    When the first values of two tuples are the same, it will attempt comparing
    the second set of values, and so on. This is why the internal _queue stores
    items as (priority, index, item): to first pick the lowest priority, then
    the most recent index.

    """

    def __init__(self):
        self._queue = []
        self._index = 0

    def __contains__(self, key):
        for i in self._queue:
            if i[-1] == key:
                return True
        return False

    def __len__(self):
        return len(self._queue)

    def __getitem__(self, key):
        return self._queue[key]

    def push(self, item, priority):
        heapq.heappush(self._queue, [priority, self._index, item])
        self._index += 1

    def pop(self):
        """Return the smallest item."""
        return heapq.heappop(self._queue)[-1]

    def empty(self):
        """Return True if the queue is empty."""
        return len(self._queue) == 0

    def getPriority(self, item):
        """Return the priority of an item."""
        for i in self._queue:
            if i[-1] == item:
                return i[0]
        else:
            print(self._queue)
            raise ValueError(f'{item!r} is not in queue')

    def setPriority(self, item, priority):
        """Change the priority of an item."""
        for i in self._queue:
            if i[-1] == item:
                i[0] = priority
                break


def uniform_cost_search(gridmap, source, target,
                        get_cost=False, verbose=False):
    """An optimization of Dijkstra's algorithm.

    https://algorithmicthoughts.wordpress.com/2012/12/15/
        artificial-intelligence-uniform-cost-searchucs/
    
    Args:
        gridmap (GridMap): The map to pathfind.
        source (Tuple[int, int]): The coordinate of the source node.
        target (Tuple[int, int]): The coordinate of the target node.
        get_cost (bool): If True, return the cost instead of a path.
        verbose (bool): If True, print the steps taken by the algorithm.
            Note: This is not yet properly developed.

    Returns:
        List[str]: A list of coordinates as strings ('0, 0')

    """
    graph = NavMesh.from_gridmap(gridmap)

    # Verbose printing
    printV = lambda *args, **kwargs: print(*args, **kwargs) \
                                     if verbose else None

    # Convert source and target keys into nodes
    source = graph.get_node(source)
    target = graph.get_node(target)
    # Create a copy of the graph for mutating the costs
    # without touching the original graph
    graph = graph.copy()
    explored = set()
    frontier = PriorityQueue()
    # Start search with source node
    frontier.push(source, 0)

    while True:
        # If frontier is empty, no path could be found
        if frontier.empty():
            return False
        # Pick the shortest path to analyze
        node = frontier.pop()

        if node == target:
            if get_cost:
                return node.cost
            # Find the path
            path = [node]
            while 'predecessor' in node.info:
                node = node.info['predecessor']
                path.append(node)
            return [n.key for n in reversed(path)]
        # Take note of node as explored as to not search through it again
        explored.add(node)

        for n in graph.neighbors(node):
            printV(n)
            printV(explored)
            if n not in explored:
                printV('not in explored')
                # Make neighbors part of the frontier if unexplored
                if n not in frontier:
                    # Push a new node with cumulative costs
                    n.cost += node.cost
                    printV(node.key, node.cost, n.key, n.cost)
                    frontier.push(n, n.cost)
                    if not get_cost:
                        n.info['predecessor'] = node
            # Neighboring node was already seen, but the stored cost
            # can be replaced if it has discovered a lower cost
            elif n in frontier and n.cost < frontier.getPriority(n):
                frontier.setPriority(n, n.cost)
                if not get_cost:
                    n.info['predecessor'] = node


def markers_from_path(path, char):
    """Create a dictionary of markers with a `char` from a given `path`."""
    markers = {}

    for y, x in path:
        markers[y, x] = char

    return markers


def main():
    global level
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

    print(level.render(11, 11, markers={(0, 0): 'S', (2, 1): 'E'}), end='\n\n')

    path = uniform_cost_search(
        gridmap=level,
        source=(0, 0),
        target=(2, 1)
    )

    print(path)
    markers = markers_from_path(path, 'P')

    print(level.render(11, 11, markers))


if __name__ == '__main__':
    main()
