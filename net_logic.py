import random
from enum import IntFlag
from typing import List, Tuple, Set, Optional, Dict
from collections import deque


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
    
    def __init__(self, width: int = 7, height: int = 7, seed: Optional[int] = None) -> None:
        # Use instance RNG instead of global for better isolation
        self.random = random.Random(seed) if seed is not None else random.Random()
            
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        
        maxdim = max(width, height)
        if maxdim <= 5:
            self.cellsize = 75
        elif maxdim <= 7:
            self.cellsize = 65
        elif maxdim <= 9:
            self.cellsize = 55
        elif maxdim <= 11:
            self.cellsize = 40
        else:
            self.cellsize = 32
            
        self.user_move_count = 0
        self.solving_animation_running = False
        
        self.initial_scrambled_grid = None
        self.solution_grid = None
        
        self.tree_edges: Set[Tuple[Tuple[int,int], Tuple[int,int]]] = set()
        self.adjacency: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        self.rotation_cache: Dict[Tuple[int, int], List[Direction]] = {}
        self.all_tiles: Set[Tuple[int, int]] = set()
        
        # Pre-define direction vectors for reuse
        self._direction_vectors = [
            (0, -1, Direction.UP, Direction.DOWN),   # Up
            (1, 0, Direction.RIGHT, Direction.LEFT), # Right
            (0, 1, Direction.DOWN, Direction.UP),    # Down
            (-1, 0, Direction.LEFT, Direction.RIGHT) # Left
        ]
        
        self.grid: List[List[Direction]] = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.tile_types: List[List[TileType]] = [[TileType.BLANK for _ in range(width)] for _ in range(height)]
        
        self.new_game()

    def clone_grid(self, grid: List[List[Direction]]) -> List[List[Direction]]:
        return [row[:] for row in grid]

    def change_size(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        
        maxdim = max(width, height)
        if maxdim <= 5:
            self.cellsize = 75
        elif maxdim <= 7:
            self.cellsize = 65
        elif maxdim <= 9:
            self.cellsize = 55
        elif maxdim <= 11:
            self.cellsize = 40
        else:
            self.cellsize = 32
        
        self.grid = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.tile_types = [[TileType.BLANK for _ in range(width)] for _ in range(height)]
        
        self.new_game()

    def new_game(self) -> None:
        self.user_move_count = 0
        self.solving_animation_running = False
        
        self.tree_edges.clear()
        self.adjacency.clear()
        self.rotation_cache.clear()
        
        self.all_tiles = {(x, y) for y in range(self.height) for x in range(self.width)}

        self.grid = [[Direction.NONE for _ in range(self.width)]
                     for _ in range(self.height)]

        self.tile_types = [[TileType.BLANK for _ in range(self.width)]
                           for _ in range(self.height)]

        # Generate the spanning tree
        self.generate_tree_dc(0, 0, self.width - 1, self.height - 1)

        for a, b in self.tree_edges:
            self.adjacency.setdefault(a, []).append(b)

        # Set tile types based on connection counts
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == self.server_pos:
                    self.tile_types[y][x] = TileType.SERVER
                else:
                    conn_count = int(self.grid[y][x]).bit_count()
                    if conn_count == 1:
                        self.tile_types[y][x] = TileType.ENDPOINT
                    else:
                        self.tile_types[y][x] = TileType.JUNCTION

        # Save solved state before scrambling
        solved_grid = self.clone_grid(self.grid)
        
        # Scramble the grid
        changed = False
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == self.server_pos:
                    continue
                
                rotations = self.random.randint(1, 3)
                if rotations:
                    changed = True
                
                for _ in range(rotations):
                    self.grid[y][x] = self.rotate_direction(self.grid[y][x])
                    self.rotation_cache.pop((x, y), None)

        # Guarantee puzzle is not already solved
        if self._check_win_with_grid(self.grid):
            # Force rotate one non-server tile
            done = False
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) != self.server_pos:
                        self.grid[y][x] = self.rotate_direction(self.grid[y][x])
                        self.rotation_cache.pop((x, y), None)
                        done = True
                        break
                if done:
                    break

        self.initial_scrambled_grid = self.clone_grid(self.grid)
        self.solution_grid = solved_grid


    def generate_tree_dc(self, x1: int, y1: int, x2: int, y2: int) -> None:
        if x1 == x2 and y1 == y2:
            return

        width = x2 - x1 + 1
        height = y2 - y1 + 1

        if height == 1:
            for x in range(x1, x2):
                self._connect(x, y1, x + 1, y1)
            return

        if width == 1:
            for y in range(y1, y2):
                self._connect(x1, y, x1, y + 1)
            return

        if width >= height:
            mid = x1 + width // 2
            self.generate_tree_dc(x1, y1, mid - 1, y2)
            self.generate_tree_dc(mid, y1, x2, y2)
            y = self.random.randint(y1, y2)
            self._connect(mid - 1, y, mid, y)
        else:
            mid = y1 + height // 2
            self.generate_tree_dc(x1, y1, x2, mid - 1)
            self.generate_tree_dc(x1, mid, x2, y2)
            x = self.random.randint(x1, x2)
            self._connect(x, mid - 1, x, mid)


    def _connect(self, x1: int, y1: int, x2: int, y2: int) -> None:
        dx = x2 - x1
        dy = y2 - y1

        if dx == 1:
            self.grid[y1][x1] |= Direction.RIGHT
            self.grid[y2][x2] |= Direction.LEFT
        elif dx == -1:
            self.grid[y1][x1] |= Direction.LEFT
            self.grid[y2][x2] |= Direction.RIGHT
        elif dy == 1:
            self.grid[y1][x1] |= Direction.DOWN
            self.grid[y2][x2] |= Direction.UP
        elif dy == -1:
            self.grid[y1][x1] |= Direction.UP
            self.grid[y2][x2] |= Direction.DOWN
            self.tree_edges.add(((x1, y1), (x2, y2)))
            self.tree_edges.add(((x2, y2), (x1, y1)))
            
    def rotate_direction(self, direction: Direction) -> Direction:
        if direction == Direction.NONE:
            return Direction.NONE
            
        result = Direction.NONE
        if direction & Direction.UP:
            result |= Direction.RIGHT
        if direction & Direction.RIGHT:
            result |= Direction.DOWN
        if direction & Direction.DOWN:
            result |= Direction.LEFT
        if direction & Direction.LEFT:
            result |= Direction.UP
            
        return result

    def rotate_direction_ccw(self, direction: Direction) -> Direction:
        if direction == Direction.NONE:
            return Direction.NONE
            
        result = Direction.NONE
        if direction & Direction.UP:
            result |= Direction.LEFT
        if direction & Direction.LEFT:
            result |= Direction.DOWN
        if direction & Direction.DOWN:
            result |= Direction.RIGHT
        if direction & Direction.RIGHT:
            result |= Direction.UP
            
        return result

    def left_rotate_at(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        if (x, y) == self.server_pos:
            return False
            
        self.grid[y][x] = self.rotate_direction(self.grid[y][x])
        self.user_move_count += 1
        
        self.rotation_cache.pop((x, y), None)
        return True

    def right_rotate_at(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        if (x, y) == self.server_pos:
            return False
            
        self.grid[y][x] = self.rotate_direction_ccw(self.grid[y][x])
        self.user_move_count += 1
        
        self.rotation_cache.pop((x, y), None)
        return True

    def apply_solve_move(self, x: int, y: int, direction: str, rotations: int) -> None:
        for _ in range(rotations):
            if direction == 'cw':
                self.grid[y][x] = self.rotate_direction(self.grid[y][x])
            else:
                self.grid[y][x] = self.rotate_direction_ccw(self.grid[y][x])
        
        self.rotation_cache.pop((x, y), None)

    def _build_tree_structure(self) -> Tuple[Dict, Dict]:
        parent = {}
        children = {}

        visited = set()
        queue = deque([self.server_pos])

        parent[self.server_pos] = None
        children[self.server_pos] = []
        visited.add(self.server_pos)

        while queue:
            node = queue.popleft()

            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = node
                    children.setdefault(node, []).append(neighbor)
                    children.setdefault(neighbor, [])
                    queue.append(neighbor)

        return parent, children

    def solve_with_dc_dp(self) -> Optional[Dict]:
        """
        Hybrid Divide & Conquer + Dynamic Programming solver.
        Splits children into groups, solves each group independently, then merges.
        """
        parent, children = self._build_tree_structure()
        dp: Dict[Tuple[int, int], Dict[int, Dict]] = {}

        def solve(node):
            x, y = node
            dp[node] = {}

            rot_range = [0] if node == self.server_pos else range(4)

            # Leaf node
            if not children[node]:
                for r in rot_range:
                    dp[node][r] = {}
                return dp[node]

            # Solve children first (postorder)
            for child in children[node]:
                solve(child)

            # Divide children into groups for DC approach
            child_list = children[node]
            mid = len(child_list) // 2
            left_group = child_list[:mid]
            right_group = child_list[mid:]

            def process_group(group):
                # Start with all rotations valid
                valid = {r: {} for r in rot_range}

                for child in group:
                    new_valid = {}

                    for r in valid:
                        rotated_parent = self._get_rotated(x, y, r)

                        found_rotation = None
                        for child_r in dp[child]:
                            rotated_child = self._get_rotated(
                                child[0], child[1], child_r
                            )

                            if self._compatible_pair(
                                rotated_parent, x, y,
                                rotated_child, child[0], child[1]
                            ):
                                found_rotation = child_r
                                break

                        if found_rotation is not None:
                            new_valid.setdefault(r, {}).update(valid[r])
                            new_valid[r][child] = found_rotation

                    valid = new_valid

                    if not valid:
                        break

                return valid

            # Process both groups independently (Divide phase)
            left_valid = process_group(left_group)
            right_valid = process_group(right_group)

            # Merge results (Conquer phase)
            for r in rot_range:
                if r in left_valid and r in right_valid:
                    merged = {}
                    merged.update(left_valid[r])
                    merged.update(right_valid[r])
                    dp[node][r] = merged

            return dp[node]

        # Run solve starting at root
        solve(self.server_pos)

        if not dp[self.server_pos]:
            return None

        solution: Dict[Tuple[int, int], int] = {}


