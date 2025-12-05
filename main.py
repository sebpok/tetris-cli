import time
import keyboard
import threading
from copy import deepcopy
from assets import ascii
from keyboard._keyboard_event import KeyboardEvent
from pieces import Piece

SPEED = 0.4  # in seconds (how fast we render next frame), lower = faster
ACC_SPEED = 0.05
BOARD_X_SIZE = 10 
BOARD_Y_SIZE = 24 
BOARD_BUFFOR_SIZE = 2

class Game:
    def __init__(self) -> None:
        self.board = []
        self.temp_board = []
        self.board_max_y = BOARD_Y_SIZE 
        self.board_max_x = BOARD_X_SIZE 
        self.buffor_y_size = BOARD_BUFFOR_SIZE 
        self.game_speed = SPEED
        self.active_piece: Piece

        self.points = 0
        self.level = 0
        self.points_per_line = 40 

        self.lock = threading.Lock()
        self.stop_game = threading.Event()
        self.main_thread = threading.Thread(target=self.main, daemon=True)
        self.keyboard_hook = None

        for _ in range(self.board_max_y):
            row = []
            for _ in range(self.board_max_x):
                row.append(0)
            self.board.append(row)
        self.temp_board = deepcopy(self.board)

    def main(self) -> None:
        self.spawn_piece()
        while not self.stop_game.is_set():
            while True:
                self.show_active_piece()
                self.render_board()
                time.sleep(self.game_speed)

                if self.is_floor_collision() or self.is_block_collision():
                    break

                self.hide_active_piece()
                self.active_piece.move_down()

            self.check_rows()

            if self.is_gameover():
                self.stop_game.set()
                self.render_gameover()
                break

            self.spawn_piece()

    def keyboard(self, e: KeyboardEvent) -> None:
        if e.name == "h" or e.name == "left":
            if e.event_type == keyboard.KEY_UP:
                if self.can_move_left():
                    self.hide_active_piece()
                    self.active_piece.x -= 1
                    self.show_active_piece()
                    self.render_board()

        elif e.name == "l" or e.name == "right":
            if e.event_type == keyboard.KEY_UP:
                if self.can_move_right():
                    self.hide_active_piece()
                    self.active_piece.x += 1
                    self.show_active_piece()
                    self.render_board()

        if e.name == "k" or e.name == "up" or e.name == "space":
            if e.event_type == keyboard.KEY_UP:
                if self.can_rotate():
                    self.hide_active_piece()
                    self.active_piece.change_rotation()
                    self.show_active_piece()
                    self.render_board()

        if e.name == "j" or e.name == "down":
            if e.event_type == keyboard.KEY_DOWN:
                if self.game_speed != ACC_SPEED:
                    self.game_speed = ACC_SPEED
            elif e.event_type == keyboard.KEY_UP:
                self.game_speed = SPEED

    def render_gameover(self) -> None:
        keyboard.unhook(self.keyboard_hook)
        ascii.clear_terminal()
        print(f'''
GAMEOVER  
Your points: {self.points}

press 'q' to quit program...
              ''')

    def run(self) -> None:
        self.keyboard_hook = keyboard.hook(self.keyboard)
        self.main_thread.start()
        keyboard.wait('q')

    def render_board(self) -> None:
        ascii.clear_terminal()
        board = ""
        for current_row in range(self.buffor_y_size, len(self.board)):
            row = ascii.BORDER 
            for current_value in range(len(self.board[current_row])):
                if self.board[current_row][current_value] == 1:
                    row += ascii.ONE_BLOCK
                else:
                    row += " " * len(ascii.ONE_BLOCK)

            row += f"{ascii.BORDER} \n"
            board += row

        board += f"└{self.board_max_x * len(ascii.ONE_BLOCK) * '─'}┘ Points: {self.points} \n"
        # b_r: {self.active_piece.get_bottom_right()} t_l: {self.active_piece.x, self.active_piece.y} | {self.active_piece.layout} 
        print(board)

    def spawn_piece(self) -> None:
        self.active_piece = Piece() 
        self.temp_board = deepcopy(self.board)
        self.active_piece.x = BOARD_X_SIZE // 2 - len(self.active_piece.layout[0]) // 2

    def hide_active_piece(self) -> None:
        with self.lock: # prevent exec from keyboard and gameloop at the same time
            for y in range(len(self.active_piece.layout)):
                for x in range(len(self.active_piece.layout[y])):
                    if self.active_piece.layout[y][x] != 0:
                        if self.temp_board[self.active_piece.y + y][self.active_piece.x + x] == 0:
                            self.board[self.active_piece.y + y][self.active_piece.x + x] = 0

    def show_active_piece(self) -> None:
        with self.lock:
            for y in range(len(self.active_piece.layout)):
                for x in range(len(self.active_piece.layout[y])):
                    if self.active_piece.layout[y][x] != 0:
                        self.board[self.active_piece.y + y][self.active_piece.x + x] = 1

    def is_gameover(self) -> bool:
        for _, value in enumerate(self.temp_board[self.buffor_y_size]):
            if value == 1:
               return True 
        return False

    def is_floor_collision(self) -> bool:
        _, y = self.active_piece.get_bottom_right()
        if y >= len(self.board) - 1:
            return True
        return False

    def can_move_right(self) -> bool:
        x, y = self.active_piece.get_bottom_right()
        if x >= len(self.temp_board[y]) - 1:
            return False 

        for y in range(len(self.active_piece.layout)):
            for x in range(len(self.active_piece.layout[y])):
                if self.active_piece.layout[y][x] != 0:
                    if self.temp_board[self.active_piece.y + y][self.active_piece.x + x + 1] == 1:
                        return False
        return True

    def can_move_left(self) -> bool:
        if self.active_piece.x == 0:
            return False 
        for y in range(len(self.active_piece.layout)):
            for x in range(len(self.active_piece.layout[y])):
                if self.active_piece.layout[y][x] != 0:
                    if self.temp_board[self.active_piece.y + y][self.active_piece.x + x - 1] == 1:
                        return False
        return True

    def can_rotate(self) -> bool:
        next_layout = self.active_piece.get_new_rotation_layout()

        # right border check
        if len(next_layout[0]) > len(self.active_piece.layout[0]):
            if self.active_piece.x + len(next_layout[0]) - 1 > len(self.temp_board[0]) - 1:
                return False

        # bottom check
        if len(next_layout) > len(self.active_piece.layout):
            if self.active_piece.y + len(next_layout) - 1 > len(self.temp_board) - 1:
                return False

        # check new position of rotated block
        for y in range(len(next_layout)):
            for x in range(len(next_layout[y])):
                if next_layout[y][x] != 0:
                    if self.temp_board[self.active_piece.y + y][self.active_piece.x + x] == 1:
                        return False

        return True

    def is_block_collision(self) -> bool:
        for y in range(len(self.active_piece.layout)):
            for x in range(len(self.active_piece.layout[y])):
                if self.active_piece.layout[y][x] != 0:
                    if self.temp_board[self.active_piece.y + y + 1][self.active_piece.x + x] == 1:
                        return True
        return False

    def check_rows(self) -> None:
        '''Operate on self.board, removing full rows and pulling down the upper ones'''
        removed = 0
        for y in range(len(self.board)):
            if all(x == 1 for x in self.board[y]):
                removed += 1
                self.board[y] = [0] * len(self.board[y]) # remove completed row
                for row in range(y - 1, BOARD_BUFFOR_SIZE - 1, -1): # from row upper to the top
                    row_copy = self.board[row].copy()
                    self.board[row] = [0] * len(self.board[row])
                    self.board[row + 1] = row_copy

        if removed > 0:
            self.points += (self.points_per_line * (self.level + 1)) * removed

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
