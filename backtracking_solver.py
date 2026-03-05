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
    def _get_connected_components(self, grid: List[List[Direction]],
                                  tiles: List[Tuple[int, int, int]],
                                  index: int) -> str:
        """Identify connected components among assigned tiles."""
        assigned = set()
        for i in range(index):
            x, y, _ = tiles[i]
            assigned.add((x, y))
        
        if not assigned:
            return "0"
        
        visited = set()
        components = []
        
        def dfs_component(start):
            component = []
            stack = [start]
            visited.add(start)
            
            while stack:
                x, y = stack.pop()
                component.append(f"{x},{y}")
                
                for dx, dy, out_dir, in_dir in self._direction_vectors:
                    if grid[y][x] & out_dir:
                        nx, ny = x + dx, y + dy
                        if ((nx, ny) in assigned and (nx, ny) not in visited and
                            grid[ny][nx] & in_dir):
                            visited.add((nx, ny))
                            stack.append((nx, ny))
            
            return component
        
        for tile in assigned:
            if tile not in visited:
                component = dfs_component(tile)
                component.sort()
                components.append("+".join(component))
        
        components.sort()
        return "/".join(components)
    
    def _check_timeout(self) -> bool:
        """Check if we've exceeded the timeout."""
        if self.timeout is None:
            return False
        
        elapsed = time.time() - self.start_time
        return elapsed > self.timeout

    def _backtrack(self, grid: List[List[Direction]],
                  tiles: List[Tuple[int, int, int]],
                  index: int) -> Optional[List[List[Direction]]]:
        """Core backtracking algorithm with memoization."""
        
        # Check timeout
        if self._check_timeout():
            print("Timeout reached")
            return None
        
        # Generate signature for memoization
        signature = self._get_state_signature(grid, tiles, index)
        
        # Check memo cache
        if signature and signature in self.memo_cache:
            self.cache_stats['hits'] += 1
            cached = self.memo_cache[signature]
            if cached is not None:
                # Restore cached solution
                for (x, y), val in cached.items():
                    grid[y][x] = Direction(val)
                return grid
            return None
        
        if signature:
            self.cache_stats['misses'] += 1
        
        # Base case: all tiles assigned
        if index == len(tiles):
            if self._is_valid_solution(grid):
                # Cache the solution
                if signature:
                    solution_pattern = {}
                    for x, y, _ in tiles:
                        solution_pattern[(x, y)] = int(grid[y][x])
                    self.memo_cache[signature] = solution_pattern
                return grid
            
            # Update best partial solution for timeout cases
            connected = len(self._get_connected_cells(grid))
            if connected > self.best_coverage:
                self.best_coverage = connected
                self.best_partial_solution = [row[:] for row in grid]
            
            if signature:
                self.memo_cache[signature] = None
            return None
        
        x, y, _ = tiles[index]
        original = grid[y][x]
        original_val = int(original)
        
        # Try rotations in intelligent order
        rotations = self._order_rotations(original, grid, x, y, tiles, index)
        
        for rotation in rotations:
            if rotation > 0:
                grid[y][x] = self._rotate_direction(grid[y][x], rotation)
            
            # Forward checking
            if self._forward_check(grid, tiles, index):
                result = self._backtrack(grid, tiles, index + 1)
                if result is not None:
                    # Cache success
                    if signature:
                        solution_pattern = {}
                        for tx, ty, _ in tiles:
                            solution_pattern[(tx, ty)] = int(grid[ty][tx])
                        self.memo_cache[signature] = solution_pattern
                    return result
            
            # Restore for next attempt
            grid[y][x] = original
        
        # No solution from this state
        if signature:
            self.memo_cache[signature] = None
        return None
     def _solve_heuristic_large(self, grid: List[List[Direction]],
                               tiles: List[Tuple[int, int, int]]) -> Optional[List[List[Direction]]]:
        """
        Specialized solver for very large grids using additional heuristics.
        """
        # First try with memoization
        result = self._backtrack(grid, tiles, 0)
        
        # If no solution found and we have a good partial solution,
        # try to complete it with a different ordering
        if result is None and self.best_partial_solution is not None:
            print("Attempting to complete best partial solution...")
            
            # Reorder tiles based on current partial solution
            new_tiles = []
            for x, y, constraint in tiles:
                if (x, y) in self._get_connected_cells(self.best_partial_solution):
                    # Prioritize tiles connected to solution
                    new_tiles.append((x, y, constraint + 100))
                else:
                    new_tiles.append((x, y, constraint))
            
            new_tiles.sort(key=lambda t: -t[2])
            
            # Try again with new ordering
            self.memo_cache.clear()
            result = self._backtrack(self.best_partial_solution, new_tiles, 0)
        
        return result
    
    def _order_rotations(self, tile: Direction, grid: List[List[Direction]],
                        x: int, y: int, tiles: List[Tuple[int, int, int]],
                        index: int) -> List[int]:
        """
        Order rotations intelligently - try most promising first.
        """
        scores = []
        
        # Get assigned tiles up to current index
        assigned = set()
        for i in range(index):
            tx, ty, _ = tiles[i]
            assigned.add((tx, ty))
        
        for rot in range(4):
            if rot == 0:
                rotated = tile
            else:
                rotated = self._rotate_direction(tile, rot)
            
            score = 0
            
            # Check assigned neighbors
            valid = True
            for dx, dy, out_dir, in_dir in self._direction_vectors:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) in assigned):
                    # Must match existing connections
                    neighbor = grid[ny][nx]
                    if (rotated & out_dir) != (neighbor & in_dir):
                        valid = False
                        break
                    elif rotated & out_dir:
                        score += 20  # Good match with assigned neighbor
            
            if not valid:
                scores.append((-100, rot))  # Invalid, will be pruned
                continue
            
            # Check server adjacency
            if (x + 1, y) == self.server_pos and (rotated & Direction.RIGHT):
                score += 15
            if (x - 1, y) == self.server_pos and (rotated & Direction.LEFT):
                score += 15
            if (x, y + 1) == self.server_pos and (rotated & Direction.DOWN):
                score += 15
            if (x, y - 1) == self.server_pos and (rotated & Direction.UP):
                score += 15
            
            # Prefer rotations that minimize open connections (reduces branching)
            open_connections = 0
            for dx, dy, out_dir, _ in self._direction_vectors:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) not in assigned and (nx, ny) != self.server_pos):
                    if rotated & out_dir:
                        open_connections += 1
                        score -= 2  # Penalty for each open connection
            
            # Bonus for matching original orientation (if it worked well elsewhere)
            if rot == 0 and open_connections <= 1:
                score += 5
            
            scores.append((score, rot))
        
        # Sort by score descending, return rotations
        scores.sort(reverse=True)
        return [rot for score, rot in scores if score > -100]
    

    def _forward_check(self, grid: List[List[Direction]],
                      tiles: List[Tuple[int, int, int]],
                      index: int) -> bool:
        """
        Forward checking with multiple pruning strategies.
        """
        x, y, _ = tiles[index]
        current = grid[y][x]
        
        # Get assigned tiles
        assigned = set()
        for i in range(index + 1):
            tx, ty, _ = tiles[i]
            assigned.add((tx, ty))
        
        # Check each neighbor
        for dx, dy, out_dir, in_dir in self._direction_vectors:
            nx, ny = x + dx, y + dy
            
            # Check bounds
            if not (0 <= nx < self.width and 0 <= ny < self.height):
                if current & out_dir:
                    self.cache_stats['pruned'] += 1
                    return False  # Connection pointing out of bounds
                continue
            
            # Skip server
            if (nx, ny) == self.server_pos:
                if current & out_dir:
                    # Must match server's connection
                    if not (grid[ny][nx] & in_dir):
                        self.cache_stats['pruned'] += 1
                        return False
                continue
            
            # If neighbor is assigned, check consistency
            if (nx, ny) in assigned:
                neighbor = grid[ny][nx]
                if (current & out_dir) != (neighbor & in_dir):
                    self.cache_stats['pruned'] += 1
                    return False
        
        # Check for isolated components
        if self._creates_premature_isolation(grid, tiles, index):
            self.cache_stats['pruned'] += 1
            return False
        
        # Check for impossible degree constraints
        if self._violates_degree_constraints(grid, tiles, index):
            self.cache_stats['pruned'] += 1
            return False
        
        return True
                          
    def _creates_premature_isolation(self, grid: List[List[Direction]],
                                     tiles: List[Tuple[int, int, int]],
                                     index: int) -> bool:
        """Check if current assignment creates a component that can't connect to server."""
        
        # Get assigned tiles
        assigned = set()
        for i in range(index + 1):
            tx, ty, _ = tiles[i]
            assigned.add((tx, ty))
        
        # Find all components among assigned tiles
        visited = set()
        components = []
        
        def dfs_component(start):
            comp = set()
            stack = [start]
            visited.add(start)
            comp.add(start)
            
            while stack:
                cx, cy = stack.pop()
                for dx, dy, out_dir, in_dir in self._direction_vectors:
                    if grid[cy][cx] & out_dir:
                        nx, ny = cx + dx, cy + dy
                        if ((nx, ny) in assigned and (nx, ny) not in visited and
                            grid[ny][nx] & in_dir):
                            visited.add((nx, ny))
                            comp.add((nx, ny))
                            stack.append((nx, ny))
            return comp
        
        for tile in assigned:
            if tile not in visited:
                comp = dfs_component(tile)
                components.append(comp)
        
        # If more than one component and none contain server, we're doomed
        server_connected = any(self.server_pos in comp for comp in components)
        
        if len(components) > 1 and not server_connected:
            return True
        
        # Check if any component has no possibility to connect to others
        for comp in components:
            if self.server_pos in comp:
                continue  # Server component is fine
            
            # Does this component have any potential connections to outside?
            has_escape = False
            for cx, cy in comp:
                for dx, dy, out_dir, _ in self._direction_vectors:
                    if grid[cy][cx] & out_dir:
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and
                            (nx, ny) not in assigned and (nx, ny) != self.server_pos):
                            has_escape = True
                            break
                if has_escape:
                    break
            
            if not has_escape:
                return True  # Component is trapped
        
        return False
    
    def _violates_degree_constraints(self, grid: List[List[Direction]],
                                     tiles: List[Tuple[int, int, int]],
                                     index: int) -> bool:
        """Check if any tile has impossible degree requirements."""
        
        # Get assigned tiles
        assigned = set()
        for i in range(index + 1):
            tx, ty, _ = tiles[i]
            assigned.add((tx, ty))
        
        # Check each assigned tile
        for ax, ay in assigned:
            current = grid[ay][ax]
            current_connections = bin(int(current)).count("1")
            
            # Count already matched connections
            matched = 0
            for dx, dy, out_dir, in_dir in self._direction_vectors:
                nx, ny = ax + dx, ay + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) in assigned):
                    if (current & out_dir) and (grid[ny][nx] & in_dir):
                        matched += 1
                    elif (current & out_dir) != (grid[ny][nx] & in_dir):
                        # Mismatch already caught elsewhere
                        pass
            
            # If we already have more matches than connections, impossible
            if matched > current_connections:
                return True
            
            # Check if we can possibly satisfy remaining connections
            remaining = current_connections - matched
            possible_future = 0
            
            for dx, dy, out_dir, in_dir in self._direction_vectors:
                nx, ny = ax + dx, ay + dy
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) not in assigned and (nx, ny) != self.server_pos):
                    # This could potentially connect in the future
                    if current & out_dir:
                        possible_future += 1
            
            if possible_future < remaining:
                return True
        
        return False

    def _is_valid_solution(self, grid: List[List[Direction]]) -> bool:
        """
        Check if the complete grid is a valid solution.
        """
        # Quick checks first
        total_cells = self.width * self.height
        
        # Check all tiles are connected to server
        connected = self._get_connected_cells(grid)
        if len(connected) != total_cells:
            return False
        
        # Count total edges
        total_edges = self._count_total_edges(grid)
        
        # Tree property: N nodes need N-1 edges
        if total_edges != total_cells - 1:
            return False
        
        # Check for cycles
        if self._has_cycles(grid):
            return False
        
        # Check all connections are matched
        for y in range(self.height):
            for x in range(self.width):
                current = grid[y][x]
                
                for dx, dy, out_dir, in_dir in self._direction_vectors:
                    if current & out_dir:
                        nx, ny = x + dx, y + dy
                        # Must be in bounds
                        if not (0 <= nx < self.width and 0 <= ny < self.height):
                            return False
                        # Neighbor must have matching connection
                        if not (grid[ny][nx] & in_dir):
                            return False
        
        return True
    
    def _get_connected_cells(self, grid: List[List[Direction]]) -> Set[Tuple[int, int]]:
        """BFS to find all cells connected to the server."""
        connected = set()
        stack = deque([self.server_pos])
        connected.add(self.server_pos)
        
        while stack:
            x, y = stack.popleft()
            current = grid[y][x]
            
            for dx, dy, out_dir, in_dir in self._direction_vectors:
                if current & out_dir:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and 
                        grid[ny][nx] & in_dir and (nx, ny) not in connected):
                        connected.add((nx, ny))
                        stack.append((nx, ny))
        
        return connected
    
    def _has_cycles(self, grid: List[List[Direction]]) -> bool:
        """DFS cycle detection."""
        visited = set()
        
        def dfs(x: int, y: int, parent: Optional[Tuple[int, int]]) -> bool:
            visited.add((x, y))
            
            for dx, dy, out_dir, in_dir in self._direction_vectors:
                if grid[y][x] & out_dir:
                    nx, ny = x + dx, y + dy
                    
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        continue
                    
                    if not (grid[ny][nx] & in_dir):
                        continue
                    
                    if (nx, ny) not in visited:
                        if dfs(nx, ny, (x, y)):
                            return True
                    elif (nx, ny) != parent:
                        return True
            
            return False
        
        # Start DFS from server
        if dfs(self.server_pos[0], self.server_pos[1], None):
            return True
        
        return False
    

    def _count_total_edges(self, grid: List[List[Direction]]) -> int:
        """Count total number of edges in the grid."""
        total = 0
        for y in range(self.height):
            for x in range(self.width):
                total += int(grid[y][x]).bit_count()
        return total // 2
    
    def get_solution_moves(self, initial_grid: List[List[Direction]], 
                          solved_grid: List[List[Direction]]) -> List[Tuple[int, int, int, str]]:
        """
        Calculate the rotations needed to transform initial to solved grid.
        Returns list of (x, y, rotations, direction) tuples.
        """
        moves = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) == self.server_pos:
                    continue
                    
                initial = initial_grid[y][x]
                solved = solved_grid[y][x]
                
                if initial == solved:
                    continue
                
                # Find minimal rotations (try both directions)
                cw_rotations = 0
                current = initial
                while current != solved and cw_rotations < 4:
                    current = self._rotate_direction(current, 1)
                    cw_rotations += 1
                
                ccw_rotations = 0
                current = initial
                while current != solved and ccw_rotations < 4:
                    current = self._rotate_direction(current, 3)  # CCW = 3 CW steps
                    ccw_rotations += 1
                
                if cw_rotations <= ccw_rotations and cw_rotations > 0:
                    moves.append((x, y, cw_rotations, 'cw'))
                elif ccw_rotations > 0:
                    moves.append((x, y, ccw_rotations, 'ccw'))
        
        return moves
    
    def print_solution_stats(self):
        """Print detailed solution statistics."""
        print("\n=== Solver Statistics ===")
        print(f"Grid size: {self.width}x{self.height}")
        print(f"Memoization: {'ON' if self.use_memoization else 'OFF'}")
        
        if self.use_memoization:
            total = self.cache_stats['hits'] + self.cache_stats['misses']
            if total > 0:
                hit_rate = (self.cache_stats['hits'] / total) * 100
                print(f"Cache hits: {self.cache_stats['hits']}")
                print(f"Cache misses: {self.cache_stats['misses']}")
                print(f"Pruned branches: {self.cache_stats['pruned']}")
                print(f"Hit rate: {hit_rate:.2f}%")
                print(f"Cache size: {len(self.memo_cache)} entries")
        
        if self.best_partial_solution:
            print(f"Best partial coverage: {self.best_coverage}/{self.width * self.height} cells")

