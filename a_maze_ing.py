import random
from mlx import Mlx

CELL_SIZE      = 20
WALL_THICKNESS = 3
COLOR_WALL     = 0xFFFFFF
COLOR_BG       = 0x000000
COLOR_ENTRY    = 0x00FF00
COLOR_EXIT     = 0xFF0000
COLOR_PATH     = 0x00FFFF


class Maze_Generator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.maze = [[0xF for _ in range(width)] for _ in range(height)]

    def set_borders(self):
        for col in range(self.width):
            self.maze[0][col] |= 1
            self.maze[self.height - 1][col] |= 4
        for row in range(self.height):
            self.maze[row][0] |= 8
            self.maze[row][self.width - 1] |= 2

    def generate(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

        self.maze = [[0xF for _ in range(self.width)]
                     for _ in range(self.height)]
        visited = [[False for _ in range(self.width)]
                   for _ in range(self.height)]

        directions = [
            (-1,  0, 1, 4),
            ( 1,  0, 4, 1),
            ( 0,  1, 2, 8),
            ( 0, -1, 8, 2),
        ]

        def carve(row, col):
            visited[row][col] = True
            random.shuffle(directions)
            for dr, dc, bit_cur, bit_nei in directions:
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.height and
                        0 <= nc < self.width and
                        not visited[nr][nc]):
                    self.maze[row][col] &= ~bit_cur
                    self.maze[nr][nc]   &= ~bit_nei
                    carve(nr, nc)

        carve(0, 0)
        self.set_borders()

    def solve(self, entry: tuple, exit_point: tuple) -> list:
        from collections import deque
        sr, sc = entry
        er, ec = exit_point

        queue = deque([(sr, sc, [])])
        visited = [[False] * self.width for _ in range(self.height)]
        visited[sr][sc] = True

        moves = {
            'N': (-1,  0, 1),
            'S': ( 1,  0, 4),
            'E': ( 0,  1, 2),
            'W': ( 0, -1, 8),
        }

        while queue:
            row, col, path = queue.popleft()
            if row == er and col == ec:
                return path
            for direction, (dr, dc, wall_bit) in moves.items():
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.height and
                        0 <= nc < self.width and
                        not visited[nr][nc] and
                        (self.maze[row][col] & wall_bit) == 0):
                    visited[nr][nc] = True
                    queue.append((nr, nc, path + [direction]))
        return []


class MazeDisplay:
    def __init__(self, mg: Maze_Generator, entry: tuple, exit_point: tuple):
        self.mg         = mg
        self.entry      = entry
        self.exit_point = exit_point
        self.show_path  = False
        self.path: list = []

        self.win_w = mg.width  * CELL_SIZE + WALL_THICKNESS
        self.win_h = mg.height * CELL_SIZE + WALL_THICKNESS + 30

        self.mlx     = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.win_w, self.win_h, "A-Maze-ing"
        )

        # IMAGE BUFFER
        self.img = self.mlx.mlx_new_image(self.mlx_ptr, self.win_w, self.win_h)
        self.addr, self.bpp, self.line_len, self.endian = \
            self.mlx.mlx_get_data_addr(self.img)

    def put_pixel(self, x, y, color):
        bytes_per_pixel = self.bpp // 8
        offset = y * self.line_len + x * bytes_per_pixel
        self.addr[offset:offset+4] = color.to_bytes(4, 'little')

    def draw_rect(self, x, y, w, h, color):
        for row in range(h):
            for col in range(w):
                self.put_pixel(x + col, y + row, color)

    def draw_cell(self, row, col, cell_value):
        north = (cell_value & 1) != 0
        east  = (cell_value & 2) != 0
        south = (cell_value & 4) != 0
        west  = (cell_value & 8) != 0

        px = col * CELL_SIZE
        py = row * CELL_SIZE
        T  = WALL_THICKNESS
        C  = CELL_SIZE

        self.draw_rect(px, py, C, C, COLOR_BG)

        if north:
            self.draw_rect(px, py, C, T, COLOR_WALL)
        if south:
            self.draw_rect(px, py + C - T, C, T, COLOR_WALL)
        if west:
            self.draw_rect(px, py, T, C, COLOR_WALL)
        if east:
            self.draw_rect(px + C - T, py, T, C, COLOR_WALL)

    def draw_maze(self):
        # clear image
        self.draw_rect(0, 0, self.win_w, self.win_h, COLOR_BG)

        for row in range(self.mg.height):
            for col in range(self.mg.width):
                self.draw_cell(row, col, self.mg.maze[row][col])

        self.mark_special(*self.entry, COLOR_ENTRY)
        self.mark_special(*self.exit_point, COLOR_EXIT)

        if self.show_path and self.path:
            self.draw_path()

        # PUSH IMAGE → écran
        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img, 0, 0
        )

        # texte (direct window)
        menu_y = self.mg.height * CELL_SIZE + WALL_THICKNESS + 5
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr,
            5, menu_y, COLOR_WALL,
            "1:regen  2:path  ESC:quit"
        )

    def mark_special(self, row, col, color):
        T = WALL_THICKNESS
        C = CELL_SIZE
        px = col * C + T + 1
        py = row * C + T + 1
        size = C - 2 * T - 2
        self.draw_rect(px, py, size, size, color)

    def draw_path(self):
        moves = {'N':(-1,0),'S':(1,0),'E':(0,1),'W':(0,-1)}
        row, col = self.entry
        for d in self.path:
            self.mark_special(row, col, COLOR_PATH)
            dr, dc = moves[d]
            row += dr
            col += dc
        self.mark_special(row, col, COLOR_PATH)

    def run(self):
        def on_loop(param):
            self.draw_maze()

        def on_key(keycode, param):
            if keycode == 49:
                self.mg.generate()
                self.path = self.mg.solve(self.entry, self.exit_point)
                self.show_path = False
            elif keycode == 50:
                self.show_path = not self.show_path
            elif keycode == 65307:
                self.mlx.mlx_loop_exit(self.mlx_ptr)

        self.mlx.mlx_loop_hook(self.mlx_ptr, on_loop, None)
        self.mlx.mlx_key_hook(self.win_ptr, on_key, None)
        self.mlx.mlx_loop(self.mlx_ptr)


def load_config(filename: str) -> dict:
    config = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key   = key.strip()
            value = value.strip()
            if key in ["WIDTH", "HEIGHT"]:
                config[key] = int(value)
            elif key in ["ENTRY", "EXIT"]:
                r, c = value.split(",")
                config[key] = (int(r), int(c))
            else:
                config[key] = value
    return config


if __name__ == "__main__":
    config     = load_config("config.txt")

    mg = Maze_Generator(config["WIDTH"], config["HEIGHT"])
    mg.generate(seed=42)

    display = MazeDisplay(mg, config["ENTRY"], config["EXIT"])
    display.path = mg.solve(config["ENTRY"], config["EXIT"])
    display.run()