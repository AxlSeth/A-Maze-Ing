import random
import  curses
class Maze_Generator:
    def __init__(self, Width: int, Height: int):
        self.width = Width
        self.height = Height

    def draw_cell (self, stdscr, row, col, cell_value, color):
        y = row * 2
        x = col * 2

        north = (cell_value & 1) != 0
        east = (cell_value & 2) != 0
        south = (cell_value & 4) != 0
        west = (cell_value & 8) != 0

        up  = "─" if north  else " ", 
        down   = "─" if south   else " "
        right = "│" if east   else " "
        left = "│" if west else " "
    
        stdscr.addstr(y, x, "┌", color)
        stdscr.addstr(y, x + 1, up, color)
        stdscr.addstr(y, x + 2, "┐", color)

        stdscr.addstr(y + 1, x, left, color)
        stdscr.addstr(y + 1, x + 1, " ", color)
        stdscr.addstr(y + 1, x + 2, right, color)

        stdscr.addstr(y + 2, x, "└", color)
        stdscr.addstr(y + 2, x + 1, down, color)
        stdscr.addstr(y + 2, x + 2, "┘", color)
    def generate_maze(self, stdcr, maze, width, height):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

        wall_color = curses.color_pair(1)

        for row in range(height):
            for col in range(width):
                cell_value = maze[row][col]
                self.draw_cell(stdcr, row, col, cell_value, wall_color)
        