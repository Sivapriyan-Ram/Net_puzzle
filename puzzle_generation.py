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


class PuzzleGenerator:
    """
    Handles the generation of network puzzle games using spanning tree algorithms.
    """
    
    def __init__(self, width: int = 7, height: int = 7, seed: Optional[int] = None) -> None:
        self.random = random.Random(seed) if seed is not None else random.Random()
        self.width = width
        self.height = height
        
        # Pre-define direction vectors for reuse
        self._direction_vectors = [
            (0, -1, Direction.UP, Direction.DOWN),   # Up
            (1, 0, Direction.RIGHT, Direction.LEFT), # Right
            (0, 1, Direction.DOWN, Direction.UP),    # Down
            (-1, 0, Direction.LEFT, Direction.RIGHT) # Left
        ]
        
    def generate_puzzle(self, server_pos: Tuple[int, int]) -> Tuple[List[List[Direction]], List[List[int]], Set]:
        """
        Generate a new puzzle using divide and conquer spanning tree algorithm.
        
        Returns:
            - Initial grid (scrambled)
            - Tile types grid
            - Tree edges set
        """
        grid = [[Direction.NONE for _ in range(self.width)] for _ in range(self.height)]
        tile_types = [[TileType.BLANK for _ in range(self.width)] for _ in range(self.height)]
        tree_edges = set()
        
        # Generate the spanning tree
        self._generate_tree_dc(0, 0, self.width - 1, self.height - 1, grid, tree_edges)
        
        # Set tile types based on connection counts
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == server_pos:
                    tile_types[y][x] = TileType.SERVER
                else:
                    conn_count = int(grid[y][x]).bit_count()
                    if conn_count == 1:
                        tile_types[y][x] = TileType.ENDPOINT
                    else:
                        tile_types[y][x] = TileType.JUNCTION
        
        return grid, tile_types, tree_edges
    
    def _generate_tree_dc(self, x1: int, y1: int, x2: int, y2: int, 
                          grid: List[List[Direction]], tree_edges: Set) -> None:
        """Divide and conquer spanning tree generation."""
        if x1 == x2 and y1 == y2:
            return

        width = x2 - x1 + 1
        height = y2 - y1 + 1

        if height == 1:
            for x in range(x1, x2):
                self._connect(x, y1, x + 1, y1, grid, tree_edges)
            return

        if width == 1:
            for y in range(y1, y2):
                self._connect(x1, y, x1, y + 1, grid, tree_edges)
            return

        if width >= height:
            mid = x1 + width // 2
            self._generate_tree_dc(x1, y1, mid - 1, y2, grid, tree_edges)
            self._generate_tree_dc(mid, y1, x2, y2, grid, tree_edges)
            y = self.random.randint(y1, y2)
            self._connect(mid - 1, y, mid, y, grid, tree_edges)
        else:
            mid = y1 + height // 2
            self._generate_tree_dc(x1, y1, x2, mid - 1, grid, tree_edges)
            self._generate_tree_dc(x1, mid, x2, y2, grid, tree_edges)
            x = self.random.randint(x1, x2)
            self._connect(x, mid - 1, x, mid, grid, tree_edges)

    def _connect(self, x1: int, y1: int, x2: int, y2: int, 
                 grid: List[List[Direction]], tree_edges: Set) -> None:
        """Connect two adjacent cells in the grid."""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 1:
            grid[y1][x1] |= Direction.RIGHT
            grid[y2][x2] |= Direction.LEFT
        elif dx == -1:
            grid[y1][x1] |= Direction.LEFT
            grid[y2][x2] |= Direction.RIGHT
        elif dy == 1:
            grid[y1][x1] |= Direction.DOWN
            grid[y2][x2] |= Direction.UP
        elif dy == -1:
            grid[y1][x1] |= Direction.UP
            grid[y2][x2] |= Direction.DOWN

        tree_edges.add(((x1, y1), (x2, y2)))
        tree_edges.add(((x2, y2), (x1, y1)))

    def scramble_puzzle(self, grid: List[List[Direction]], server_pos: Tuple[int, int]) -> List[List[Direction]]:
        """
        Scramble the puzzle by randomly rotating non-server tiles.
        Returns the scrambled grid.
        """
        scrambled = [row[:] for row in grid]
        
        changed = False
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == server_pos:
                    continue
                
                rotations = self.random.randint(1, 3)
                if rotations:
                    changed = True
                
                for _ in range(rotations):
                    scrambled[y][x] = self._rotate_direction_cw(scrambled[y][x])

        # Ensure puzzle is not already solved
        if self._is_solved(scrambled, server_pos):
            # Force rotate one non-server tile
            done = False
            for y in range(self.height):
                for x in range(self.width):
                    if (x, y) != server_pos:
                        scrambled[y][x] = self._rotate_direction_cw(scrambled[y][x])
                        done = True
                        break
                if done:
                    break
                    
        return scrambled

    def _rotate_direction_cw(self, direction: Direction) -> Direction:
        """Rotate direction clockwise."""
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

    def _rotate_direction_ccw(self, direction: Direction) -> Direction:
        """Rotate direction counter-clockwise."""
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

    def _is_solved(self, grid: List[List[Direction]], server_pos: Tuple[int, int]) -> bool:
        """Check if the grid is in a solved state."""
        connected = self._get_connected_cells(grid, server_pos)
        total_nodes = self.width * self.height
        
        if len(connected) != total_nodes:
            return False
        
        total_edges = self._count_total_edges(grid)
        
        return total_edges == total_nodes - 1 and not self._has_cycles(grid)

    def _get_connected_cells(self, grid: List[List[Direction]], 
                             server_pos: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Get all cells connected to the server."""
        connected = set()
        stack = deque([server_pos])
        connected.add(server_pos)
        
        while stack:
            x, y = stack.popleft()
            current = grid[y][x]
            
            for dx, dy, dir_bit, opp_bit in self._direction_vectors:
                if current & dir_bit:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and 
                        grid[ny][nx] & opp_bit and (nx, ny) not in connected):
                        connected.add((nx, ny))
                        stack.append((nx, ny))
                        
        return connected

    def _has_cycles(self, grid: List[List[Direction]]) -> bool:
        """Check if the grid contains cycles."""
        visited = set()

        def dfs(x: int, y: int, parent: Optional[Tuple[int, int]]) -> bool:
            visited.add((x, y))

            for dx, dy, d_bit, opp_bit in self._direction_vectors:
                if grid[y][x] & d_bit:
                    nx, ny = x + dx, y + dy

                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        continue

                    if not (grid[ny][nx] & opp_bit):
                        continue

                    if (nx, ny) not in visited:
                        if dfs(nx, ny, (x, y)):
                            return True
                    elif (nx, ny) != parent:
                        return True

            return False

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in visited and grid[y][x] != Direction.NONE:
                    if dfs(x, y, None):
                        return True

        return False

    def _count_total_edges(self, grid: List[List[Direction]]) -> int:
        """Count total number of edges in the grid."""
        total = 0
        for y in range(self.height):
            for x in range(self.width):
                total += int(grid[y][x]).bit_count()
        return total // 2


class GameState:
    """
    Manages the current state of a network puzzle game.
    """
    
    def __init__(self, width: int = 7, height: int = 7, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        
        # Calculate cell size based on dimensions
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
        
        # Game data
        self.grid = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.tile_types = [[TileType.BLANK for _ in range(width)] for _ in range(height)]
        self.tree_edges: Set[Tuple[Tuple[int,int], Tuple[int,int]]] = set()
        self.initial_scrambled_grid = None
        self.solution_grid = None
        
        # Rotation cache for performance
        self.rotation_cache: Dict[Tuple[int, int], List[Direction]] = {}
        
        # Direction vectors
        self._direction_vectors = [
            (0, -1, Direction.UP, Direction.DOWN),
            (1, 0, Direction.RIGHT, Direction.LEFT),
            (0, 1, Direction.DOWN, Direction.UP),
            (-1, 0, Direction.LEFT, Direction.RIGHT)
        ]
        
        # Initialize generator
        self.generator = PuzzleGenerator(width, height, seed)
        
    def new_game(self) -> None:
        """Start a new game."""
        self.user_move_count = 0
        self.solving_animation_running = False
        self.rotation_cache.clear()
        
        # Generate puzzle
        solved_grid, self.tile_types, self.tree_edges = self.generator.generate_puzzle(
            self.server_pos
        )
        self.solution_grid = solved_grid
        
        # Scramble the grid
        self.grid = self.generator.scramble_puzzle(solved_grid, self.server_pos)
        self.initial_scrambled_grid = [row[:] for row in self.grid]
        
    def change_size(self, width: int, height: int) -> None:
        """Change the board size."""
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        
        # Recalculate cell size
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
        
        # Reset grids
        self.grid = [[Direction.NONE for _ in range(width)] for _ in range(height)]
        self.tile_types = [[TileType.BLANK for _ in range(width)] for _ in range(height)]
        
        # Update generator
        self.generator = PuzzleGenerator(width, height)
        
        self.new_game()
        
    def rotate_cw(self, x: int, y: int) -> bool:
        """Rotate tile clockwise."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        if (x, y) == self.server_pos:
            return False
            
        self.grid[y][x] = self.generator._rotate_direction_cw(self.grid[y][x])
        self.user_move_count += 1
        self.rotation_cache.pop((x, y), None)
        return True
        
    def rotate_ccw(self, x: int, y: int) -> bool:
        """Rotate tile counter-clockwise."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        if (x, y) == self.server_pos:
            return False
            
        self.grid[y][x] = self.generator._rotate_direction_ccw(self.grid[y][x])
        self.user_move_count += 1
        self.rotation_cache.pop((x, y), None)
        return True
        
    def get_rotated(self, x: int, y: int, rot: int) -> Direction:
        """Get the direction after applying rotation."""
        key = (x, y)
        if key not in self.rotation_cache:
            base = self.grid[y][x]
            rotations = [base]
            for _ in range(3):
                rotations.append(self.generator._rotate_direction_cw(rotations[-1]))
            self.rotation_cache[key] = rotations
        return self.rotation_cache[key][rot % 4]
        
    def check_win(self) -> bool:
        """Check if the current puzzle state is solved."""
        return self.generator._is_solved(self.grid, self.server_pos)
        
    def get_connected_cells(self) -> Set[Tuple[int, int]]:
        """Get all cells connected to the server."""
        return self.generator._get_connected_cells(self.grid, self.server_pos)
        
    def count_endpoints(self) -> int:
        """Count the number of endpoint tiles."""
        count = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.tile_types[y][x] == TileType.ENDPOINT:
                    count += 1
        return count
        
    def has_cycles(self) -> bool:
        """Check if the current grid has cycles."""
        return self.generator._has_cycles(self.grid)
        
    def clone_grid(self) -> List[List[Direction]]:
        """Create a deep copy of the current grid."""
        return [row[:] for row in self.grid]
