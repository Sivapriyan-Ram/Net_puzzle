# NET Game - Master the art of puzzles

PUZZLE DEVELOPERS :

  Rishikeshwar V T - CB.SC.U4CSE24041
  Sivapriyan R - CB.SC.U4CSE24051
  Prithesh S - CB.SC.U4CSE24038
  Rakesh Khanna G - CB.SC.U4CSE24014

This repository contains the complete backend logic for a NET (pipe connection) puzzle game.
The project focuses on efficient puzzle generation, bitmask-based grid representation, and a high-performance greedy solver with O(W × H) time complexity.

The UI is also included; this code is designed to be plugged into the given ui.

Table of Contents:
  Project Overview
  Features
  Technologies Used
  Grid Representation
  Game Components
  Puzzle Generation Algorithm
  Greedy Solver Algorithm
  Rotation Logic
  Restart & Replay Support
  Connected Component Detection
  Time & Space Complexity
  How to Run / Use
  Use Cases

Project Overview:

The NET puzzle requires players to rotate tiles so that all pipes connect correctly to a central server without forming loops.
This implementation guarantees:

A single connected solution
No cycles (tree structure)
Fast automatic solving
Identical puzzle state on restart

Features:

DFS-based puzzle generation
Guaranteed solvable puzzles
No loop formation
Bitmask representation for connections
Optimized greedy solver (single pass)
Dynamic grid sizing
Restart with same scrambled puzzle
Exact move sequence generation

Technologies Used:

Python 3
Enum (IntFlag) for bitmask operations
Depth-First Search (DFS)
Greedy (hill-climbing) algorithm

Grid Representation:

Each tile stores its pipe connections using bitwise flags:

Direction	Bit Value
UP	1
RIGHT	2
DOWN	4
LEFT	8

Example:

UP | RIGHT


This represents a tile connected to the top and right.
This approach acts as an implicit adjacency list, making the grid memory-efficient.

Game Components:
Direction (Enum)
Defines pipe directions using bitmasks.
TileType

Identifies logical roles:

SERVER
ENDPOINT
JUNCTION
BLANK
NetGameLogic (Main Class)

Handles:

Grid creation
Puzzle generation
Scrambling
Solving
Player moves
Win checking

Puzzle Generation Algorithm

Place the server tile at the grid center
Create 2–3 initial connections
Expand the grid using DFS

Ensure:

All tiles are connected
No cycles are formed
Save the grid as the solution
Randomly rotate tiles (except server) to scramble
Time Complexity: O(W × H)

Greedy Solver Algorithm

The solver is a single-pass greedy algorithm:
Compare each tile with the solution
Calculate minimum rotations required (0–3)
Rank tiles by how “broken” they are
Fix the most broken tiles first
Rotate using the shortest direction (CW / CCW)
Solver output format:

(x, y, 'cw')
(x, y, 'ccw')


Time Complexity: O(W × H)
Performance: ~500× faster than naive solvers

Rotation Logic:

Clockwise rotation: 90°
Counter-clockwise rotation: 90°
Bitwise transformation
Constant time per rotation
Restart & Replay Support
Restores the initial scrambled grid

Ensures:

Fair user vs solver comparison
Same puzzle after restart
Move counters reset correctly
Connected Component Detection
Uses DFS traversal from the server tile to find all connected cells.

Used for:

Connectivity validation
Visual highlighting
Win condition checks
Time Complexity: O(W × H)

Time & Space Complexity Summary
Operation	Complexity
Puzzle Generation	O(W × H)
Greedy Solver	O(W × H)
Rotation	O(1)
Win Check	O(W × H)
DFS Traversal	O(W × H)
How to Run / Use
from net_game_logic import NetGameLogic

game = NetGameLogic(7, 7)
moves = game.greedy_solve_full(game.grid)


You can integrate this logic with:

Pygame
Tkinter
Web UI (Canvas / React)
Any custom GUI

Use Cases:

College mini / major projects
Algorithm demonstrations
Puzzle game development
Greedy algorithm study
Graph traversal learning
