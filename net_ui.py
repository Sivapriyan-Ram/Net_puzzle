"""
Tkinter user interface for the NET pipe-connection puzzle (no undo/redo).

This module is responsible only for:
- Creating and laying out widgets
- Drawing the grid on a Canvas
- Converting mouse events to calls into NetGameLogic
- Triggering greedy solver animations
"""

import tkinter as tk
from tkinter import messagebox

from net_logic import NetGameLogic, Direction, TileType


class NetGameUI:
    """
    Main GUI class that binds Tkinter widgets to NetGameLogic.
    """

    def __init__(self, root: tk.Tk, width: int = 7, height: int = 7) -> None:
        """
        Build the full window UI and start with an initial game.
        """
        self.root = root
        self.root.title("NET Puzzle Game")
        self.root.configure(bg="#09c3f2")

        # Create logic layer
        self.logic = NetGameLogic(width=width, height=height)
        self.cell_size = self.logic.cell_size

        # Animation state (separate from logic)
        self.solving_animation_running = False
        self.greedy_solution_moves = []
        self.greedy_animation_index = 0
        self.greedy_step_count = 0

        # --------------------- Layout: frames and menus ---------------------
        main_frame = tk.Frame(root, bg="#09c3f2")
        main_frame.pack(padx=20, pady=20)

        control_frame = tk.Frame(main_frame, bg='#09c3f2')
        control_frame.pack(pady=(0, 10))

        # Menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New game", command=self.new_game)
        game_menu.add_command(label="Restart game", command=self.restart_game)
        game_menu.add_separator()
        # Removed Undo/Redo menu entries
        game_menu.add_command(label="Solve game", command=self.solve_now)

        # Difficulty / grid size
        type_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Type", menu=type_menu)

        self.difficulty_var = tk.StringVar(value="7x7")
        for size_name, w, h in [("5x5", 5, 5), ("7x7", 7, 7),
                                ("9x9", 9, 9), ("11x11", 11, 11)]:
            type_menu.add_radiobutton(
                label=size_name,
                variable=self.difficulty_var,
                value=size_name,
                command=lambda w=w, h=h: self.change_size(w, h)
            )

        # Button row
        btn_frame = tk.Frame(control_frame, bg='#09c3f2')
        btn_frame.pack()

        btn_style = {
            'font': ('Arial', 10),
            'bg': '#3498db',
            'fg': 'white',
            'padx': 10,
            'pady': 5,
            'relief': tk.RAISED,
            'cursor': 'hand2'
        }

        tk.Button(btn_frame, text="New game", command=self.new_game,
                  **btn_style).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Restart game", command=self.restart_game,
                  **btn_style).pack(side=tk.LEFT, padx=3)

        # Solve now: apply entire greedy plan instantly
        tk.Button(btn_frame, text="Solve now", command=self.solve_now,
                  bg="#068f28", fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        # Start / stop animated solving
        tk.Button(btn_frame, text="Start solve", command=self.start_solve_step,
                  bg='#e74c3c', fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame, text="Stop solve", command=self.stop_solve_step,
                  bg='#c0392b', fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        # Status panel (Active tiles, user steps, greedy steps)
        status_frame = tk.Frame(main_frame, bg='#09c3f2')
        status_frame.pack(pady=5)

        self.status_label = tk.Label(
            status_frame,
            text="Active: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.user_label = tk.Label(
            status_frame,
            text="User steps: 0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.user_label.pack(side=tk.RIGHT, padx=10)

        self.greedy_label = tk.Label(
            status_frame,
            text="DC steps: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.greedy_label.pack(side=tk.RIGHT, padx=10)

        # Canvas for drawing grid
        canvas_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.SUNKEN, bd=2)
        canvas_frame.pack()

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.logic.width * self.cell_size,
            height=self.logic.height * self.cell_size,
            bg="#e1ae38",
            highlightthickness=0
        )
        self.canvas.pack()

        # Mouse bindings: L/R click rotate tiles, middle currently unused
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Button-2>', self.on_middle_click)

        # Draw initial game state
        self.update_display()

    # ------------------------------------------------------------------
    # UI actions wired to logic
    # ------------------------------------------------------------------
    def change_size(self, width: int, height: int) -> None:
        """
        Called when user selects a different grid size from the menu.
        """
        self.logic.change_size(width, height)
        self.canvas.config(width=self.logic.width * self.cell_size,
                           height=self.logic.height * self.cell_size)
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.greedy_label.config(text="DC steps: 0/0")
        self.update_display()

    def new_game(self) -> None:
        """
        Create a completely new random puzzle.
        """
        self.stop_solve_step()
        self.logic.new_game()
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.greedy_label.config(text="DC steps: 0/0")
        self.update_display()

    def restart_game(self) -> None:
        """
        Reset current puzzle to its initial scrambled state.
        """
        self.stop_solve_step()
        self.logic.restart_game()
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.greedy_label.config(text="DC steps: 0/0")
        self.update_display()

    # ------------------------------------------------------------------
    # Solver controls
    # ------------------------------------------------------------------
    def start_solve_step(self) -> None:
        """
        Start step-by-step greedy animation (1 step per second).
        """
        if self.solving_animation_running:
            return

        # Compute full greedy plan once, then animate through it
        moves = self.logic.greedy_solve_full(self.logic.grid)
        self.greedy_solution_moves = moves
        self.greedy_step_count = len(moves)
        self.greedy_animation_index = 0
        self.greedy_label.config(text=f"DC steps: 0/{self.greedy_step_count}")

        if self.greedy_step_count == 0:
            return

        self.solving_animation_running = True
        self.animate_greedy_step()

    def stop_solve_step(self) -> None:
        """
        Stop the step-by-step solver animation.
        """
        self.solving_animation_running = False

    def solve_now(self) -> None:
        """
        Immediately apply the full greedy solution (no animation).
        """
        if self.solving_animation_running:
            self.stop_solve_step()

        moves = self.logic.greedy_solve_full(self.logic.grid)
        for x, y, direction in moves:
            if direction == 'cw':
                self.logic.grid[y][x] = self.logic.rotate_direction(self.logic.grid[y][x])
            else:
                self.logic.grid[y][x] = self.logic.rotate_direction_ccw(self.logic.grid[y][x])

        self.greedy_step_count = len(moves)
        self.greedy_label.config(
            text=f"DC steps: {self.greedy_step_count}/{self.greedy_step_count}"
        )
        self.update_display()

    def animate_greedy_step(self) -> None:
        """
        Execute one greedy move and schedule the next one in 1000 ms.
        """
        if not self.solving_animation_running:
            return

        if self.greedy_animation_index >= len(self.greedy_solution_moves):
            # Reached end of plan
            self.solving_animation_running = False
            self.update_display()
            return

        x, y, direction = self.greedy_solution_moves[self.greedy_animation_index]
        if direction == 'cw':
            self.logic.grid[y][x] = self.logic.rotate_direction(self.logic.grid[y][x])
        else:
            self.logic.grid[y][x] = self.logic.rotate_direction_ccw(self.logic.grid[y][x])

        self.greedy_animation_index += 1
        self.greedy_label.config(
            text=f"DC steps: {self.greedy_animation_index}/{self.greedy_step_count}"
        )
        self.update_display()

        if self.solving_animation_running:
            # Schedule next step
            self.root.after(1000, self.animate_greedy_step)

    # ------------------------------------------------------------------
    # Mouse event handlers
    # ------------------------------------------------------------------
    def on_left_click(self, event) -> None:
        """
        Rotate the clicked tile clockwise (user move).
        """
        if self.solving_animation_running:
            return

        x = event.x // self.cell_size
        y = event.y // self.cell_size
        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.left_rotate_at(x, y):
                self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
                self.update_display()
                if self.logic.check_win():
                    self.show_win_message()

    def on_right_click(self, event) -> None:
        """
        Rotate the clicked tile counter-clockwise (user move).
        """
        if self.solving_animation_running:
            return

        x = event.x // self.cell_size
        y = event.y // self.cell_size
        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.right_rotate_at(x, y):
                self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
                self.update_display()
                if self.logic.check_win():
                    self.show_win_message()

    def on_middle_click(self, event) -> None:
        """
        Placeholder for future middle click behavior.
        """
        pass

    # ------------------------------------------------------------------
    # Win message and drawing
    # ------------------------------------------------------------------
    def show_win_message(self) -> None:
        """
        Show a simple message box when the puzzle is solved.
        """
        messagebox.showinfo("Congratulations!", "Puzzle completed!")

    def update_display(self) -> None:
        """
        Redraw the entire grid and update status label (Active: X/Y).
        """
        self.draw_grid()
        connected = self.logic.get_connected_cells()
        total = sum(
            1 for y in range(self.logic.height)
            for x in range(self.logic.width)
            if self.logic.grid[y][x] != Direction.NONE
        )
        self.status_label.config(text=f"Active: {len(connected)}/{total}")

    def draw_grid(self) -> None:
        """
        Clear the canvas and draw every cell (background, pipes, nodes).
        """
        self.canvas.delete('all')
        connected = self.logic.get_connected_cells()
        for y in range(self.logic.height):
            for x in range(self.logic.width):
                x1 = x * self.cell_size
                y1 = y * self.cell_size
                is_connected = (x, y) in connected
                tile_type = self.logic.tile_types[y][x]
                self.draw_cell(x, y, x1, y1, is_connected, tile_type)

    def draw_cell(self, x: int, y: int, x1: int, y1: int,
                  is_connected: bool, tile_type: int) -> None:
        """
        Draw one cell: background, grid borders, pipes and node marker.
        """
        cell_size = self.cell_size
        center_x = x1 + cell_size // 2
        center_y = y1 + cell_size // 2

        # Cell background
        bg_color = '#e1ae38'
        self.canvas.create_rectangle(
            x1, y1, x1 + cell_size, y1 + cell_size,
            fill=bg_color, outline=''
        )

        # Outer grid lines
        barrier_color = '#34495e'
        barrier_width = 3
        self.canvas.create_line(x1, y1, x1 + cell_size, y1,
                                fill=barrier_color, width=barrier_width)
        self.canvas.create_line(x1, y1, x1, y1 + cell_size,
                                fill=barrier_color, width=barrier_width)
        if x == self.logic.width - 1:
            self.canvas.create_line(
                x1 + cell_size, y1, x1 + cell_size, y1 + cell_size,
                fill=barrier_color, width=barrier_width
            )
        if y == self.logic.height - 1:
            self.canvas.create_line(
                x1, y1 + cell_size, x1 + cell_size, y1 + cell_size,
                fill=barrier_color, width=barrier_width
            )

        # Pipe lines
        connections = self.logic.grid[y][x]
        if connections == Direction.NONE:
            return

        line_width = 6
        # Connected pipes are green, others orange
        line_color = "#16a022" if is_connected else "#ce851f"

        if connections & Direction.UP:
            self.canvas.create_line(
                center_x, center_y, center_x, y1,
                fill=line_color, width=line_width
            )
        if connections & Direction.RIGHT:
            self.canvas.create_line(
                center_x, center_y, x1 + cell_size, center_y,
                fill=line_color, width=line_width
            )
        if connections & Direction.DOWN:
            self.canvas.create_line(
                center_x, center_y, center_x, y1 + cell_size,
                fill=line_color, width=line_width
            )
        if connections & Direction.LEFT:
            self.canvas.create_line(
                center_x, center_y, x1, center_y,
                fill=line_color, width=line_width
            )

        # Node markers (server, endpoint, junction)
        if tile_type == TileType.SERVER:
            size = 14
            self.canvas.create_rectangle(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill="#000000", outline=''
            )
        elif tile_type == TileType.ENDPOINT:
            size = 12
            node_color = '#3498db' if is_connected else '#34495e'
            self.canvas.create_rectangle(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill=node_color, outline=''
            )
        else:  # JUNCTION or any other type
            size = 6
            node_color = '#34495e'
            self.canvas.create_oval(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill=node_color, outline=''
            )


if __name__ == '__main__':
    # Entry point: create Tk root and start the UI.
    root = tk.Tk()
    game = NetGameUI(root, width=7, height=7)
    root.mainloop()



