import tkinter as tk
from tkinter import messagebox
from net_logic import NetGameLogic, Direction, TileType


class NetGameUI:

    def __init__(self, root: tk.Tk, width: int = 7, height: int = 7) -> None:

        self.root = root
        self.root.title("NET Puzzle Game")
        self.root.configure(bg="#09c3f2")

        self.logic = NetGameLogic(width=width, height=height)
        self.cellsize = self.logic.cellsize

        self.solving_animation_running = False
        self.solution_moves = []  # Will store list of (x, y, rotations) tuples
        self.animation_index = 0
        self.total_moves = 0
        self.animation_speed = 500
        self.after_id = None
        self.initial_grid = None  # Store initial scrambled grid for restart

        main_frame = tk.Frame(root, bg="#09c3f2")
        main_frame.pack(padx=20, pady=20)

        control_frame = tk.Frame(main_frame, bg='#09c3f2')
        control_frame.pack(pady=(0, 10))

        menubar = tk.Menu(root)
        root.config(menu=menubar)

        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New game", command=self.new_game)
        game_menu.add_command(label="Restart game", command=self.restart_game)
        game_menu.add_separator()
        game_menu.add_command(label="Solve game", command=self.solve_now)

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

        tk.Button(btn_frame, text="Solve now", command=self.solve_now,
                  bg="#068f28", fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame, text="Start solve", command=self.start_solve_animation,
                  bg='#e74c3c', fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        tk.Button(btn_frame, text="Stop solve", command=self.stop_solve_animation,
                  bg='#c0392b', fg='white', font=('Arial', 10),
                  padx=10, pady=5, relief=tk.RAISED,
                  cursor='hand2').pack(side=tk.LEFT, padx=3)

        # Speed control
        speed_frame = tk.Frame(control_frame, bg='#09c3f2')
        speed_frame.pack(pady=5)
        
        tk.Label(speed_frame, text="Animation speed:", bg='#09c3f2', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=500)
        speed_scale = tk.Scale(speed_frame, from_=100, to=1000, orient=tk.HORIZONTAL,
                              variable=self.speed_var, length=200, bg='#09c3f2',
                              command=self.update_speed)
        speed_scale.pack(side=tk.LEFT)

        status_frame = tk.Frame(main_frame, bg='#09c3f2')
        status_frame.pack(pady=5)

        self.status_label = tk.Label(
            status_frame,
            text="Connected: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.endpoint_label = tk.Label(
            status_frame,
            text="Endpoints: 0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.endpoint_label.pack(side=tk.LEFT, padx=10)

        self.cycle_label = tk.Label(
            status_frame,
            text="Cycles: No",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.cycle_label.pack(side=tk.LEFT, padx=10)

        self.user_label = tk.Label(
            status_frame,
            text="User steps: 0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.user_label.pack(side=tk.RIGHT, padx=10)

        self.solve_label = tk.Label(
            status_frame,
            text="Solve steps: 0/0",
            font=('Arial', 11, 'bold'),
            bg='#09c3f2',
            fg="#000000"
        )
        self.solve_label.pack(side=tk.RIGHT, padx=10)

        canvas_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.SUNKEN, bd=2)
        canvas_frame.pack()

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.logic.width * self.cellsize,
            height=self.logic.height * self.cellsize,
            bg="#e1ae38",
            highlightthickness=0
        )
        self.canvas.pack()

        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-3>', self.on_right_click)

        # Store initial grid after creation
        self.initial_grid = self.logic.clone_grid(self.logic.grid)
        self.update_display()

    def change_size(self, width: int, height: int) -> None:
        self.stop_solve_animation()
        self.logic.change_size(width, height)
        self.cellsize = self.logic.cellsize
        self.canvas.config(width=self.logic.width * self.cellsize,
                           height=self.logic.height * self.cellsize)
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")
        self.initial_grid = self.logic.clone_grid(self.logic.grid)  # Store new initial grid
        self.update_display()

    def new_game(self) -> None:
        self.stop_solve_animation()
        self.logic.new_game()
        self.cellsize = self.logic.cellsize
        self.canvas.config(width=self.logic.width * self.cellsize,
                           height=self.logic.height * self.cellsize)
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")
        self.initial_grid = self.logic.clone_grid(self.logic.grid)  # Store new initial grid
        self.update_display()

    def restart_game(self) -> None:
        """Restart the game to the initial scrambled state"""
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
        self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
        self.solve_label.config(text="Solve steps: 0/0")
        self.update_display()

    def update_speed(self, value):
        self.animation_speed = int(value)

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
        """Start step-by-step animation of the solution - does NOT increment user steps."""
        if self.solving_animation_running:
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
        
        # Reset solve label
        self.solve_label.config(text="Solve steps: 0/0")
        self.update_display()

    def animate_next_step(self) -> None:
        """Animate the next step in the solution - does NOT increment user steps."""
        if not self.solving_animation_running:
            return
        
        if self.animation_index >= len(self.solution_moves):
            # Animation complete
            self.solving_animation_running = False
            self.solve_label.config(text=f"Solve steps: {self.total_moves}/{self.total_moves}")
            
            # Re-enable user interaction
            self.canvas.bind('<Button-1>', self.on_left_click)
            self.canvas.bind('<Button-3>', self.on_right_click)
            
            self.update_display()
            if self.logic.check_win():
                self.show_win_message()
            return
        
        # Get next move
        x, y, rotations = self.solution_moves[self.animation_index]
        
        # Apply rotation without incrementing user steps
        for _ in range(rotations):
            # Directly manipulate the grid to avoid user step increment
            self.logic.grid[y][x] = self.logic.rotate_direction(self.logic.grid[y][x])
        
        # Clear rotation cache for this position
        self.logic.rotation_cache.pop((x, y), None)
        
        self.animation_index += 1
        self.solve_label.config(text=f"Solve steps: {self.animation_index}/{self.total_moves}")
        self.update_display()
        
        # Schedule next step
        if self.solving_animation_running:
            self.after_id = self.root.after(self.animation_speed, self.animate_next_step)

    def on_left_click(self, event) -> None:
        if self.solving_animation_running:
            messagebox.showinfo("Info", "Please stop the solve animation first!")
            return

        x = event.x // self.cellsize
        y = event.y // self.cellsize
        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.left_rotate_at(x, y):
                self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
                self.update_display()
                if self.logic.check_win():
                    self.show_win_message()

    def on_right_click(self, event) -> None:
        if self.solving_animation_running:
            messagebox.showinfo("Info", "Please stop the solve animation first!")
            return

        x = event.x // self.cellsize
        y = event.y // self.cellsize
        if 0 <= x < self.logic.width and 0 <= y < self.logic.height:
            if self.logic.right_rotate_at(x, y):
                self.user_label.config(text=f"User steps: {self.logic.user_move_count}")
                self.update_display()
                if self.logic.check_win():
                    self.show_win_message()

    def show_win_message(self) -> None:
        messagebox.showinfo("Congratulations!", "Puzzle completed!")

    def update_display(self) -> None:
        self.draw_grid()
        connected = self.logic.get_connected_cells()
        total = self.logic.width * self.logic.height
        self.status_label.config(text=f"Connected: {len(connected)}/{total}")
        
        endpoints = self.logic.count_endpoints()
        self.endpoint_label.config(text=f"Endpoints: {endpoints}")
        
        has_cycles = self.logic.has_cycles()
        cycle_text = "Yes" if has_cycles else "No"
        cycle_color = "#e74c3c" if has_cycles else "#2ecc71"
        self.cycle_label.config(text=f"Cycles: {cycle_text}", fg=cycle_color)

    def draw_grid(self) -> None:
        self.canvas.delete('all')
        connected = self.logic.get_connected_cells()
        for y in range(self.logic.height):
            for x in range(self.logic.width):
                x1 = x * self.cellsize
                y1 = y * self.cellsize
                is_connected = (x, y) in connected
                tile_type = self.logic.tile_types[y][x]
                self.draw_cell(x, y, x1, y1, is_connected, tile_type)

    def draw_cell(self, x: int, y: int, x1: int, y1: int,
                  is_connected: bool, tile_type: int) -> None:

        cell_size = self.cellsize
        center_x = x1 + cell_size // 2
        center_y = y1 + cell_size // 2

        # Cell background
        bg_color = '#e1ae38'
        self.canvas.create_rectangle(
            x1, y1, x1 + cell_size, y1 + cell_size,
            fill=bg_color, outline=''
        )

        # Grid lines
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

        # Draw connections
        connections = self.logic.grid[y][x]
        if connections == Direction.NONE:
            return

        line_width = 6
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

        # Draw tile type indicator
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
        else:  # JUNCTION
            size = 6
            node_color = '#34495e'
            self.canvas.create_oval(
                center_x - size, center_y - size,
                center_x + size, center_y + size,
                fill=node_color, outline=''
            )


if __name__ == '__main__':
    root = tk.Tk()
    game = NetGameUI(root, width=7, height=7)
    root.mainloop()
