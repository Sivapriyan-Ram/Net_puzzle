"""
NET Puzzle Game - Complete User Interface
Requires: net_logic.py (which should contain NetGameLogic class)
"""

import tkinter as tk
from tkinter import messagebox, ttk
from net_logic import NetGameLogic, Direction, TileType


class NetGameUI:
    """
    Main user interface for the NET puzzle game.
    Provides a complete interactive gaming experience with solve animations.
    """

    def __init__(self, root: tk.Tk, width: int = 7, height: int = 7) -> None:
        """
        Initialize the game UI.

        Args:
            root: Tkinter root window
            width: Grid width (default 7)
            height: Grid height (default 7)
        """
        self.root = root
        self.root.title("NET Puzzle Game")
        self.root.configure(bg="#09c3f2")

        # Game logic instance
        self.logic = NetGameLogic(width=width, height=height)
        self.cellsize = self.logic.cellsize

        # Animation state variables
        self.solving_animation_running = False
        self.solution_moves = []  # List of (x, y, rotations) tuples
        self.animation_index = 0
        self.total_moves = 0
        self.animation_speed = 500  # milliseconds
        self.after_id = None
        self.initial_grid = None  # Store initial scrambled grid for restart

        # Build the user interface
        self._create_menu()
        self._create_main_frame()
        self._create_control_panel()
        self._create_status_bar()
        self._create_game_board()

        # Store initial grid after creation
        self.initial_grid = self.logic.clone_grid(self.logic.grid)
        self.update_display()

    # ------------------------------------------------------------------------
    # UI Construction Methods
    # ------------------------------------------------------------------------

    def _create_menu(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Game", command=self.new_game, accelerator="Ctrl+N")
        game_menu.add_command(label="Restart Game", command=self.restart_game, accelerator="Ctrl+R")
        game_menu.add_separator()
        game_menu.add_command(label="Solve Instantly", command=self.solve_now, accelerator="Ctrl+S")
        game_menu.add_command(label="Start Animation", command=self.start_solve_animation, accelerator="Ctrl+A")
        game_menu.add_command(label="Stop Animation", command=self.stop_solve_animation, accelerator="Ctrl+Q")
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+X")

        # Size menu
        size_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Board Size", menu=size_menu)

        self.difficulty_var = tk.StringVar(value="7x7")
        sizes = [("5x5", 5, 5), ("7x7", 7, 7), ("9x9", 9, 9), ("11x11", 11, 11)]

        for size_name, w, h in sizes:
            size_menu.add_radiobutton(
                label=size_name,
                variable=self.difficulty_var,
                value=size_name,
                command=lambda w=w, h=h: self.change_size(w, h)
            )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Play", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_game())
        self.root.bind('<Control-r>', lambda e: self.restart_game())
        self.root.bind('<Control-s>', lambda e: self.solve_now())
        self.root.bind('<Control-a>', lambda e: self.start_solve_animation())
        self.root.bind('<Control-q>', lambda e: self.stop_solve_animation())
        self.root.bind('<Control-x>', lambda e: self.root.quit())
        self.root.bind('<F1>', lambda e: self.show_help())

    def _create_main_frame(self) -> None:
        """Create the main container frame."""
        self.main_frame = tk.Frame(self.root, bg="#09c3f2")
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    def _create_control_panel(self) -> None:
        """Create the control panel with buttons."""
        control_frame = tk.Frame(self.main_frame, bg='#09c3f2')
        control_frame.pack(pady=(0, 10), fill=tk.X)

        # Button styles
        btn_style = {
            'font': ('Arial', 10, 'bold'),
            'fg': 'white',
            'padx': 12,
            'pady': 6,
            'relief': tk.RAISED,
            'borderwidth': 2,
            'cursor': 'hand2'
        }

        # First row - Game control buttons
        btn_frame1 = tk.Frame(control_frame, bg='#09c3f2')
        btn_frame1.pack(pady=2)

        tk.Button(btn_frame1, text="🔄 New Game", command=self.new_game,
                  bg='#3498db', **btn_style).pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame1, text="↺ Restart", command=self.restart_game,
                  bg='#f39c12', **btn_style).pack(side=tk.LEFT, padx=3)

        # Second row - Solve buttons
        btn_frame2 = tk.Frame(control_frame, bg='#09c3f2')
        btn_frame2.pack(pady=2)

        tk.Button(btn_frame2, text="⚡ Solve Now", command=self.solve_now,
                  bg='#27ae60', **btn_style).pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame2, text="▶ Start Animation", command=self.start_solve_animation,
                  bg='#e67e22', **btn_style).pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame2, text="⏹ Stop Animation", command=self.stop_solve_animation,
                  bg='#c0392b', **btn_style).pack(side=tk.LEFT, padx=3)

        # Speed control
        speed_frame = tk.Frame(control_frame, bg='#09c3f2')
        speed_frame.pack(pady=5, fill=tk.X)

        tk.Label(speed_frame, text="Animation Speed:", bg='#09c3f2',
                 font=('Arial', 10, 'bold'), fg='#2c3e50').pack(side=tk.LEFT, padx=5)

        self.speed_var = tk.IntVar(value=500)
        speed_scale = tk.Scale(
            speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
            variable=self.speed_var, length=250, bg='#09c3f2',
            highlightbackground='#34495e', troughcolor='#ecf0f1',
            command=self.update_speed
        )
        speed_scale.pack(side=tk.LEFT, padx=5)

        # Speed label
        self.speed_label = tk.Label(speed_frame, text="500 ms", bg='#09c3f2',
                                     font=('Arial', 9), fg='#2c3e50')
        self.speed_label.pack(side=tk.LEFT, padx=5)

    def _create_status_bar(self) -> None:
        """Create the status bar with game information."""
        status_frame = tk.Frame(self.main_frame, bg='#09c3f2')
        status_frame.pack(pady=5, fill=tk.X)

        # Left side status info
        left_frame = tk.Frame(status_frame, bg='#09c3f2')
        left_frame.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            left_frame,
            text="Connected: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#2c3e50",
            padx=10
        )
        self.status_label.pack(side=tk.LEFT)

        self.endpoint_label = tk.Label(
            left_frame,
            text="Endpoints: 0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#2c3e50",
            padx=10
        )
        self.endpoint_label.pack(side=tk.LEFT)

        self.cycle_label = tk.Label(
            left_frame,
            text="Cycles: No",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#2ecc71",
            padx=10
        )
        self.cycle_label.pack(side=tk.LEFT)

        # Right side move counters
        right_frame = tk.Frame(status_frame, bg='#09c3f2')
        right_frame.pack(side=tk.RIGHT)

        self.user_label = tk.Label(
            right_frame,
            text="User moves: 0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#2980b9",
            padx=10
        )
        self.user_label.pack(side=tk.RIGHT)

        self.solve_label = tk.Label(
            right_frame,
            text="Solve steps: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#27ae60",
            padx=10
        )
        self.solve_label.pack(side=tk.RIGHT)

    def _create_game_board(self) -> None:
        """Create the game board canvas."""
        canvas_frame = tk.Frame(self.main_frame, bg='#34495e', relief=tk.SUNKEN, bd=3)
        canvas_frame.pack(pady=10)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.logic.width * self.cellsize,
            height=self.logic.height * self.cellsize,
            bg="#ecf0f1",
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack()

        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Leave>', self.on_mouse_leave)

        # Tooltip for hover
        self.tooltip = None

    # ------------------------------------------------------------------------
    # Game Control Methods
    # ------------------------------------------------------------------------

    def change_size(self, width: int, height: int) -> None:
        """Change the board size."""
        self.stop_solve_animation()
        self.logic.change_size(width, height)
        self.cellsize = self.logic.cellsize

        # Update canvas size
        self.canvas.config(
            width=self.logic.width * self.cellsize,
            height=self.logic.height * self.cellsize
        )

        # Update labels
        self.user_label.config(text=f"User moves: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")

        # Store initial grid
        self.initial_grid = self.logic.clone_grid(self.logic.grid)
        self.update_display()

    def new_game(self) -> None:
        """Start a new game."""
        self.stop_solve_animation()
        self.logic.new_game()
        self.cellsize = self.logic.cellsize

        # Update canvas size
        self.canvas.config(
            width=self.logic.width * self.cellsize,
            height=self.logic.height * self.cellsize
        )

        # Update labels
        self.user_label.config(text=f"User moves: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")

        # Store initial grid
        self.initial_grid = self.logic.clone_grid(self.logic.grid)
        self.update_display()

        messagebox.showinfo("New Game", "New puzzle generated! Try to connect all tiles to the server.")

    def restart_game(self) -> None:
        """Restart the game to the initial scrambled state."""
        self.stop_solve_animation()

        # Restore the initial scrambled grid
        if self.initial_grid:
            for y in range(self.logic.height):
                for x in range(self.logic.width):
                    self.logic.grid[y][x] = self.initial_grid[y][x]

        # Reset move counters
        self.logic.user_move_count = 0
        self.logic.rotation_cache.clear()

        # Update display
        self.user_label.config(text=f"User moves: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")
        self.update_display()

    def update_speed(self, value):
        """Update animation speed from scale."""
        self.animation_speed = int(value)
        self.speed_label.config(text=f"{value} ms")

    # ------------------------------------------------------------------------
    # Solving Methods
    # ------------------------------------------------------------------------

    def solve_now(self) -> None:
        """Solve the puzzle instantly - does NOT increment user steps."""
        if self.solving_animation_running:
            self.stop_solve_animation()

        # Get solution using DC DP solver
        solution = self.logic.solve_with_dc_dp()

        if not solution:
            messagebox.showinfo("Info", "No solution found or puzzle already solved!")
            return

        move_count = len([v for v in solution.values() if v > 0])
        self.solve_label.config(text=f"Solve steps: {move_count}/{move_count}")

        # Update display
        self.update_display()

        if self.logic.check_win():
            self.show_win_message()

    def start_solve_animation(self) -> None:
        """Start step-by-step animation of the solution."""
        if self.solving_animation_running:
            messagebox.showinfo("Info", "Animation is already running!")
            return

        # Store current grid to restore after solving
        current_grid = self.logic.clone_grid(self.logic.grid)

        # Get solution using DC DP solver
        solution = self.logic.solve_with_dc_dp()

        if not solution:
            messagebox.showinfo("Info", "No solution found or puzzle already solved!")
            return

        # Convert solution dictionary to move list (only non-zero rotations)
        self.solution_moves = []
        for (x, y), rotations in solution.items():
            if rotations > 0:
                self.solution_moves.append((x, y, rotations))

        self.total_moves = len(self.solution_moves)

        if not self.solution_moves:
            messagebox.showinfo("Info", "No moves needed - puzzle already solved!")
            return

        # Restore original grid before starting animation
        for y in range(self.logic.height):
            for x in range(self.logic.width):
                self.logic.grid[y][x] = current_grid[y][x]

        self.animation_index = 0
        self.solving_animation_running = True
        self.solve_label.config(text=f"Solve steps: 0/{self.total_moves}")

        # Disable user interaction during animation
        self.canvas.unbind('<Button-1>')
        self.canvas.unbind('<Button-3>')
        self.canvas.config(cursor="watch")

        # Start animation
        self.animate_next_step()

    def stop_solve_animation(self) -> None:
        """Stop the animation and re-enable user interaction."""
        self.solving_animation_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        # Re-enable user interaction
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.config(cursor="hand2")

        # Reset solve label
        self.solve_label.config(text="Solve steps: 0/0")
        self.update_display()

    def animate_next_step(self) -> None:
        """Animate the next step in the solution."""
        if not self.solving_animation_running:
            return

        if self.animation_index >= len(self.solution_moves):
            # Animation complete
            self.solving_animation_running = False
            self.solve_label.config(text=f"Solve steps: {self.total_moves}/{self.total_moves}")

            # Re-enable user interaction
            self.canvas.bind('<Button-1>', self.on_left_click)
            self.canvas.bind('<Button-3>', self.on_right_click)
            self.canvas.config(cursor="hand2")

            self.update_display()
            if self.logic.check_win():
                self.show_win_message()
            return

        # Get next move
        x, y, rotations = self.solution_moves[self.animation_index]

        # Apply rotation without incrementing user steps
        for _ in range(rotations):
            self.logic.grid[y][x] = self.logic.rotate_direction(self.logic.grid[y][x])

        # Clear rotation cache for this position
        self.logic.rotation_cache.pop((x, y), None)

        self.animation_index += 1
        self.solve_label.config(text=f"Solve steps: {self.animation_index}/{self.total_moves}")

        # Highlight the current tile
        self.update_display(highlight=(x, y))

        # Schedule next step
        if self.solving_animation_running:
            self.after_id = self.root.after(self.animation_speed, self.animate_next_step)

    # ------------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------------

    def on_left_click(self, event) -> None:
        """Handle left click (clockwise rotation)."""
        if self.solving_animation_running:
            messagebox.showinfo("Info", "Please stop the solve animation first!")
            return

        x = event.x // self.cellsize
        y = event.y // self.cellsize

        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.left_rotate_at(x, y):
                self.user_label.config(text=f"User moves: {self.logic.user_move_count}")
                self.update_display()

                if self.logic.check_win():
                    self.show_win_message()

    def on_right_click(self, event) -> None:
        """Handle right click (counter-clockwise rotation)."""
        if self.solving_animation_running:
            messagebox.showinfo("Info", "Please stop the solve animation first!")
            return

        x = event.x // self.cellsize
        y = event.y // self.cellsize

        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.right_rotate_at(x, y):
                self.user_label.config(text=f"User moves: {self.logic.user_move_count}")
                self.update_display()

                if self.logic.check_win():
                    self.show_win_message()

    def on_mouse_move(self, event) -> None:
        """Handle mouse movement for hover effects."""
        x = event.x // self.cellsize
        y = event.y // self.cellsize

        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            # Show tooltip with tile info
            if (x, y) != self.logic.server_pos:
                tile_type = self.logic.tile_types[y][x]
                type_names = {TileType.ENDPOINT: "Endpoint", TileType.JUNCTION: "Junction", TileType.SERVER: "Server"}
                type_name = type_names.get(tile_type, "Unknown")

                connections = self.logic.grid[y][x]
                conn_list = []
                if connections & Direction.UP:
                    conn_list.append("↑")
                if connections & Direction.RIGHT:
                    conn_list.append("→")
                if connections & Direction.DOWN:
                    conn_list.append("↓")
                if connections & Direction.LEFT:
                    conn_list.append("←")

                conn_str = " ".join(conn_list) if conn_list else "None"

                self.show_tooltip(event, f"{type_name}\nConnections: {conn_str}")
            else:
                self.hide_tooltip()
        else:
            self.hide_tooltip()

    def on_mouse_leave(self, event) -> None:
        """Handle mouse leaving the canvas."""
        self.hide_tooltip()

    def show_tooltip(self, event, text: str) -> None:
        """Show a tooltip at mouse position."""
        self.hide_tooltip()

        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        label = tk.Label(
            self.tooltip,
            text=text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9, "bold"),
            padx=3,
            pady=2
        )
        label.pack()

    def hide_tooltip(self) -> None:
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    # ------------------------------------------------------------------------
    # Display Methods
    # ------------------------------------------------------------------------

    def update_display(self, highlight: tuple = None) -> None:
        """Update the game board display."""
        self.draw_grid(highlight)

        # Update status labels
        connected = self.logic.get_connected_cells()
        total = self.logic.width * self.logic.height
        self.status_label.config(text=f"Connected: {len(connected)}/{total}")

        endpoints = self.logic.count_endpoints()
        self.endpoint_label.config(text=f"Endpoints: {endpoints}")

        has_cycles = self.logic.has_cycles()
        cycle_text = "Yes" if has_cycles else "No"
        cycle_color = "#e74c3c" if has_cycles else "#2ecc71"
        self.cycle_label.config(text=f"Cycles: {cycle_text}", fg=cycle_color)

    def draw_grid(self, highlight: tuple = None) -> None:
        """Draw the game grid."""
        self.canvas.delete('all')
        connected = self.logic.get_connected_cells()

        for y in range(self.logic.height):
            for x in range(self.logic.width):
                x1 = x * self.cellsize
                y1 = y * self.cellsize

                is_connected = (x, y) in connected
                is_highlight = (x, y) == highlight
                tile_type = self.logic.tile_types[y][x]

                self.draw_cell(x, y, x1, y1, is_connected, tile_type, is_highlight)

    def draw_cell(self, x: int, y: int, x1: int, y1: int,
                  is_connected: bool, tile_type: int, is_highlight: bool = False) -> None:
        """Draw a single cell."""
        cell_size = self.cellsize
        center_x = x1 + cell_size // 2
        center_y = y1 + cell_size // 2

        # Cell background
        if is_highlight:
            bg_color = '#f1c40f'  # Highlight color
        elif (x, y) == self.logic.server_pos:
            bg_color = '#d35400'  # Server background
        else:
            bg_color = '#ecf0f1'  # Default

        self.canvas.create_rectangle(
            x1, y1, x1 + cell_size, y1 + cell_size,
            fill=bg_color, outline='', width=0
        )

        # Grid lines
        grid_color = '#34495e'
        grid_width = 2

        # Top line
        self.canvas.create_line(x1, y1, x1 + cell_size, y1,
                                fill=grid_color, width=grid_width)
        # Left line
        self.canvas.create_line(x1, y1, x1, y1 + cell_size,
                                fill=grid_color, width=grid_width)

        # Right line (for last column)
        if x == self.logic.width - 1:
            self.canvas.create_line(
                x1 + cell_size, y1, x1 + cell_size, y1 + cell_size,
                fill=grid_color, width=grid_width
            )

        # Bottom line (for last row)
        if y == self.logic.height - 1:
            self.canvas.create_line(
                x1, y1 + cell_size, x1 + cell_size, y1 + cell_size,
                fill=grid_color, width=grid_width
            )

        # Draw connections
        connections = self.logic.grid[y][x]
        if connections == Direction.NONE:
            return

        line_width = max(3, cell_size // 12)
        line_color = "#27ae60" if is_connected else "#7f8c8d"

        if connections & Direction.UP:
            self.canvas.create_line(
                center_x, center_y, center_x, y1,
                fill=line_color, width=line_width, capstyle=tk.ROUND
            )
        if connections & Direction.RIGHT:
            self.canvas.create_line(
                center_x, center_y, x1 + cell_size, center_y,
                fill=line_color, width=line_width, capstyle=tk.ROUND
            )
        if connections & Direction.DOWN:
            self.canvas.create_line(
                center_x, center_y, center_x, y1 + cell_size,
                fill=line_color, width=line_width, capstyle=tk.ROUND
            )
        if connections & Direction.LEFT:
            self.canvas.create_line(
                center_x, center_y, x1, center_y,
                fill=line_color, width=line_width, capstyle=tk.ROUND
            )

        # Draw tile type indicator
        if tile_type == TileType.SERVER:
            size = cell_size // 4
            self.canvas.create_rectangle(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill="#2c3e50", outline='#ecf0f1', width=2
            )
            self.canvas.create_text(
                center_x, center_y,
                text="S",
                fill="white",
                font=('Arial', cell_size // 4, 'bold')
            )
        elif tile_type == TileType.ENDPOINT:
            size = cell_size // 5
            node_color = '#2980b9' if is_connected else '#34495e'
            self.canvas.create_oval(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill=node_color, outline='white', width=2
            )
        elif tile_type == TileType.JUNCTION:
            size = cell_size // 8
            node_color = '#34495e'
            self.canvas.create_oval(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill=node_color, outline='white', width=1
            )

    # ------------------------------------------------------------------------
    # Message Dialogs
    # ------------------------------------------------------------------------

    def show_win_message(self) -> None:
        """Show win message with statistics."""
        moves = self.logic.user_move_count
        total_cells = self.logic.width * self.logic.height

        msg = f"🎉 Congratulations! You solved the puzzle!\n\n"
        msg += f"📊 Statistics:\n"
        msg += f"   • Board size: {self.logic.width}x{self.logic.height}\n"
        msg += f"   • Total moves: {moves}\n"
        msg += f"   • All {total_cells} tiles connected!\n\n"
        msg += f"Would you like to play again?"

        if messagebox.askyesno("Victory!", msg):
            self.new_game()

    def show_help(self) -> None:
        """Show help dialog."""
        help_text = """
🎮 **HOW TO PLAY NET PUZZLE** 🎮

**Objective:**
Connect all tiles to the central server by rotating them to form a continuous network.

**Game Rules:**
• The server (black square with 'S') is the starting point
• All tiles must be connected to form a single network
• No cycles allowed (loops in the network)
• Endpoint tiles (blue circles) must have exactly one connection
• Junction tiles (gray dots) must have 2-4 connections

**Controls:**
• Left Click: Rotate tile clockwise
• Right Click: Rotate tile counter-clockwise
• Hover: Shows tile information
• New Game: Start a fresh puzzle
• Restart: Return to initial scrambled state
• Solve Now: Instant solution display
• Start Animation: Watch step-by-step solution

**Visual Indicators:**
• Green lines: Connected to server
• Gray lines: Not yet connected
• Yellow highlight: Current animation step
• Red "Cycles: Yes" warning: Network contains a loop

**Tips:**
1. Start from the server and work outward
2. Watch for endpoint tiles - they must have only one connection
3. Avoid creating cycles early
4. Use the status bar to track your progress

Good luck! 🍀
        """
        messagebox.showinfo("How to Play", help_text)

    def show_about(self) -> None:
        """Show about dialog."""
        about_text = """
🧩 **NET PUZZLE GAME** 🧩

Version 2.0

A challenging network connection puzzle where you must
rotate tiles to connect everything to the central server.

**Features:**
• Multiple board sizes (5x5 to 11x11)
• Intelligent DC DP solving algorithm
• Step-by-step solution animation
• Real-time connectivity feedback
• Cycle detection

**Implementation:**
• Python with Tkinter
• Divide & Conquer spanning tree generation
• Optimized backtracking solver with memoization

Created as a demonstration of algorithmic puzzle solving.

© 2024
        """
        messagebox.showinfo("About NET Puzzle", about_text)


# ------------------------------------------------------------------------
# Application Entry Point
# ------------------------------------------------------------------------

def main():
    """Main application entry point."""
    root = tk.Tk()

    # Set application icon (if available)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass  # No icon available

    # Center window on screen
    window_width = 800
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    # Set minimum window size
    root.minsize(600, 500)

    # Create and start game
    app = NetGameUI(root, width=7, height=7)

    # Set window title with version
    root.title("NET Puzzle Game v2.0")

    # Start main loop
    root.mainloop()


if __name__ == '__main__':
    main()
