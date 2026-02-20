import random
from enum import IntFlag
from functools import lru_cache


class Direction(IntFlag):
    """Bit flags for pipe directions."""
    NONE = 0
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8


class TileType:
    """Tile type constants."""
    BLANK = 0
    ENDPOINT = 1
    SERVER = 2
    JUNCTION = 3


class NetGameLogic:
    """
    Core game logic: grid, rotations, win condition, and tree DP solver.
    Time complexity of most methods: O(width * height).
    """

    def __init__(self, width: int = 7, height: int = 7) -> None:
        self.width = width
        self.height = height

        # UI cell size based on larger dimension
        max_dim = max(width, height)
        if max_dim <= 5:
            self.cell_size = 75
        elif max_dim <= 7:
            self.cell_size = 65
        elif max_dim <= 9:
            self.cell_size = 55
        elif max_dim <= 11:
            self.cell_size = 40
        else:
            self.cell_size = 32

        self.user_move_count = 0
        self.solving_animation_running = False
        self.initial_scrambled_grid = None

        self.grid = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.tile_types = [[TileType.BLANK for _ in range(width)] for _ in range(height)]
        self.solution = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.server_pos = (width // 2, height // 2)

        self.new_game()

    def clone_grid(self, grid):
        """Deep copy of a 2D grid."""
        return [[grid[y][x] for x in range(self.width)] for y in range(self.height)]

    def change_size(self, width: int, height: int) -> None:
        """Change grid dimensions and generate new puzzle."""
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)

        max_dim = max(width, height)
        if max_dim <= 5:
            self.cell_size = 75
        elif max_dim <= 7:
            self.cell_size = 65
        elif max_dim <= 9:
            self.cell_size = 55
        elif max_dim <= 11:
            self.cell_size = 40
        else:
            self.cell_size = 32

        self.new_game()

    def new_game(self) -> None:
        """Generate a random tree puzzle, store solution, scramble it."""
        self.user_move_count = 0
        self.solving_animation_running = False

        self.grid = [[Direction.NONE for _ in range(self.width)] for _ in range(self.height)]
        self.tile_types = [[TileType.BLANK for _ in range(self.width)] for _ in range(self.height)]
        self.solution = [[Direction.NONE for _ in range(self.width)] for _ in range(self.height)]

        sx, sy = self.server_pos
        self.tile_types[sy][sx] = TileType.SERVER

        visited = set([(sx, sy)])
        # (dx, dy, out direction, in direction)
        directions = [
            (0, -1, Direction.UP, Direction.DOWN),
            (1, 0, Direction.RIGHT, Direction.LEFT),
            (0, 1, Direction.DOWN, Direction.UP),
            (-1, 0, Direction.LEFT, Direction.RIGHT)
        ]

        random.shuffle(directions)
        initial_branches = random.choice([2, 3])
        stack = []

        # Connect server to neighbours
        for dx, dy, d, o in directions:
            if initial_branches == 0:
                break
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                self.grid[sy][sx] |= d
                self.grid[ny][nx] |= o
                visited.add((nx, ny))
                stack.append((nx, ny))
                initial_branches -= 1

        # DFS to build tree
        while stack:
            x, y = stack[-1]
            neighbours = []
            for dx, dy, direction, opposite in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited):
                    neighbours.append((nx, ny, direction, opposite))
            if neighbours:
                nx, ny, direction, opposite = random.choice(neighbours)
                self.grid[y][x] |= direction
                self.grid[ny][nx] |= opposite
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        # Store solution and classify tile types
        for y in range(self.height):
            for x in range(self.width):
                self.solution[y][x] = self.grid[y][x]

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == self.server_pos:
                    continue
                if self.grid[y][x] != Direction.NONE:
                    conn_count = bin(self.grid[y][x]).count('1')
                    self.tile_types[y][x] = TileType.ENDPOINT if conn_count == 1 else TileType.JUNCTION

        # Scramble non‑server tiles
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) != self.server_pos and self.grid[y][x] != Direction.NONE:
                    rotations = random.randint(1, 3)
                    for _ in range(rotations):
                        self.grid[y][x] = self.rotate_direction(self.grid[y][x])

        self.initial_scrambled_grid = self.clone_grid(self.grid)

    def restart_game(self) -> None:
        """Restore initial scrambled grid."""
        if not self.initial_scrambled_grid:
            return
        self.user_move_count = 0
        self.solving_animation_running = False
        self.grid = self.clone_grid(self.initial_scrambled_grid)

    def solve_with_tree_dp(self, start_grid):
        """
        Return minimal rotation sequence (cw/ccw moves) to reach solution.
        Uses tree DP; time O(N) with memoisation.
        """
        # Build adjacency list from solution graph
        adj = {(x, y): [] for y in range(self.height) for x in range(self.width)}

        for y in range(self.height):
            for x in range(self.width):
                if self.solution[y][x] == Direction.NONE:
                    continue

                for dx, dy, d, o in [
                    (0, -1, Direction.UP, Direction.DOWN),
                    (1, 0, Direction.RIGHT, Direction.LEFT),
                    (0, 1, Direction.DOWN, Direction.UP),
                    (-1, 0, Direction.LEFT, Direction.RIGHT)
                ]:
                    if self.solution[y][x] & d:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            adj[(x, y)].append((nx, ny))

        root = self.server_pos

        @lru_cache(maxsize=None)
        def solve_subtree(node, parent):
            """
            Return (min_cost, best_cw_rotations) for subtree rooted at node.
            min_cost = minimal rotations for node + all children.
            best_cw_rotations = clockwise rotations applied to node (0‑3).
            """
            x, y = node
            current = start_grid[y][x]
            target = self.solution[y][x]

            # All orientations after 0..3 cw rotations
            rotations = []
            state = current
            for i in range(4):
                rotations.append((state, i))
                state = self.rotate_direction(state)

            best_cost = float('inf')
            best_rotation = 0

            for state, rot_cw in rotations:
                if state != target:
                    continue
                rot_ccw = (4 - rot_cw) % 4
                tile_cost = min(rot_cw, rot_ccw)
                total = tile_cost
                for child in adj[node]:
                    if child == parent:
                        continue
                    child_cost, _ = solve_subtree(child, node)
                    total += child_cost
                if total < best_cost:
                    best_cost = total
                    best_rotation = rot_cw

            return best_cost, best_rotation

        solve_subtree(root, None)  # fill cache

        moves = []

        def collect_moves(node, parent):
            _, rot_cw = solve_subtree(node, parent)
            x, y = node
            current = start_grid[y][x]
            target = self.solution[y][x]

            if current != target:
                # Count cw steps to target
                cw = current
                cw_cnt = 0
                while cw != target and cw_cnt < 4:
                    cw = self.rotate_direction(cw)
                    cw_cnt += 1
                # Count ccw steps to target
                ccw = current
                ccw_cnt = 0
                while ccw != target and ccw_cnt < 4:
                    ccw = self.rotate_direction_ccw(ccw)
                    ccw_cnt += 1
                direction = 'cw' if cw_cnt <= ccw_cnt else 'ccw'
                rotations = cw_cnt if direction == 'cw' else ccw_cnt
                moves.extend([(x, y, direction)] * rotations)

            for child in adj[node]:
                if child != parent:
                    collect_moves(child, node)

        collect_moves(root, None)
        return moves

    def rotate_direction(self, direction: Direction) -> Direction:
        """Rotate 90° clockwise."""
        result = Direction.NONE
        if direction & Direction.UP:    result |= Direction.RIGHT
        if direction & Direction.RIGHT: result |= Direction.DOWN
        if direction & Direction.DOWN:  result |= Direction.LEFT
        if direction & Direction.LEFT:  result |= Direction.UP
        return result

    def rotate_direction_ccw(self, direction: Direction) -> Direction:
        """Rotate 90° counter‑clockwise."""
        result = Direction.NONE
        if direction & Direction.UP:    result |= Direction.LEFT
        if direction & Direction.LEFT:  result |= Direction.DOWN
        if direction & Direction.DOWN:  result |= Direction.RIGHT
        if direction & Direction.RIGHT: result |= Direction.UP
        return result

    def left_rotate_at(self, x: int, y: int) -> bool:
        """User clockwise rotation; returns True if tile exists."""
        if self.grid[y][x] == Direction.NONE:
            return False
        self.grid[y][x] = self.rotate_direction(self.grid[y][x])
        self.user_move_count += 1
        return True

    def right_rotate_at(self, x: int, y: int) -> bool:
        """User counter‑clockwise rotation."""
        if self.grid[y][x] == Direction.NONE:
            return False
        self.grid[y][x] = self.rotate_direction_ccw(self.grid[y][x])
        self.user_move_count += 1
        return True

    def check_win(self) -> bool:
        """Compare current grid with solution."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != self.solution[y][x]:
                    return False
        return True

    def get_connected_cells(self):
        """Return set of all cells connected to the server."""
        connected = set()
        stack = [self.server_pos]
        connected.add(self.server_pos)

        while stack:
            x, y = stack.pop()
            current = self.grid[y][x]
            for dx, dy, direction, opposite in [
                (0, -1, Direction.UP, Direction.DOWN),
                (1, 0, Direction.RIGHT, Direction.LEFT),
                (0, 1, Direction.DOWN, Direction.UP),
                (-1, 0, Direction.LEFT, Direction.RIGHT)
            ]:
                if current & direction:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height
                            and (nx, ny) not in connected
                            and self.grid[ny][nx] & opposite):
                        connected.add((nx, ny))
                        stack.append((nx, ny))
        return connected
