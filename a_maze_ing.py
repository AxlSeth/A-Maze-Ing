import random
import sys
import math
from mlx import Mlx

CELL_SIZE       = 28
WALL_THICKNESS  = 4

COLOR_BG        = 0xFF0D0D0D
COLOR_CELL_BG   = 0xFF111122
COLOR_WALL      = 0xFF7C6AF7
COLOR_WALL_GLOW = 0xFF9D8FFF
COLOR_ENTRY     = 0xFF00FF66
COLOR_EXIT      = 0xFFFF4444
COLOR_PATH_START = 0xFF00FFFF
COLOR_PATH_END   = 0xFFFF00FF
COLOR_42        = 0xFFFFD700

PATTERN_4 = [
    [1, 0, 0],
    [1, 0, 0],
    [1, 1, 1],
    [0, 0, 1],
    [0, 0, 1],
]
PATTERN_2 = [
    [1, 1, 1],
    [0, 0, 1],
    [1, 1, 1],
    [1, 0, 0],
    [1, 1, 1],
]
PAT_H = 5
PAT_W = 7


def lerp_color(c1: int, c2: int, t: float) -> int:
    r1 = (c1 >> 16) & 0xFF
    g1 = (c1 >> 8)  & 0xFF
    b1 =  c1        & 0xFF
    r2 = (c2 >> 16) & 0xFF
    g2 = (c2 >> 8)  & 0xFF
    b2 =  c2        & 0xFF
    r  = int(r1 + (r2 - r1) * t)
    g  = int(g1 + (g2 - g1) * t)
    b  = int(b1 + (b2 - b1) * t)
    return 0xFF000000 | (r << 16) | (g << 8) | b


class Maze_Generator:
    def __init__(self, width: int, height: int):
        self.width    = width
        self.height   = height
        self.maze     = [[0xF] * width for _ in range(height)]
        self.generation_order: list = []
        self.has_42   = False
        self.start_row_42 = 0
        self.start_col_42 = 0

    def _42_fits(self) -> bool:
        return self.height >= PAT_H + 4 and self.width >= PAT_W + 4

    def _get_42_origin(self):
        sr = (self.height - PAT_H) // 2
        sc = (self.width  - PAT_W) // 2
        return sr, sc

    def _42_cells(self):
        """Retourne la liste de (row, col) de toutes les cellules du 42."""
        if not self._42_fits():
            return []
        sr, sc = self._get_42_origin()
        cells = []
        for r, row in enumerate(PATTERN_4):
            for c, cell in enumerate(row):
                if cell:
                    cells.append((sr + r, sc + c))
        for r, row in enumerate(PATTERN_2):
            for c, cell in enumerate(row):
                if cell:
                    cells.append((sr + r, sc + 4 + c))
        return cells

    def place_42_visited(self, visited: list) -> None:
        for r, c in self._42_cells():
            visited[r][c] = True

    def place_42(self) -> None:
        if not self._42_fits():
            print("Labyrinthe trop petit pour afficher le pattern '42'")
            self.has_42 = False
            return
        sr, sc = self._get_42_origin()
        self.start_row_42 = sr
        self.start_col_42 = sc
        for r, c in self._42_cells():
            self.maze[r][c] = 0xF
        self.has_42 = True

    def set_borders(self) -> None:
        for col in range(self.width):
            self.maze[0][col]               |= 1
            self.maze[self.height - 1][col] |= 4
        for row in range(self.height):
            self.maze[row][0]              |= 8
            self.maze[row][self.width - 1] |= 2

    def generate(self, seed: int = None) -> None:
        if seed is not None:
            random.seed(seed)
        self.maze = [[0xF] * self.width for _ in range(self.height)]
        self.generation_order = []
        visited    = [[False] * self.width for _ in range(self.height)]
        directions = [(-1,0,1,4),(1,0,4,1),(0,1,2,8),(0,-1,8,2)]

        self.place_42_visited(visited)

        def carve(row: int, col: int) -> None:
            visited[row][col] = True
            self.generation_order.append((row, col))
            random.shuffle(directions)
            for dr, dc, bit_cur, bit_nei in directions:
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.height and
                        0 <= nc < self.width and
                        not visited[nr][nc]):
                    self.maze[row][col] &= ~bit_cur
                    self.maze[nr][nc]   &= ~bit_nei
                    carve(nr, nc)

        sys.setrecursionlimit(self.width * self.height * 2)
        carve(0, 0)
        self.set_borders()
        self.place_42()

    def solve(self, entry: tuple, exit_point: tuple) -> list:
        from collections import deque
        sr, sc = entry
        er, ec = exit_point
        queue   = deque([(sr, sc, [])])
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
    def __init__(self, mg: Maze_Generator,
                 entry: tuple, exit_point: tuple):
        self.mg          = mg
        self.entry       = entry
        self.exit_point  = exit_point
        self.show_path   = False
        self.path: list  = []
        self.animating   = False
        self.anim_index  = 0
        self.pulse_t     = 0.0

        self.win_w = mg.width  * CELL_SIZE + WALL_THICKNESS
        self.win_h = mg.height * CELL_SIZE + WALL_THICKNESS + 35

        self.mlx     = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.win_w, self.win_h, "A-Maze-ing"
        )
        self.img = self.mlx.mlx_new_image(
            self.mlx_ptr, self.win_w, self.win_h
        )
        self.addr, self.bpp, self.line_len, _ = \
            self.mlx.mlx_get_data_addr(self.img)

    # ── Primitives ───────────────────────────────────────────────

    def put_pixel(self, x: int, y: int, color: int) -> None:
        if 0 <= x < self.win_w and 0 <= y < self.win_h:
            off = y * self.line_len + x * (self.bpp // 8)
            self.addr[off:off+4] = color.to_bytes(4, 'little')

    def draw_rect(self, x: int, y: int,
                  w: int, h: int, color: int) -> None:
        for row in range(h):
            for col in range(w):
                self.put_pixel(x + col, y + row, color)

    def draw_rect_glow(self, x: int, y: int,
                       w: int, h: int, color: int) -> None:
        self.draw_rect(x, y, w, h, color)
        for i in range(1):
            self.put_pixel(x + i,     y + i,     COLOR_WALL_GLOW)
            self.put_pixel(x + w-1-i, y + i,     COLOR_WALL_GLOW)
            self.put_pixel(x + i,     y + h-1-i, COLOR_WALL_GLOW)
            self.put_pixel(x + w-1-i, y + h-1-i, COLOR_WALL_GLOW)

    def draw_circle(self, cx: int, cy: int,
                    r: int, color: int) -> None:
        for dy in range(-r, r + 1):
            dx_max = int((r * r - dy * dy) ** 0.5)
            for dx in range(-dx_max, dx_max + 1):
                self.put_pixel(cx + dx, cy + dy, color)

    # ── Cellule ──────────────────────────────────────────────────

    def draw_cell(self, row: int, col: int,
                  cell_value: int, highlight: bool = False) -> None:
        north = (cell_value & 1) != 0
        east  = (cell_value & 2) != 0
        south = (cell_value & 4) != 0
        west  = (cell_value & 8) != 0

        px = col * CELL_SIZE
        py = row * CELL_SIZE
        T  = WALL_THICKNESS
        C  = CELL_SIZE

        bg = 0xFF1A1A3A if highlight else COLOR_CELL_BG
        self.draw_rect(px, py, C, C, bg)

        wall = COLOR_WALL_GLOW if highlight else COLOR_WALL
        if north:
            self.draw_rect_glow(px, py, C, T, wall)
        if south:
            self.draw_rect_glow(px, py + C - T, C, T, wall)
        if west:
            self.draw_rect_glow(px, py, T, C, wall)
        if east:
            self.draw_rect_glow(px + C - T, py, T, C, wall)

    # ── Pattern 42 ───────────────────────────────────────────────

    def draw_42(self) -> None:
        """Colorie les cellules du pattern 42 en doré."""
        if not self.mg.has_42:
            return
        C = CELL_SIZE
        T = WALL_THICKNESS
        for r, c in self.mg._42_cells():
            px = c * C + T + 1
            py = r * C + T + 1
            sz = C - 2 * T - 2
            self.draw_rect(px, py, sz, sz, COLOR_42)
            # bordure intérieure plus foncée pour le relief
            border = 0xFFB8860B
            self.draw_rect(px, py, sz, 1, border)
            self.draw_rect(px, py + sz - 1, sz, 1, border)
            self.draw_rect(px, py, 1, sz, border)
            self.draw_rect(px + sz - 1, py, 1, sz, border)

    # ── Marqueurs entrée / sortie ────────────────────────────────

    def draw_marker(self, row: int, col: int,
                    color: int, pulse: float = 0.0) -> None:
        C  = CELL_SIZE
        T  = WALL_THICKNESS
        cx = col * C + C // 2
        cy = row * C + C // 2
        halo_r  = int((C // 2 - T - 1) * (1.0 + 0.2 * pulse))
        halo_c  = lerp_color(color, COLOR_BG, 0.65)
        self.draw_circle(cx, cy, halo_r, halo_c)
        main_r  = max(2, C // 2 - T - 3)
        self.draw_circle(cx, cy, main_r, color)

    # ── Chemin gradient ──────────────────────────────────────────

    def draw_path_gradient(self) -> None:
        moves = {'N':(-1,0),'S':(1,0),'E':(0,1),'W':(0,-1)}
        row, col = self.entry
        cells    = [(row, col)]
        for d in self.path:
            dr, dc = moves[d]
            row   += dr
            col   += dc
            cells.append((row, col))

        total = max(1, len(cells) - 1)
        C = CELL_SIZE
        T = WALL_THICKNESS

        for i, (r, c) in enumerate(cells):
            t     = i / total
            color = lerp_color(COLOR_PATH_START, COLOR_PATH_END, t)
            cx    = c * C + C // 2
            cy    = r * C + C // 2
            self.draw_circle(cx, cy, C // 2 - T - 2, color)

        pulse = math.sin(self.pulse_t * 3) * 0.5 + 0.5
        self.draw_marker(*self.entry,      COLOR_ENTRY, pulse)
        self.draw_marker(*self.exit_point, COLOR_EXIT,  pulse)

    # ── Fond ─────────────────────────────────────────────────────

    def draw_background(self) -> None:
        size = self.line_len * self.win_h
        self.addr[0:size] = b'\x0d\x0d\x0d\xff' * (size // 4)
        GRID = 0xFF161616
        for r in range(0, self.win_h, CELL_SIZE):
            for x in range(self.win_w):
                self.put_pixel(x, r, GRID)
        for c in range(0, self.win_w, CELL_SIZE):
            for y in range(self.win_h):
                self.put_pixel(c, y, GRID)

    # ── Frame ────────────────────────────────────────────────────

    def draw_maze(self) -> None:
        self.pulse_t += 0.05
        pulse = math.sin(self.pulse_t) * 0.5 + 0.5

        self.draw_background()

        if self.animating:
            step = min(self.anim_index,
                       len(self.mg.generation_order))
            for i in range(step):
                r, c      = self.mg.generation_order[i]
                highlight = (i == step - 1)
                self.draw_cell(r, c,
                               self.mg.maze[r][c], highlight)
            self.anim_index += 3
            if self.anim_index >= len(self.mg.generation_order):
                self.animating = False
                self.draw_42()
        else:
            for row in range(self.mg.height):
                for col in range(self.mg.width):
                    self.draw_cell(row, col,
                                   self.mg.maze[row][col])
            # 42 toujours visible par-dessus les cellules
            self.draw_42()

            if self.show_path and self.path:
                self.draw_path_gradient()
            else:
                self.draw_marker(*self.entry,      COLOR_ENTRY, pulse)
                self.draw_marker(*self.exit_point, COLOR_EXIT,  pulse)

        self.mlx.mlx_put_image_to_window(
            self.mlx_ptr, self.win_ptr, self.img, 0, 0
        )
        menu_y = self.mg.height * CELL_SIZE + WALL_THICKNESS + 8
        self.mlx.mlx_string_put(
            self.mlx_ptr, self.win_ptr,
            5, menu_y, COLOR_WALL,
            "1:regen   2:path   ESC:quit"
        )

    # ── Boucle ───────────────────────────────────────────────────

    def run(self) -> None:
        def loop(_: object) -> None:
            self.draw_maze()

        def key(keycode: int, _: object) -> None:
            if keycode == 49:
                self.mg.generate()
                self.path      = self.mg.solve(
                    self.entry, self.exit_point)
                self.show_path = False
                self.animating = True
                self.anim_index = 0
            elif keycode == 50:
                self.show_path = not self.show_path
            elif keycode == 65307:
                self.mlx.mlx_loop_exit(self.mlx_ptr)

        def on_close(_: object) -> None:
            self.mlx.mlx_loop_exit(self.mlx_ptr)

        self.animating  = True
        self.anim_index = 0

        self.mlx.mlx_loop_hook(self.mlx_ptr, loop, None)
        self.mlx.mlx_key_hook(self.win_ptr,  key,  None)
        self.mlx.mlx_hook(self.win_ptr, 33, 0, on_close, None)
        self.mlx.mlx_loop(self.mlx_ptr)

        self.mlx.mlx_destroy_image(self.mlx_ptr, self.img)
        self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
        self.mlx.mlx_release(self.mlx_ptr)


def load_config(filename: str) -> dict:
    config: dict = {}
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
    return config


if __name__ == "__main__":
    config  = load_config("config.txt")
    mg      = Maze_Generator(config["WIDTH"], config["HEIGHT"])
    mg.generate(seed=42)
    display = MazeDisplay(mg, config["ENTRY"], config["EXIT"])
    display.path = mg.solve(config["ENTRY"], config["EXIT"])
    display.run()