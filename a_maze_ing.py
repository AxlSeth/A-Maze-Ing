import random
import curses

class Maze_Generator:
    def __init__(self, Width: int, Height: int):
        self.width = Width
        self.height = Height
        self.maze = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def draw_cell(self, stdscr, row, col, cell_value, color):
        y = row * 2
        x = col * 2

        max_y, max_x = stdscr.getmaxyx()
        if y + 2 >= max_y or x + 2 >= max_x:
            return

        north = (cell_value & 1) != 0
        east = (cell_value & 2) != 0
        south = (cell_value & 4) != 0
        west = (cell_value & 8) != 0

        up = "─" if north else " "
        down = "─" if south else " "
        right = "│" if east else " "
        left = "│" if west else " "

        stdscr.addstr(y, x, "┌", color)
        stdscr.addstr(y, x+1, up, color)
        stdscr.addstr(y, x+2, "┐", color)

        stdscr.addstr(y+1, x, left, color)
        stdscr.addstr(y+1, x+1, " ", color)
        stdscr.addstr(y+1, x+2, right, color)

        stdscr.addstr(y+2, x, "└", color)
        stdscr.addstr(y+2, x+1, down, color)
        stdscr.addstr(y+2, x+2, "┘", color)

    def draw_maze(self, stdscr, maze, width, height):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

        self.wall_color = curses.color_pair(1)

        stdscr.clear()

        for row in range(height):
            for col in range(width):
                cell_value = maze[row][col]
                self.draw_cell(stdscr, row, col, cell_value, self.wall_color)

        stdscr.refresh()

    def mark_special(self, stdscr, row, col, char, color):
        y = row * 2 + 1
        x = col * 2 + 1

        max_y, max_x = stdscr.getmaxyx()
        if y >= max_y or x >= max_x:
            return

        stdscr.addstr(y, x, char, color)

    def draw_path(self, stdscr, path, entry_row, entry_col):
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        path_color = curses.color_pair(4)

        row, col = entry_row, entry_col

        moves = {
            'N': (-1,  0),
            'S': ( 1,  0),
            'E': ( 0,  1),
            'W': ( 0, -1),
        }

        for direction in path:
            y = row * 2 + 1
            x = col * 2 + 1

            max_y, max_x = stdscr.getmaxyx()
            if y < max_y and x < max_x:
                stdscr.addstr(y, x, "·", path_color)

            dr, dc = moves[direction]
            row += dr
            col += dc

        # dernière case
        y = row * 2 + 1
        x = col * 2 + 1

        max_y, max_x = stdscr.getmaxyx()
        if y < max_y and x < max_x:
            stdscr.addstr(y, x, "·", path_color)

    def set_borders(self):
        for col in range(self.width):
            self.maze[0][col] |= 1
            self.maze[self.height-1][col] |= 4

        for row in range(self.height):
            self.maze[row][0] |= 8
            self.maze[row][self.width-1] |= 2


def load_config(filename):
    config = {}

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            if not line or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key in ["WIDTH", "HEIGHT"]:
                config[key] = int(value)

            elif key in ["ENTRY", "EXIT"]:
                row, col = value.split(",")
                config[key] = (int(row), int(col))

            elif key == "PERFECT":
                config[key] = value.lower() == "true"

            else:
                config[key] = value

    return config


def main(stdscr):
    curses.curs_set(0)

    config = load_config("config.txt")

    width = config["WIDTH"]
    height = config["HEIGHT"]
    entry_row, entry_col = config["ENTRY"]
    exit_row, exit_col = config["EXIT"]

    max_y, max_x = stdscr.getmaxyx()

    needed_y = height * 2 + 1
    needed_x = width * 2 + 1

    if needed_y > max_y or needed_x > max_x:
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal trop petit !")
        stdscr.addstr(1, 0, f"Besoin: {needed_x}x{needed_y}")
        stdscr.addstr(2, 0, f"Actuel: {max_x}x{max_y}")
        stdscr.refresh()
        stdscr.getch()
        return

    maze = Maze_Generator(width, height)

    maze.set_borders()  # optionnel mais utile

    maze.draw_maze(stdscr, maze.maze, width, height)

    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    maze.mark_special(stdscr, entry_row, entry_col, "E", curses.color_pair(2))
    maze.mark_special(stdscr, exit_row, exit_col, "S", curses.color_pair(3))

    stdscr.refresh()
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)