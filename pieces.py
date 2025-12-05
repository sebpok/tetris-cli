from assets import ascii
from random import randint

class Piece:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.layout = []
        self.rotation_index = 0
        self.type_index = 0

        self.pieces = ascii.pieces_list()

        self.draw_piece()

    def update_layout(self) -> None:
        self.layout = self.pieces[self.type_index][self.rotation_index]

    def draw_piece(self) -> None:
        self.type_index = randint(0, len(self.pieces) - 1)
        self.rotation_index = 0
        self.update_layout()

    def change_rotation(self) -> None:
        if self.rotation_index == len(self.pieces[self.type_index]) - 1:
            self.rotation_index = 0
        else:
            self.rotation_index += 1
        self.update_layout()

    def get_new_rotation_layout(self) -> list:
        layout = []
        if self.rotation_index == len(self.pieces[self.type_index]) - 1:
            layout = self.pieces[self.type_index][0]
        else:
            layout = self.pieces[self.type_index][self.rotation_index + 1]
        return layout

    def add_rotation(self) -> None:
        self.rotation_index += 1
        self.update_layout()

    def subtract_rotation(self) -> None:
        self.rotation_index -= 1
        self.update_layout()

    def move_down(self) -> None:
        self.y += 1

    def move_right(self) -> None:
        self.x += 1

    def move_left(self) -> None:
        self.x -= 1

    def get_bottom_right(self) -> tuple[int, int]:
        x = self.x + len(self.layout[0]) - 1
        y = self.y + len(self.layout) - 1
        return x, y

