from typing import List, Tuple, Set, Optional, Dict, Any
from collections import deque
from enum import IntFlag
import time
import hashlib

# Import from generation module
from puzzle_generation import Direction, TileType


class BacktrackingSolver:
    """
    Pure backtracking solver for network puzzles with comprehensive memoization.
    Handles all edge cases and optimizations for grids of any size.
    """
    
    def __init__(self, width: int, height: int, use_memoization: bool = True):
        self.width = width
        self.height = height
        self.server_pos = (width // 2, height // 2)
        self.use_memoization = use_memoization
        
        # Direction vectors for neighbor checking
        self._direction_vectors = [
            (0, -1, Direction.UP, Direction.DOWN),   # Up
            (1, 0, Direction.RIGHT, Direction.LEFT), # Right
            (0, 1, Direction.DOWN, Direction.UP),    # Down
            (-1, 0, Direction.LEFT, Direction.RIGHT) # Left
        ]
        
        # Rotation cache for performance
        self.rotation_cache = {}
        
        # Memoization cache
        self.memo_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0, 'pruned': 0}
        
        # Pre-compute direction patterns for faster comparison
        self.direction_patterns = self._precompute_patterns()
        
        # Track best solution for timeout situations
        self.best_partial_solution = None
        self.best_coverage = 0
        self.start_time = None
        self.timeout = None
        
    def _precompute_patterns(self) -> Dict[int, Tuple[bool, bool, bool, bool]]:
        """Pre-compute connection patterns for all possible tile values."""
        patterns = {}
        for val in range(16):  # 0-15 (4 bits)
            d = Direction(val)
            patterns[val] = (
                bool(d & Direction.UP),
                bool(d & Direction.RIGHT),
                bool(d & Direction.DOWN),
                bool(d & Direction.LEFT)
            )
        return patterns
    
    def _rotate_direction(self, direction: Direction, steps: int) -> Direction:
        """Rotate direction clockwise by specified steps with caching."""
        if steps == 0 or direction == Direction.NONE:
            return direction
            
        # Use rotation cache for efficiency
        key = (int(direction), steps % 4)
        if key in self.rotation_cache:
            return self.rotation_cache[key]
        
        result = direction
        for _ in range(steps % 4):
            if result == Direction.NONE:
                continue
            new_result = Direction.NONE
            if result & Direction.UP:
                new_result |= Direction.RIGHT
            if result & Direction.RIGHT:
                new_result |= Direction.DOWN
            if result & Direction.DOWN:
                new_result |= Direction.LEFT
            if result & Direction.LEFT:
                new_result |= Direction.UP
            result = new_result
        
        self.rotation_cache[key] = result
        return result
    
    def solve(self, grid: List[List[Direction]], timeout: Optional[float] = None) -> Optional[List[List[Direction]]]:
        """
        Solve the puzzle using backtracking with adaptive memoization.
        
        Args:
            grid: The scrambled puzzle grid
            timeout: Maximum seconds to spend solving (None = no timeout)
        
        Returns:
            Solved grid or None if unsolvable/timed out
        """
        # Reset caches and stats
        self.memo_cache.clear()
        self.rotation_cache.clear()
        self.cache_stats = {'hits': 0, 'misses': 0, 'pruned': 0}
        self.best_partial_solution = None
        self.best_coverage = 0
        self.start_time = time.time()
        self.timeout = timeout
        
        # Validate input grid
        if not self._validate_grid(grid):
            print("Invalid grid input")
            return None
        
        working_grid = [row[:] for row in grid]
        
        # Get rotatable tiles (all except server)
        tiles = self._get_rotatable_tiles(grid)
        
        # Adaptive strategy based on grid size
        grid_size = self.width * self.height
        rotatable_count = len(tiles)
        
        print(f"Solving {self.width}x{self.height} grid with {rotatable_count} rotatable tiles")
        print(f"Memoization: {'ON' if self.use_memoization else 'OFF'}")
        
        # For very large grids, use heuristic-guided search
        if rotatable_count > 40 and self.use_memoization:
            print("Large grid detected - using enhanced heuristic search")
            result = self._solve_heuristic_large(working_grid, tiles)
        else:
            # Standard backtracking
            result = self._backtrack(working_grid, tiles, 0)
        
        # Print cache stats if memoization was used
        if self.use_memoization:
            total = self.cache_stats['hits'] + self.cache_stats['misses']
            if total > 0:
                hit_rate = (self.cache_stats['hits'] / total) * 100
                print(f"Cache stats: {self.cache_stats['hits']} hits, "
                      f"{self.cache_stats['misses']} misses, "
                      f"{self.cache_stats['pruned']} pruned")
                print(f"Hit rate: {hit_rate:.1f}%")
        
        return result
    
    def _validate_grid(self, grid: List[List[Direction]]) -> bool:
        """Validate input grid dimensions and content."""
        if len(grid) != self.height:
            return False
        
        for row in grid:
            if len(row) != self.width:
                return False
            
            for cell in row:
                if not isinstance(cell, Direction):
                    return False
        
        return True
    
    def _get_rotatable_tiles(self, grid: List[List[Direction]]) -> List[Tuple[int, int, int]]:
        """
        Get all rotatable tiles with heuristic information.
        Returns list of (x, y, constraint_level) where higher constraint_level = more constrained.
        """
        tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == self.server_pos:
                    continue
                
                # Calculate constraint level for heuristic ordering
                constraint = 0
                
                # Factor 1: Number of connections (more connections = more constrained)
                connections = bin(int(grid[y][x])).count("1")
                constraint += connections * 10
                
                # Factor 2: Number of adjacent tiles (corners/edges are more constrained)
                adjacent = 0
                for dx, dy, _, _ in self._direction_vectors:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        adjacent += 1
                constraint += (4 - adjacent) * 5  # Corner/edge penalty
                
                # Factor 3: Distance from server (further = less constrained usually)
                dist = abs(x - self.server_pos[0]) + abs(y - self.server_pos[1])
                constraint -= dist  # Slight preference for closer tiles
                
                tiles.append((x, y, constraint))
        
        # Sort by most constrained first (highest constraint value)
        tiles.sort(key=lambda t: -t[2])
        return tiles
    
    def _get_state_signature(self, grid: List[List[Direction]], 
                            tiles: List[Tuple[int, int, int]], 
                            index: int) -> str:
        """
        Create a signature that captures the essential puzzle state for memoization.
        Optimized to balance uniqueness and performance.
        """
        if not self.use_memoization:
            return ""
        
        # For very large grids, use a faster but still unique signature
        if self.width * self.height > 49:  # 7x7 or larger
            return self._get_fast_state_signature(grid, tiles, index)
        
        signature_parts = []
        
        # Part 1: Assigned tile patterns (up to index)
        assigned_patterns = []
        for i in range(min(index, len(tiles))):
            x, y, _ = tiles[i]
            val = int(grid[y][x])
            # Use the pattern tuple for comparison
            pattern = self.direction_patterns[val]
            assigned_patterns.append(f"{x},{y}:{pattern}")
        
        assigned_patterns.sort()
        signature_parts.append("A:" + "|".join(assigned_patterns))
        
        # Part 2: Frontier connections (connections to unassigned area)
        frontier = []
        frontier_set = set()
        
        # Find all frontier cells
        for i in range(min(index, len(tiles))):
            x, y, _ = tiles[i]
            current = grid[y][x]
            
            for dx, dy, out_dir, _ in self._direction_vectors:
                if current & out_dir:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and
                        self._is_unassigned((nx, ny), tiles, index)):
                        frontier.add((nx, ny))
                        frontier.append(f"{x},{y}->{nx},{ny}")
        
        frontier.sort()
        signature_parts.append("F:" + "|".join(frontier))
        
        # Part 3: Component connectivity
        components = self._get_connected_components(grid, tiles, index)
        signature_parts.append(f"C:{components}")
        
        # Part 4: Index
        signature_parts.append(f"I:{index}")
        
        return "|".join(signature_parts)
    
    def _get_fast_state_signature(self, grid: List[List[Direction]],
                                  tiles: List[Tuple[int, int, int]],
                                  index: int) -> str:
        """Faster signature generation for large grids."""
        # Use a hash of the relevant part of the grid
        hash_input = []
        
        # Include only assigned tiles and their neighbors
        for i in range(min(index, len(tiles))):
            x, y, _ = tiles[i]
            hash_input.append(f"{x},{y}:{int(grid[y][x])}")
            
            # Also include neighbors to capture frontier
            for dx, dy, _, _ in self._direction_vectors:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    hash_input.append(f"n{nx},{ny}:{int(grid[ny][nx])}")
        
        hash_input.sort()
        hash_str = "|".join(hash_input)
        
        # Create a shorter hash
        return hashlib.md5(hash_str.encode()).hexdigest()[:16]
    
    def _is_unassigned(self, pos: Tuple[int, int], 
                       tiles: List[Tuple[int, int, int]], 
                       index: int) -> bool:
        """Check if a position is unassigned (not in first index tiles)."""
        if pos == self.server_pos:
            return False
        
        for i in range(index):
            x, y, _ = tiles[i]
            if (x, y) == pos:
                return False
        
        return True
