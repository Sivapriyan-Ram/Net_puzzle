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
* 🤖 Optimal auto-solver using **Tree Dynamic Programming**
* 🎞 Step-by-step animated solving
* 📊 Real-time connectivity tracking

---

## 🎮 Game Preview

![WhatsApp Image 2026-02-20 at 10 54 32 AM](https://github.com/user-attachments/assets/ebd00478-31a0-44fa-b387-c5e3c8102ffc)

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

1. A **server node** is placed at the center.
2. A randomized DFS-like expansion generates a **tree structure**.
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

## 🤖 Solver – Tree Dynamic Programming

The solver:

* Reconstructs adjacency from the solution tree
* Recursively computes optimal rotations per subtree
* Uses `lru_cache` for memoization
* Minimizes total rotation cost

It returns a move sequence like:

```python
[(x, y, "cw"), (x, y, "ccw"), ...]
```

### Why Tree-DP?

Since the generated puzzle is a **tree**, each subtree can be solved independently, enabling:

* Optimal minimal-rotation solutions
* Efficient solving even on larger grids
* Clean recursive structure

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
* **DC Steps:** Solver step count

Connected tiles are visually highlighted.

---

# 📂 Project Structure

```
.
├── net_logic.py      # Core generation + solver logic
├── main_ui.py        # Tkinter GUI implementation
└── README.md
```

---

# 🚀 Installation

## Requirements

* Python 3.8+
* Tkinter (included in most Python distributions)

## Run the Game

```bash
python main_ui.py
```

---

# 🏆 Win Condition

The puzzle is solved when:

```python
grid == solution
```

All tiles must match the generated solution state exactly.

---

# 🏗 Architecture Overview

```
NetGameLogic
 ├── new_game()               → Procedural generation
 ├── solve_with_tree_dp()     → Optimal solver
 ├── rotate_direction()       → Bitwise rotation
 ├── get_connected_cells()    → Connectivity check
 └── check_win()              → Victory detection

NetGameUI
 ├── Canvas rendering
 ├── Event handling (clicks)
 ├── Animation loop
 └── Menu + controls
```

---

# 📈 Technical Highlights

* Tree-based procedural generation
* Bitwise state encoding
* Graph traversal (DFS)
* Memoized recursion (`lru_cache`)
* Separation of concerns (Logic vs UI)
* Real-time visual feedback

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
Featuring a Tree Dynamic Programming solver.

---

# ⭐ Contributing

Pull requests are welcome.
For major changes, please open an issue first to discuss proposed improvements.

---
