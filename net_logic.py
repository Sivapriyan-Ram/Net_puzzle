import random
from enum import IntFlag
from functools import lru_cache


class Direction(IntFlag):
    NONE = 0
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8



class TileType:
    BLANK = 0
    ENDPOINT = 1
    SERVER = 2
    JUNCTION = 3



class NetGameLogic:

    def __init__(self, width: int = 7, height: int = 7) -> None:
        self.width = width
        self.height = height
        
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
        """O(W×H) deep copy of grid."""
        return [[grid[y][x] for x in range(self.width)] for y in range(self.height)]

    def change_size(self, width: int, height: int) -> None:
        """
        Resize grid with DYNAMIC cell sizing + new puzzle.
        ✅ Automatically adjusts cell_size for new dimensions!
        """
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        
        # ========== UPDATE CELL SIZE FOR NEW GRID =========
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
        """
        Generate solvable puzzle using DFS spanning tree.
        
        ALGORITHM:
        1. Start at server, create 2-3 random branches
        2. DFS: extend randomly until no unvisited neighbors
        3. Classify tiles by degree (ENDPOINT=1, JUNCTION=2+)
        4. Save solution, scramble non-server tiles randomly
        
        Time: O(W×H) - visits each cell at most once
        Space: O(W×H) for grids
        """
        self.user_move_count = 0
        self.solving_animation_running = False

        self.grid = [[Direction.NONE for _ in range(self.width)] for _ in range(self.height)]
        self.tile_types = [[TileType.BLANK for _ in range(self.width)] for _ in range(self.height)]
        self.solution = [[Direction.NONE for _ in range(self.width)] for _ in range(self.height)]

        # Place server and generate tree
        sx, sy = self.server_pos
        self.tile_types[sy][sx] = TileType.SERVER

        visited = set([(sx, sy)])
        directions = [
            (0, -1, Direction.UP, Direction.DOWN),
            (1, 0, Direction.RIGHT, Direction.LEFT),
            (0, 1, Direction.DOWN, Direction.UP),
            (-1, 0, Direction.LEFT, Direction.RIGHT)
        ]

        random.shuffle(directions)
        initial_branches = random.choice([2, 3])
        stack = []

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

        while stack:
            x, y = stack[-1]
            neighbors = []
            for dx, dy, direction, opposite in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited):
                    neighbors.append((nx, ny, direction, opposite))
            if neighbors:
                nx, ny, direction, opposite = random.choice(neighbors)
                self.grid[y][x] |= direction
                self.grid[ny][nx] |= opposite
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        # Save solution and classify tiles
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

        # Scramble
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) != self.server_pos and self.grid[y][x] != Direction.NONE:
                    rotations = random.randint(1, 3)
                    for _ in range(rotations):
                        self.grid[y][x] = self.rotate_direction(self.grid[y][x])

        self.initial_scrambled_grid = self.clone_grid(self.grid)

    def restart_game(self) -> None:
        """Restore initial scrambled state. Time: O(W×H)"""
        if not self.initial_scrambled_grid:
            return
        self.user_move_count = 0
        self.solving_animation_running = False
        self.grid = self.clone_grid(self.initial_scrambled_grid)

    def solve_with_tree_dp(self, start_grid):
        """
        DIVIDE AND CONQUER SOLVER using Dynamic Programming on tree structure.
        
        This is the main solver method called directly by the UI.
        
        Algorithm:
        - Divide: Break problem into subtrees (children of each node)
        - Conquer: Solve each subtree optimally using DP
        - Optimal substructure: Local optimal rotations + sum of child solutions
        
        Time Complexity: O(W×H) - visits each cell once with memoization
        Space Complexity: O(W×H) - for DP cache and adjacency
        
        Returns: List of moves [(x, y, 'cw'|'ccw')] to solve the puzzle
        """
        # Phase 1: Build adjacency from solution (tree structure)
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
            Recursive DP function that returns (min_cost, best_clockwise_rotations)
            for the subtree rooted at 'node'.
            """
            x, y = node
            current = start_grid[y][x]
            target = self.solution[y][x]

            # Generate all possible rotations for current tile
            rotations = []
            state = current
            for i in range(4):
                rotations.append((state, i))  # (rotated_state, clockwise_rotations)
                state = self.rotate_direction(state)

            best_cost = float('inf')
            best_rotation = 0
            
            # Try each possible rotation state for current node
            for state, rot_cw in rotations:
                if state != target:
                    continue  # Must match target orientation

                # Cost for this tile: minimal rotations (CW vs CCW)
                rot_ccw = (4 - rot_cw) % 4
                tile_cost = min(rot_cw, rot_ccw)

                total = tile_cost

                # DIVIDE: Recursively solve each child subtree
                for child in adj[node]:
                    if child == parent:
                        continue
                    child_cost, _ = solve_subtree(child, node)
                    total += child_cost

                # CONQUER: Choose minimal total cost for this configuration
                if total < best_cost:
                    best_cost = total
                    best_rotation = rot_cw

            return best_cost, best_rotation
            
        # Trigger recursion from root to populate cache
        solve_subtree(root, None)

        # Phase 2: RECONSTRUCTION - Build actual move list from DP results
        moves = []

        def collect_moves(node, parent):
            """Reconstruct the actual moves from computed DP results."""
            _, rot_cw = solve_subtree(node, parent)
            x, y = node
            current = start_grid[y][x]
            target = self.solution[y][x]

            # Determine actual direction to apply minimal rotations
            if current != target:
                # Find minimal rotations (clockwise vs counter‑clockwise)
                cw = current
                cw_cnt = 0
                while cw != target and cw_cnt < 4:
                    cw = self.rotate_direction(cw)
                    cw_cnt += 1
                ccw = current
                ccw_cnt = 0
                while ccw != target and ccw_cnt < 4:
                    ccw = self.rotate_direction_ccw(ccw)
                    ccw_cnt += 1
                if cw_cnt <= ccw_cnt:
                    direction = 'cw'
                    rotations = cw_cnt
                else:
                    direction = 'ccw'
                    rotations = ccw_cnt
                moves.extend([(x, y, direction)] * rotations)

            # Recurse on children
            for child in adj[node]:
                if child != parent:
                    collect_moves(child, node)

        collect_moves(root, None)
        return moves

    def rotate_direction(self, direction: Direction) -> Direction:
        """O(1) 90° clockwise rotation."""
        result = Direction.NONE
        if direction & Direction.UP:    result |= Direction.RIGHT
        if direction & Direction.RIGHT: result |= Direction.DOWN
        if direction & Direction.DOWN:  result |= Direction.LEFT
        if direction & Direction.LEFT:  result |= Direction.UP
        return result

    def rotate_direction_ccw(self, direction: Direction) -> Direction:
        """O(1) 90° counter-clockwise rotation."""
        result = Direction.NONE
        if direction & Direction.UP:    result |= Direction.LEFT
        if direction & Direction.LEFT:  result |= Direction.DOWN
        if direction & Direction.DOWN:  result |= Direction.RIGHT
        if direction & Direction.RIGHT: result |= Direction.UP
        return result

    def left_rotate_at(self, x: int, y: int) -> bool:
        """O(1) clockwise rotation + increment counter."""
        if self.grid[y][x] == Direction.NONE:
            return False
        self.grid[y][x] = self.rotate_direction(self.grid[y][x])
        self.user_move_count += 1
        return True

    def right_rotate_at(self, x: int, y: int) -> bool:
        """O(1) counter-clockwise rotation + increment counter."""
        if self.grid[y][x] == Direction.NONE:
            return False
        self.grid[y][x] = self.rotate_direction_ccw(self.grid[y][x])
        self.user_move_count += 1
        return True

    def check_win(self) -> bool:
        """O(W×H) exact match check."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != self.solution[y][x]:
                    return False
        return True

    def get_connected_cells(self):
        """O(W×H) DFS traversal."""
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
