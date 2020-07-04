import random


class Cell:
    """A room inside a GridMap.

    Args:
        parent_map (GridMap): The map the cell is located inside.
        y
        x (int): The coordinate of the cell in the map.
        paths (Optional[List[str]]): A list of cardinal directions
            showing where the cell is connected to.
        objects (Optional[dict]): A dictionary of objects inside the cell.

    """

    def __init__(self, parent_map, y, x, *, paths=None, objects=None):
        self.y = y
        self.x = x
        self.parent_map = parent_map

        self.paths = []
        if paths is not None:
            for p in paths:
                p = p.upper()
                self.paths.append(p)
        self.sync_paths()

        if objects is None:
            self.objects = {}
        else:
            self.objects = objects

    def move_object(self, key, other_y, other_x, *, copy=False):
        """Move an object to another cell.

        Args:
            key (str): The key of the object to move.
            new_y
            new_x (int): The coordinates of the other cell.
            copy (bool): If True, does not delete key from self.

        """
        if key in self.objects:
            # Get other cell
            other = self.parent_map[other_y][other_x]

            if isinstance(other, Cell):
                if key not in other.objects:
                    # Transfer object
                    obj = self.objects[key]
                    if not copy:
                        del self.objects[key]
                    other.objects[key] = obj
                else:
                    raise KeyError(
                        f'{key!r} already exists in {other_y}, {other_x}')
            else:
                raise IndexError(f'{other_y}, {other_x} is not a Cell')
        else:
            raise KeyError(f'{key!r} does not exist in {self.y}, {self.x}')

    def move_object_direction(self, key, direction, *, copy=False):
        """Move an object to another cell referred by a vector or cardinal."""
        # Copy code from `move_object` to avoid double-checking
        # the key and cell
        if key in self.objects:
            # Calculate other coordinates
            if isinstance(direction, str):
                vy, vx = cardinal_to_vector(direction)
            else:
                vy, vx = direction
            other_y, other_x = self.y + vy, self.x + vx

            # Get other cell
            other = self.parent_map[other_y][other_x]

            if isinstance(other, Cell):
                if key not in other.objects:
                    # Transfer object
                    obj = self.objects[key]
                    if not copy:
                        del self.objects[key]
                    other.objects[key] = obj
                else:
                    raise KeyError(
                        f'{key!r} already exists in {other_y}, {other_x}')
            else:
                raise IndexError(f'{other_y}, {other_x} is not a Cell')
        else:
            raise KeyError(f'{key!r} does not exist in {self.y}, {self.x}')

    def sync_paths(self, sync_broken_neighbours=False):
        """Create corresponding paths to cells connected to this cell.

        NOTE: Running with the `sync_broken_neighbours` flag has not been
            tested and may result in a hanging program.

        Args:
            sync_broken_neighbours (bool): If the cell has a path to
                a neighbour but the neighbour is missing the corresponding
                path, then call the neighbour's `sync_paths` method.
                Will also make the neighbour do the same to its neighbours,
                allowing the fix to spread.

        """
        # Loop through vectors for surrounding cells
        for y in range(-1, 2):
            for x in range(-1, 2):
                if y == 0 and x == 0:
                    # Own cell
                    continue

                # Get neighbour if it exists
                try:
                    neighbour = self.parent_map[self.y + y][self.x + x]
                except IndexError:
                    continue

                if isinstance(neighbour, Cell):
                    connected_path_self = vector_to_cardinal(y, x)
                    connected_path_other = vector_to_cardinal(-y, -x)

                    self_connected = connected_path_self in self.paths
                    neighbour_connected = \
                        connected_path_other in neighbour.paths
                    if self_connected:
                        # Connected to neighbour; check them
                        if neighbour_connected:
                            # Paths are intact
                            continue
                        else:
                            # Neighbour missing path
                            neighbour.paths.append(connected_path_other)
                            if sync_broken_neighbours:
                                # Sync neighbour's paths as well
                                neighbour.sync_paths(
                                    sync_broken_neighbours=True)
                    elif neighbour_connected:
                        # Self missing path
                        self.paths.append(connected_path_self)


class GridMap:
    """A 2D map."""

    def __init__(self, y_size, x_size):
        self.grid = [[None] * x_size for _ in range(y_size)]

    def __getitem__(self, index):
        return self.grid[index]

    def __len__(self):
        return len(self.grid)

    def connect_cell(self, y, x, path):
        """Connect two cells with a path.

        `path` can either be a cardinal direction (str) or a vector (list).

        """
        is_vector = isinstance(path, (tuple, list))
        if isinstance(path, str):
            cardinal = path
        elif is_vector:
            cardinal = vector_to_cardinal(*path)
        else:
            raise TypeError(f'unknown path type {type(path)}')

        vy, vx = path if is_vector else cardinal_to_vector(path)
        end_y, end_x = y + vy, x + vx
        if self.verify_path(y, x, cardinal):
            # Valid path; connect both
            start = self[y][x]
            end = self[end_y][end_x]
            cardinal_reverse = reverse_cardinal(cardinal)
            if cardinal not in start.paths:
                start.paths.append(cardinal)
            if cardinal_reverse not in end.paths:
                end.paths.append(cardinal_reverse)
        else:
            raise ValueError('cannot connect {y}, {x} and {end_y}, {end_x}')

    def create_cell(self, y, x, *args, **kwargs):
        """Create a cell at a given position."""
        self[y][x] = Cell(self, y, x, *args, **kwargs)

    @classmethod
    def from_json(cls, file):
        """Load a map from json."""

    def get_all_squares(self, *, Cells_only=False):
        """Return an iterator of all squares in the map with their coordinates.

        Args:
            Cells_only (bool): Return only squares that contain Cells.

        """
        for y in range(len(self)):
            for x in range(len(self[0])):
                cell = self[y][x]

                if Cells_only and not isinstance(cell, Cell):
                    continue

                yield cell, y, x

    def render(self, max_y, max_x, markers=None, fallback_compact=True):
        """Render the map.

        Args:
            max_y
            max_x (int):
                The maximum acceptable render size it can be.
                If the normal render is too large, it will try using
                compact render. If it is still too large, will raise
                a RuntimeError.
            markers (Optional[Dict[Tuple[int, int], str]]):
                An optional list of markers to place on the grid.
                The string must be one character.
            fallback_compact (bool): Allow compact rendering to be used
                if not within maximum limits.

        """
        # Calculate render size and check if it is below limits
        y, x = len(self), len(self[0])
        size_y = y * 3 + y - 1
        if size_y > max_y:
            if fallback_compact:
                return self.render_compact(max_y, max_x, markers)
            else:
                # RuntimeError is too generic; suggest custom exception
                raise RuntimeError(
                    f'y-axis size ({size_y}) exceeds max ({max_y})')
        size_x = x * 3 + x - 1
        if size_x > max_x:
            if fallback_compact:
                return self.render_compact(max_y, max_x, markers)
            else:
                # RuntimeError is too generic; suggest custom exception
                raise RuntimeError(
                    f'x-axis size ({size_x}) exceeds max ({max_x})')

        if markers is None:
            markers = {}

        # Create render
        lines = []
        # ry, rx = render y/x
        for ry in range(size_y):
            y_part = ry % 4
            y_grid = ry // 4
            line = []
            if y_part == 0:
                # Top
                for cell in self[y_grid]:
                    line.append('--- ' if isinstance(cell, Cell) else '    ')
            elif y_part == 1:
                # Middle
                for x_grid, cell in enumerate(self[y_grid]):
                    if isinstance(cell, Cell):
                        line.append('|')
                        marker = markers.get((y_grid, x_grid), ' ')
                        if len(marker) <= 1:
                            line.append(marker)
                        else:
                            raise ValueError(
                                f'marker {marker} for pos {y}, {x} '
                                'must be a single char')
                        if x_grid + 1 >= len(self[y_grid]):
                            # Right of the map; no eastern paths
                            line.append('|')
                        else:
                            cell_E = self[y_grid][x_grid + 1]
                            if (
                                    'E' in cell.paths
                                    or isinstance(cell_E, Cell)
                                    and 'W' in cell_E.paths
                                    ):
                                line.append('|-')
                            else:
                                line.append('| ')
                    else:
                        line.append('    ')
            elif y_part == 2:
                # Bottom
                for cell in self[y_grid]:
                    line.append('--- ' if isinstance(cell, Cell) else '    ')
            elif y_part == 3:
                # Bottom gap
                # Check if not bottom of map
                if y_grid + 1 < len(self):
                    for x_grid, cell in enumerate(self[y_grid]):
                        if isinstance(cell, Cell):
                            # Southern path
                            line.append(' | ' if 'S' in cell.paths else '   ')
                            if x_grid + 1 >= len(self[y_grid]):
                                # Right of the map; no diagonals
                                line.append(' ')
                                break
                            else:
                                # Southeastern paths
                                # Consider paths of surrounding cells
                                cell_S = self[y_grid + 1][x_grid]
                                cell_SE = self[y_grid + 1][x_grid + 1]
                                cell_E = self[y_grid][x_grid + 1]
                                back_slash = (
                                    'SE' in cell.paths
                                    or isinstance(cell_SE, Cell)
                                    and 'NW' in cell_SE.paths
                                )
                                forward_slash = (
                                    isinstance(cell_S, Cell)
                                    and 'NE' in cell_S.paths
                                    or isinstance(cell_E, Cell)
                                    and 'SW' in cell_E.paths
                                )
                                if forward_slash and back_slash:
                                    line.append('X')
                                elif forward_slash:
                                    line.append('/')
                                elif back_slash:
                                    line.append('\\')
                                else:
                                    line.append(' ')
                        else:
                            line.append('    ')

            line = ''.join(line)
            lines.append(line)

        return '\n'.join(lines)

    def render_compact(self, max_y, max_x, markers=None):
        """Render the map in a compact style."""
        # Calculate render size and check if it is below limits
        y, x = len(self), len(self[0])
        size_y = y + y - 1
        if size_y > max_y:
            # RuntimeError is too generic; suggest custom exception
            raise RuntimeError(
                f'y-axis size ({size_y}) exceeds max ({max_y})')
        size_x = x + x - 1
        if size_x > max_x:
            # RuntimeError is too generic; suggest custom exception
            raise RuntimeError(
                f'x-axis size ({size_x}) exceeds max ({max_x})')

        if markers is None:
            markers = {}

        # Create render
        lines = []
        # ry, rx = render y/x
        for ry in range(size_y):
            y_part = ry % 2
            y_grid = ry // 2
            line = []
            if y_part == 0:
                # Cell
                for x_grid, cell in enumerate(self[y_grid]):
                    if isinstance(cell, Cell):  # □▪▫
                        marker = markers.get((y_grid, x_grid), '▫')
                        if len(marker) <= 1:
                            line.append(marker)
                        else:
                            raise ValueError(
                                f'marker {marker} for pos {y}, {x} '
                                'must be a single char')
                        # Check for right path if not at edge of map
                        if x_grid + 1 < len(self[y_grid]):
                            cell_E = self[y_grid][x_grid + 1]
                            if (
                                    'E' in cell.paths
                                    or isinstance(cell_E, Cell)
                                    and 'W' in cell_E.paths
                                    ):
                                line.append('-')
                            else:
                                line.append(' ')
                    else:
                        line.append('  ')
            elif y_part == 1:
                # Bottom gap
                # Check if not bottom of map
                if y_grid + 1 < len(self):
                    for x_grid, cell in enumerate(self[y_grid]):
                        if isinstance(cell, Cell):
                            # Southern path
                            line.append('|' if 'S' in cell.paths else ' ')
                            if x_grid + 1 >= len(self[y_grid]):
                                # Right of the map; no diagonals
                                line.append(' ')
                                break
                            else:
                                # Southeastern paths
                                # Consider paths of surrounding cells
                                cell_S = self[y_grid + 1][x_grid]
                                cell_SE = self[y_grid + 1][x_grid + 1]
                                cell_E = self[y_grid][x_grid + 1]
                                back_slash = (
                                    'SE' in cell.paths
                                    or isinstance(cell_SE, Cell)
                                    and 'NW' in cell_SE.paths
                                )
                                forward_slash = (
                                    isinstance(cell_S, Cell)
                                    and 'NE' in cell_S.paths
                                    or isinstance(cell_E, Cell)
                                    and 'SW' in cell_E.paths
                                )
                                if forward_slash and back_slash:
                                    line.append('X')
                                elif forward_slash:
                                    line.append('/')
                                elif back_slash:
                                    line.append('\\')
                                else:
                                    line.append(' ')
                        else:
                            line.append('  ')

            line = ''.join(line)
            lines.append(line)

        return '\n'.join(lines)

    def verify_path(self, y, x, path, raise_out_of_bounds=True):
        """Check if a path connects two Cells."""
        if not isinstance(self[y][x], Cell):
            return False

        vy, vx = cardinal_to_vector(path)

        try:
            other = self[y + vy][x + vx]
        except IndexError:
            if raise_out_of_bounds:
                raise ValueError('path {c!r} not valid for pos {y}, {x}')
            else:
                return False
        return isinstance(other, Cell)


def cardinal_to_vector(direction):
    """Return a vector for a given cardinal direction.

    Directions:
        N
        NE
        E
        SE
        S
        SW
        W
        NW

    Returns:
        List[int]

    """
    if isinstance(direction, str):
        if 1 <= len(direction) <= 2:
            direction = direction.upper()
            vector = [0, 0]

            def change_vector(index, change):
                if vector[index] == 0:
                    vector[index] += change
                else:
                    raise ValueError('two opposing cardinal directions')

            for d in ('N', 'E', 'S', 'W'):
                count = direction.count(d)
                if count == 0:
                    continue
                elif count == 1:
                    if d == 'N':
                        change_vector(0, -1)
                    elif d == 'E':
                        change_vector(1, 1)
                    elif d == 'S':
                        change_vector(0, 1)
                    elif d == 'W':
                        change_vector(1, -1)
                else:
                    raise ValueError(
                        f'expected 0-1 occurrences of {d!r}, '
                        f'received {count}')

            return vector

        else:
            raise ValueError('direction must have 1-2 cardinal letters')
    else:
        raise TypeError(f'expected type str, received {type(direction)}')


def generate_spelunky_map(y_size, x_size, only_pathed_cells=False):
    """Create a GridMap with spelunky-style paths.

    NOTE: If `only_pathed_cells`, then it should be redesigned so it
        only creates new cells in its path generation instead of
        filling the level with cells and deleting them afterwards.

    Returns:
        Tuple[GridMap, Tuple[int, int], Tuple[int, int]]:
            The level along with the start and end coordinates.

    """
    level = GridMap(y_size, x_size)

    # Select starting point on the top
    x_start = random.randint(0, x_size - 1)
    # Starting coordinates
    y = 0
    x = x_start

    # Create starting cell
    level.create_cell(y, x)

    # Pre-calculate limits
    y_size -= 1
    x_size -= 1

    # Cardinals and vectors it can take
    directions = ('E', 'S', 'W')
    vectors = {  # Pre-calculated vectors
        'E': (0, 1),
        'S': (1, 0),
        'W': (0, -1)
    }

    # Stored directions modified during generation
    cardinal = None
    backtrack_cardinal = None  # Make sure it does not backtrack

    while True:
        if cardinal == 'S':
            # Previous direction was south; no backtracking to deal with
            # because north is not an option
            cardinal = random.choice(directions)
            backtrack_cardinal = reverse_cardinal(cardinal)
        else:
            # Pick a random direction that doesn't go back on itself
            while True:
                cardinal = random.choice(directions)
                if cardinal != backtrack_cardinal:
                    break
            backtrack_cardinal = reverse_cardinal(cardinal)

        if x == 0 and cardinal == 'W' or x == x_size and cardinal == 'E':
            # Next path hit a wall; go down
            cardinal = 'S'

        if y == y_size and cardinal == 'S':
            # Downwards path hit the floor; finish
            break
        else:
            # Create new cell and connect to it
            y_new, x_new = vectors[cardinal]
            y_new += y
            x_new += x

            level.create_cell(y_new, x_new)
            level.connect_cell(y, x, cardinal)

            # Set coordinates to the new cell
            y = y_new
            x = x_new

    if not only_pathed_cells:
        # Create empty cells
        for cell, y_check, x_check in level.get_all_squares():
            if cell is None:
                level.create_cell(y_check, x_check)

    return level, (0, x_start), (y, x)


def reverse_cardinal(direction):
    """Return the cardinal direction pointing opposite of a given direction."""
    y, x = cardinal_to_vector(direction)
    return vector_to_cardinal(-y, -x)


def vector_to_cardinal(y, x):
    """Return a cardinal direction for a given vector."""
    cardinal = []
    if not -1 <= y <= 1:
        raise ValueError(f'y ({y}) must be between -1 and 1')
    elif not -1 <= x <= 1:
        raise ValueError(f'x ({x}) must be between -1 and 1')

    if y < 0:
        cardinal.append('N')
    elif y > 0:
        cardinal.append('S')
    if x < 0:
        cardinal.append('W')
    elif x > 0:
        cardinal.append('E')

    return ''.join(cardinal)


def main():

    def spelunky(only_pathed_cells=False, change_size=False):
        if change_size:
            print('Hardcoded max size of 30 chars down, 119 chars right')
            print('or a map of either 7 by 29 or compact 14 by 58')
        else:
            y, x = 4, 4

        while True:
            input()
            if change_size:
                y, x = [int(n) for n in input(
                            'y-size and x-size ("14 58"): ').split()]
            if y > 14 or x > 58:
                print('Map is too big to fit in border')
                continue
            print('\n\n\n\n\n')

            level, start, end = generate_spelunky_map(
                y, x,
                only_pathed_cells
            )

            try:
                print(level.render(
                    29, 117, markers={start: 'S', end: 'E'}))
            except RuntimeError:
                print('Failed render: too big to fit in border')

    def moving_objects(y_size, x_size):
        from math import inf as infinity

        # Create level and fill with cells
        level = GridMap(y_size, x_size)
        for _, y, x in level.get_all_squares():
            level.create_cell(y, x)

        letters = ('K', 'I', 'C', 'R')

        def convert_coordinates(s):
            return [int(n) for n in s.split(',')]

        def render():
            markers = {}

            # Find objects
            for obj in letters:
                for cell, y, x in level.get_all_squares(Cells_only=True):
                    if obj in cell.objects:
                        markers[y, x] = obj
                        break

            print(level.render_compact(
                infinity, infinity, markers), end='\n\n')

        # Create objects on corners of map
        y_size -= 1
        x_size -= 1
        level[0][0].objects[letters[0]] = True
        level[0][x_size].objects[letters[1]] = True
        level[y_size][0].objects[letters[2]] = True
        level[y_size][x_size].objects[letters[3]] = True

        print('Move objects on the map')
        print('Command examples:')
        print('move A 1,1')
        print('move 0,0 1,1')
        print('move A SE')
        print('Note: cannot move objects into other objects')
        print()

        while True:
            render()

            action = input(': ')
            action = action.split()

            try:
                if action[0] == 'move':
                    start = action[1].upper()
                    end = action[2]

                    if start in letters:
                        # Starting at object
                        for cell, y, x in level.get_all_squares(
                                Cells_only=True):
                            if start in cell.objects:
                                break
                        else:
                            print('Cannot find', start)
                            continue

                        start_y, start_x = y, x
                    elif ',' in start:
                        # Coordinates of start
                        start_y, start_x = convert_coordinates(start)

                    if ',' in end:
                        # Coordinates of end
                        end_y, end_x = convert_coordinates(end)
                    else:
                        # Probably cardinal
                        vy, vx = cardinal_to_vector(end)
                        end_y, end_x = start_y + vy, start_x + vx
            except Exception as e:
                print(type(e), e)
                continue

            # Get cells
            start = level[start_y][start_x]
            end = level[end_y][end_x]

            if start.objects:
                if not end.objects:
                    # Identify what key is being moved
                    key = next(iter(start.objects))
                    # Transfer the object
                    start.move_object(key, end_y, end_x)

                    print('Moved', key, f'to {end_y},{end_x}')
                else:
                    print(f'Cannot move object to {end_y},{end_x};')
                    print('already an object there')
            else:
                print(f'No object found in {start_y},{start_x}')

            print()

    # spelunky(True, True)
    moving_objects(4, 4)


if __name__ == '__main__':
    main()
