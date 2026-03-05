# NET Game - Master the art of puzzles

PUZZLE DEVELOPERS :

  Rishikeshwar V T - CB.SC.U4CSE24041
  Sivapriyan R - CB.SC.U4CSE24051
  Prithesh S - CB.SC.U4CSE24038
  Rakesh Khanna G - CB.SC.U4CSE24014

# 🧩 NET Puzzle Game

A professional, fully playable **network-connection puzzle game** built with **Python** and **Tkinter**, featuring:

* 🎲 Procedural puzzle generation
* 🔄 Interactive tile rotation
* 🤖 Optimal auto-solver using **Backtracking + memoization**
* 🎞 Step-by-step animated solving
* 📊 Real-time connectivity tracking

---

## 🎮 Game Preview

 ![WhatsApp Image 2026-03-05 at 11 21 54 PM](https://github.com/user-attachments/assets/f758d8ac-deb4-4173-ab00-a133ed47f25c)


---

# ✨ Features

* ✅ Procedurally generated tree-based puzzles
* ✅ Guaranteed solvable boards
* ✅ Bitwise tile encoding using `IntFlag`
* ✅ Optimal solver (minimum rotation cost)
* ✅ Animated solution playback
* ✅ Multiple difficulty levels (5×5 to 11×11)
* ✅ Clean separation of logic and UI

---

# 🧠 How It Works

## 🔧 Puzzle Generation

1. An empty grid of size W × H.
2. A Recursive Divide and Conquer to generate a **tree structure**.
3. Each tile becomes:

   * `SERVER`
   * `ENDPOINT` (1 connection)
   * `JUNCTION` (2+ connections)
4. The solution is stored.
5. Tiles are randomly rotated to scramble the board.

Because the network is a **tree**, the puzzle:

* Has no cycles
* Is always connected in the solution
* Is guaranteed solvable

---

## 🔁 Tile Representation

Each tile uses bitwise directional flags:

```python
class Direction(IntFlag):
    NONE = 0
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8
```

This allows:

* Efficient rotation
* Fast connectivity checks
* Compact state storage

---

## 🤖 Solver – BackTracking

The solver:

1.	Tries all possible rotations (0°, 90°, 180°, 270°) for each tile.
2.	Checks whether the current tile connections are valid with neighboring tiles.
3.	If a configuration becomes invalid, the algorithm backtracks to the previous tile.
4.	Recursively explores the next tile when a valid configuration is found.
5.	Prunes invalid configurations early to reduce unnecessary computation.
6.	Continues until the entire grid forms a valid connected network.


---

# 🖥️ User Interface

Built with **Tkinter Canvas**, featuring:

| Action      | Behavior                 |
| ----------- | ------------------------ |
| Left Click  | Rotate clockwise         |
| Right Click | Rotate counter-clockwise |
| New Game    | Generate new puzzle      |
| Restart     | Reset to scrambled state |
| Solve Now   | Instantly solve          |
| Start Solve | Animated solve           |
| Stop Solve  | Stop animation           |

---

# 🎚 Difficulty Levels

Selectable grid sizes:

* 5×5
* 7×7 (default)
* 9×9
* 11×11

Larger grids:

* Smaller cell sizes
* More complex branching
* Longer optimal solution paths

---

# 📊 Game Status Indicators

* **Active:** Connected tiles / Total tiles
* **User Steps:** Player move count
* **Solve Steps:** Solver step count
* **Cycles:Yes/No** Cycle formation in puzzle

Connected tiles are visually highlighted.

---

# 📂 Project Structure

```
.
├── backtracking_solver.py      # Solver logic
├── puzzle_generation.py      # Puzzle generation logic
├── net_game_ui.py        # Tkinter GUI implementation
└── README.md
```

---

# 🚀 Installation

## Requirements

* Python 3.8+
* Tkinter (included in most Python distributions)

## Run the Game

```bash
python net_game_ui.py
```

---

# 📈 Technical Highlights

* *Graph theory* (tree structures and connectivity)
* *Backtracking search algorithm*
* *Depth-First Search (DFS)* for traversal and cycle detection
* *Memoization / state caching* to avoid repeated states
* *Bitwise state modeling* using directional flags
* *Constraint checking and pruning* during search
* *Puzzle scrambling and generation algorithms*
* *Separation of game logic and puzzle solver modules*

---

# 🛠 Potential Enhancements

* ⏱ Add timer & scoring system
* 🧩 Add daily challenge mode
* 🎯 Implement hint system
* 🌱 Add seed-based puzzle sharing
* 🎨 Improve UI theme & animations
* 🌍 Port to Pygame or Web (Canvas / React)
* 🤖 Compare solver vs heuristic AI
* 📊 Difficulty estimator using graph metrics

---

# 👤 Author

Developed in Python using Tkinter
Featuring a Backtracking solver.

---

# ⭐ Contributing

Pull requests are welcome.
For major changes, please open an issue first to discuss proposed improvements.

---
