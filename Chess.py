import tkinter as tk  # GUI library
import string         # For string operations (like ascii_lowercase)
import os             # For file and directory operations
from PIL import Image, ImageTk  # For image handling (Pillow library)
import random         # For random AI moves

# -------------------------------
# Chess Board Class
# -------------------------------
class Board(tk.Frame):
    def __init__(self, parent, length, width, move_listbox):
        super().__init__(parent)
        # Store references and state
        self.parent = parent
        self.length = length
        self.width = width
        self.move_listbox = move_listbox  # Listbox widget for move history

        # Board and piece state
        self.squares = {}            # Dictionary: square name -> Button widget
        self.white_images = {}       # Dictionary: filename -> PhotoImage (white)
        self.black_images = {}       # Dictionary: filename -> PhotoImage (black)
        self.white_piece_refs = {}   # Dictionary: piece letter -> PhotoImage (white)
        self.black_piece_refs = {}   # Dictionary: piece letter -> PhotoImage (black)
        self.white_pieces = []       # List of all white piece images
        self.black_pieces = []       # List of all black piece images
        self.blank_image = None      # Reference to blank square image
        self.ranks = "abcdefgh"      # File letters for board
        self.buttons_pressed = 0     # 0 = no selection, 1 = piece selected
        self.turns = 0               # Even = white's turn, odd = black's turn

        # Castling and move state
        self.wk_moved = self.bk_moved = False
        self.wr1_moved = self.wr2_moved = False
        self.br1_moved = self.br2_moved = False
        self.castled = False
        self.move_history = []       # List of moves for history
        self.highlighted_squares = []# List of currently highlighted squares
        self.piece_color = None      # "white" or "black" for current selection

        # Setup board and pieces
        self.set_squares()           # Create the board squares/buttons
        self.import_pieces()         # Load piece images
        self.setup_piece_refs()      # Setup references for piece images
        self.set_pieces()            # Place pieces on the board
        self.pack()                  # Pack the frame into the parent window

    # -------------------------------
    # Setup piece image references
    # -------------------------------
    def setup_piece_refs(self):
        # Map piece letters to their images for white and black
        self.white_piece_refs = {
            "k": self.white_images["k.png"],
            "q": self.white_images["q.png"],
            "r": self.white_images["r.png"],
            "b": self.white_images["b.png"],
            "n": self.white_images["n.png"],
            "p": self.white_images["p.png"]
        }
        self.black_piece_refs = {
            "k": self.black_images["k.png"],
            "q": self.black_images["q.png"],
            "r": self.black_images["r.png"],
            "b": self.black_images["b.png"],
            "n": self.black_images["n.png"],
            "p": self.black_images["p.png"]
        }
        # Store all piece images for easy color checking
        self.white_pieces = list(self.white_piece_refs.values())
        self.black_pieces = list(self.black_piece_refs.values())
        self.blank_image = self.white_images["blank.png"]

    # -------------------------------
    # Handle piece selection and moves
    # -------------------------------
    def select_piece(self, button):
        self.clear_highlights()  # Always clear highlights on any click

        # First click: select a piece
        if self.buttons_pressed == 0:
            # Only allow selecting your own piece on your turn
            if button.image in self.white_pieces and self.turns % 2 == 0:
                self.piece_color = "white"
            elif button.image in self.black_pieces and self.turns % 2 == 1:
                self.piece_color = "black"
            else:
                return  # Not your piece or not a piece

            # Store selection
            self.sq1 = list(self.squares.keys())[list(self.squares.values()).index(button)]
            self.sq1_button = button
            self.buttons_pressed = 1

            # Highlight legal moves for this piece
            self.highlight_legal_moves()

            # Show possible moves in window title (for debugging/UX)
            possible_moves = []
            for sq in self.squares:
                self.sq2 = sq
                self.sq2_button = self.squares[sq]
                if self.allowed_piece_move() and not self.friendly_fire():
                    possible_moves.append(sq)
            self.parent.title(f"Possible moves: {', '.join(possible_moves)}")

        # Second click: attempt to move to target square
        elif self.buttons_pressed == 1:
            self.sq2 = list(self.squares.keys())[list(self.squares.values()).index(button)]
            self.sq2_button = button

            # If clicked same square, cancel selection
            if self.sq2 == self.sq1:
                self.buttons_pressed = 0
                self.parent.title("Chess")
                return

            # If move is legal and not capturing own piece
            if self.allowed_piece_move() and not self.friendly_fire():
                # Save previous state for undo if needed
                prev_sq1 = self.sq1
                prev_sq1_button_piece = self.sq1_button.image
                prev_sq2 = self.sq2
                prev_sq2_button_piece = self.sq2_button.image

                # Move the piece
                self.squares[self.sq2].config(image=self.sq1_button.image)
                self.squares[self.sq2].image = self.sq1_button.image
                self.squares[self.sq1].config(image=self.blank_image)
                self.squares[self.sq1].image = self.blank_image

                # Check if move puts own king in check (illegal)
                if self.in_check() and not self.castled:
                    # Undo move
                    self.squares[prev_sq2].config(image=prev_sq2_button_piece)
                    self.squares[prev_sq2].image = prev_sq2_button_piece
                    self.squares[prev_sq1].config(image=prev_sq1_button_piece)
                    self.squares[prev_sq1].image = prev_sq1_button_piece
                    self.buttons_pressed = 0
                    self.parent.title("Chess")
                    return
                else:
                    # Update castling rights if king or rook moved
                    if prev_sq1_button_piece == self.white_piece_refs["k"]:
                        self.wk_moved = True
                    if prev_sq1_button_piece == self.black_piece_refs["k"]:
                        self.bk_moved = True
                    if prev_sq1_button_piece == self.white_piece_refs["r"] and prev_sq1 == "a1":
                        self.wr1_moved = True
                    if prev_sq1_button_piece == self.white_piece_refs["r"] and prev_sq1 == "h1":
                        self.wr2_moved = True
                    if prev_sq1_button_piece == self.black_piece_refs["r"] and prev_sq1 == "a8":
                        self.br1_moved = True
                    if prev_sq1_button_piece == self.black_piece_refs["r"] and prev_sq1 == "h8":
                        self.br2_moved = True

                    # Move complete: update state
                    self.buttons_pressed = 0
                    self.turns += 1
                    piece_name = self.get_piece_name(prev_sq1_button_piece)
                    move_str = f"{piece_name}: {prev_sq1} → {prev_sq2}"
                    self.move_history.append((prev_sq1, prev_sq2, piece_name))
                    self.move_listbox.insert(tk.END, move_str)

                    # Handle pawn promotion
                    if (self.sq2_button.image == self.white_piece_refs["p"] and prev_sq2.endswith("8")) or \
                       (self.sq2_button.image == self.black_piece_refs["p"] and prev_sq2.endswith("1")):
                        self.promotion_menu(self.piece_color)

            # Reset highlights and state
            self.castled = False
            self.highlighted_squares = []
            self.parent.title("Chess")
            self.piece_color = None

        # Fallback: reset selection state
        else:
            self.buttons_pressed = 0
            self.parent.title("Chess")
            return

    # -------------------------------
    # Get piece name for move history
    # -------------------------------
    def get_piece_name(self, img):
        for name, ref in self.white_piece_refs.items():
            if img == ref:
                return "White " + name.upper()
        for name, ref in self.black_piece_refs.items():
            if img == ref:
                return "Black " + name.upper()
        return "Unknown"

    # -------------------------------
    # Pawn promotion menu
    # -------------------------------
    def promotion_menu(self, color):
        def return_piece(piece_img):
            self.squares[self.sq2].config(image=piece_img)
            self.squares[self.sq2].image = piece_img
            promo.destroy()
        promo = tk.Toplevel(self)
        promo.title("Choose what to promote your pawn to")
        if color == "white":
            tk.Button(promo, text="Knight", command=lambda: return_piece(self.white_piece_refs["n"])).grid(row=0, column=0)
            tk.Button(promo, text="Bishop", command=lambda: return_piece(self.white_piece_refs["b"])).grid(row=0, column=1)
            tk.Button(promo, text="Rook", command=lambda: return_piece(self.white_piece_refs["r"])).grid(row=1, column=0)
            tk.Button(promo, text="Queen", command=lambda: return_piece(self.white_piece_refs["q"])).grid(row=1, column=1)
        elif color == "black":
            tk.Button(promo, text="Knight", command=lambda: return_piece(self.black_piece_refs["n"])).grid(row=0, column=0)
            tk.Button(promo, text="Bishop", command=lambda: return_piece(self.black_piece_refs["b"])).grid(row=0, column=1)
            tk.Button(promo, text="Rook", command=lambda: return_piece(self.black_piece_refs["r"])).grid(row=1, column=0)
            tk.Button(promo, text="Queen", command=lambda: return_piece(self.black_piece_refs["q"])).grid(row=1, column=1)

    # -------------------------------
    # Check if move would capture own piece
    # -------------------------------
    def friendly_fire(self):
        piece_2_color = self.sq2_button.image
        if self.piece_color == "white" and piece_2_color in self.white_pieces:
            return True
        if self.piece_color == "black" and piece_2_color in self.black_pieces:
            return True
        return False

    # -------------------------------
    # Check if path is clear for sliding pieces
    # -------------------------------
    def clear_path(self, piece):
        # Rook/Queen: check straight lines
        if piece == "rook" or piece == "queen":
            if self.sq1[0] == self.sq2[0]:  # Same file
                pos1 = min(int(self.sq1[1]), int(self.sq2[1]))
                pos2 = max(int(self.sq1[1]), int(self.sq2[1]))
                for i in range(pos1+1, pos2):
                    square_on_path = self.squares[self.sq1[0]+str(i)].image
                    if square_on_path != self.blank_image:
                        return False
            elif self.sq1[1] == self.sq2[1]:  # Same rank
                pos1 = min(self.ranks.find(self.sq1[0]), self.ranks.find(self.sq2[0]))
                pos2 = max(self.ranks.find(self.sq1[0]), self.ranks.find(self.sq2[0]))
                for i in range(pos1+1, pos2):
                    square_on_path = self.squares[self.ranks[i]+self.sq1[1]].image
                    if square_on_path != self.blank_image:
                        return False
        # Bishop/Queen: check diagonals
        if piece == "bishop" or piece == "queen":
            x1 = self.ranks.find(self.sq1[0])
            x2 = self.ranks.find(self.sq2[0])
            y1 = int(self.sq1[1])
            y2 = int(self.sq2[1])
            if y1 < y2:
                if x1 < x2:
                    for x in range(x1+1, x2):
                        y1 += 1
                        square_on_path = self.squares[self.ranks[x]+str(y1)].image
                        if square_on_path != self.blank_image:
                            return False
                elif x1 > x2:
                    for x in range(x1-1, x2, -1):
                        y1 += 1
                        square_on_path = self.squares[self.ranks[x]+str(y1)].image
                        if square_on_path != self.blank_image:
                            return False
            elif y1 > y2:
                if x1 < x2:
                    for x in range(x1+1, x2):
                        y1 -= 1
                        square_on_path = self.squares[self.ranks[x]+str(y1)].image
                        if square_on_path != self.blank_image:
                            return False
                if x1 > x2:
                    for x in range(x1-1, x2, -1):
                        y1 -= 1
                        square_on_path = self.squares[self.ranks[x]+str(y1)].image
                        if square_on_path != self.blank_image:
                            return False
        return True

    # -------------------------------
    # Highlight all legal moves for selected piece
    # -------------------------------
    def highlight_legal_moves(self):
        self.clear_highlights()
        self.sq1 = list(self.squares.keys())[list(self.squares.values()).index(self.sq1_button)]
        for sq in self.squares:
            self.sq2 = sq
            self.sq2_button = self.squares[sq]
            if self.allowed_piece_move() and not self.friendly_fire():
                self.squares[sq].config(bg="lime green")
                self.highlighted_squares.append(sq)

    # -------------------------------
    # Remove all highlights from board
    # -------------------------------
    def clear_highlights(self):
        for sq in self.highlighted_squares:
            x = 8 - int(sq[1])
            y = string.ascii_lowercase.index(sq[0])
            color = "tan4" if (x + y) % 2 == 0 else "burlywood1"
            self.squares[sq].config(bg=color)
        self.highlighted_squares.clear()

    # -------------------------------
    # Check if the selected move is legal for the piece
    # -------------------------------
    def allowed_piece_move(self):
        # Assign references for easier reading
        wb = self.white_piece_refs["b"]
        wk = self.white_piece_refs["k"]
        wn = self.white_piece_refs["n"]
        wp = self.white_piece_refs["p"]
        wq = self.white_piece_refs["q"]
        wr = self.white_piece_refs["r"]
        bb = self.black_piece_refs["b"]
        bk = self.black_piece_refs["k"]
        bn = self.black_piece_refs["n"]
        bp = self.black_piece_refs["p"]
        bq = self.black_piece_refs["q"]
        br = self.black_piece_refs["r"]
        blank = self.blank_image

        if self.sq1_button.image == blank:
            return False

        # Bishop
        if (self.sq1_button.image == wb or self.sq1_button.image == bb) and self.clear_path("bishop"):
            if abs(int(self.sq1[1]) - int(self.sq2[1])) == abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])):
                return True

        # Knight
        if self.sq1_button.image == wn or self.sq1_button.image == bn:
            if (abs(int(self.sq1[1]) - int(self.sq2[1])) == 2 and abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 1) or \
               (abs(int(self.sq1[1]) - int(self.sq2[1])) == 1 and abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 2):
                return True

        # King
        if self.sq1_button.image == wk or self.sq1_button.image == bk:
            if abs(int(self.sq1[1]) - int(self.sq2[1])) < 2 and abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) < 2:
                return True
            if self.castle():
                return True

        # White Pawn
        if self.sq1_button.image == wp:
            if self.sq1[1] == "2":
                if (int(self.sq2[1]) == 3 or int(self.sq2[1]) == 4) and self.sq1[0] == self.sq2[0] and self.sq2_button.image == blank:
                    if int(self.sq2[1]) == 4:
                        in_front = self.squares[self.sq1[0] + "3"]
                        if in_front.image == blank:
                            return True
                    else:
                        return True
            if int(self.sq2[1]) == int(self.sq1[1]) + 1 and self.sq1[0] == self.sq2[0] and self.sq2_button.image == blank:
                return True
            if int(self.sq2[1]) == int(self.sq1[1]) + 1 and abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 1 and self.sq2_button.image in self.black_pieces:
                return True

        # Black Pawn
        if self.sq1_button.image == bp:
            if self.sq1[1] == "7":
                if (int(self.sq2[1]) == 6 or int(self.sq2[1]) == 5) and self.sq1[0] == self.sq2[0] and self.sq2_button.image == blank:
                    if int(self.sq2[1]) == 5:
                        in_front = self.squares[self.sq1[0] + "6"]
                        if in_front.image == blank:
                            return True
                    else:
                        return True
            if int(self.sq2[1]) == int(self.sq1[1]) - 1 and self.sq1[0] == self.sq2[0] and self.sq2_button.image == blank:
                return True
            if int(self.sq2[1]) == int(self.sq1[1]) - 1 and abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])) == 1 and self.sq2_button.image in self.white_pieces:
                return True

        # Queen
        if (self.sq1_button.image == wq or self.sq1_button.image == bq) and self.clear_path("queen"):
            if int(self.sq1[1]) == int(self.sq2[1]) or self.sq1[0] == self.sq2[0]:
                return True
            if abs(int(self.sq1[1]) - int(self.sq2[1])) == abs(self.ranks.find(self.sq1[0]) - self.ranks.find(self.sq2[0])):
                return True

        # Rook
        if self.sq1_button.image == wr or self.sq1_button.image == br:
            if (int(self.sq1[1]) == int(self.sq2[1]) or self.sq1[0] == self.sq2[0]) and self.clear_path("rook"):
                return True

        return False

    # -------------------------------
    # Castling logic (not implemented)
    # -------------------------------
    def castle(self):
        return False

    # -------------------------------
    # Check if current player's king is in check
    # -------------------------------
    def in_check(self):
        previous_sq1 = self.sq1
        previous_sq1_button = self.sq1_button
        previous_sq2 = self.sq2
        previous_sq2_button = self.sq2_button

        def return_previous_values():
            self.sq1 = previous_sq1
            self.sq1_button = previous_sq1_button
            self.sq2 = previous_sq2
            self.sq2_button = previous_sq2_button

        # Check all enemy moves to see if they attack our king
        if self.piece_color == "white":
            king_img = self.white_piece_refs["k"]
            self.sq2 = self.find_king(king_img)
            for key in self.squares:
                self.sq1 = key
                self.sq1_button = self.squares[self.sq1]
                if self.sq1_button.image in self.black_pieces:
                    if self.allowed_piece_move():
                        return True
        if self.piece_color == "black":
            king_img = self.black_piece_refs["k"]
            self.sq2 = self.find_king(king_img)
            for key in self.squares:
                self.sq1 = key
                self.sq1_button = self.squares[self.sq1]
                if self.sq1_button.image in self.white_pieces:
                    if self.allowed_piece_move():
                        return True
        return_previous_values()
        return False

    # -------------------------------
    # Find the square containing the given king image
    # -------------------------------
    def find_king(self, king_img):
        for square in self.squares:
            button = self.squares[square]
            if button.image == king_img:
                return square

    # -------------------------------
    # Create the board squares as buttons
    # -------------------------------
    def set_squares(self):
        for x in range(8):
            for y in range(8):
                # Alternate colors for chessboard pattern
                if x % 2 == 0 and y % 2 == 0:
                    self.square_color = "tan4"
                elif x % 2 == 1 and y % 2 == 1:
                    self.square_color = "tan4"
                else:
                    self.square_color = "burlywood1"
                B = tk.Button(self, bg=self.square_color, activebackground="lawn green")
                B.grid(row=8-x, column=y)
                pos = self.ranks[y]+str(x+1)
                self.squares.setdefault(pos, B)
                self.squares[pos].config(command=lambda key=self.squares[pos]: self.select_piece(key))

    # -------------------------------
    # Load piece images from disk
    # -------------------------------
    def import_pieces(self):
        # Load white pieces
        path = os.path.join(os.path.dirname(__file__), "White")
        w_dirs = os.listdir(path)
        for file in w_dirs:
            img = Image.open(os.path.join(path, file))
            img = img.resize((80, 80), Image.LANCZOS)
            img = ImageTk.PhotoImage(image=img)
            self.white_images.setdefault(file, img)
        # Load black pieces
        path = os.path.join(os.path.dirname(__file__), "Black")
        b_dirs = os.listdir(path)
        for file in b_dirs:
            img = Image.open(os.path.join(path, file))
            img = img.resize((80, 80), Image.LANCZOS)
            img = ImageTk.PhotoImage(image=img)
            self.black_images.setdefault(file, img)

    # -------------------------------
    # Place pieces in starting positions
    # -------------------------------
    def set_pieces(self):
        # Dictionaries for starting positions
        dict_rank1_pieces = {"a1": "r.png", "b1": "n.png", "c1": "b.png", "d1": "q.png", "e1": "k.png", "f1": "b.png", "g1": "n.png", "h1": "r.png"}
        dict_rank2_pieces = {"a2": "p.png", "b2": "p.png", "c2": "p.png", "d2": "p.png", "e2": "p.png", "f2": "p.png", "g2": "p.png", "h2": "p.png"}
        dict_rank7_pieces = {"a7": "p.png", "b7": "p.png", "c7": "p.png", "d7": "p.png", "e7": "p.png", "f7": "p.png", "g7": "p.png", "h7": "p.png"}
        dict_rank8_pieces = {"a8": "r.png", "b8": "n.png", "c8": "b.png", "d8": "q.png", "e8": "k.png", "f8": "b.png", "g8": "n.png", "h8": "r.png"}
        # Place white pieces
        for key in dict_rank1_pieces:
            starting_piece = dict_rank1_pieces[key]
            self.squares[key].config(image=self.white_images[starting_piece])
            self.squares[key].image = self.white_images[starting_piece]
        for key in dict_rank2_pieces:
            starting_piece = dict_rank2_pieces[key]
            self.squares[key].config(image=self.white_images[starting_piece])
            self.squares[key].image = self.white_images[starting_piece]
        # Place black pieces
        for key in dict_rank7_pieces:
            starting_piece = dict_rank7_pieces[key]
            self.squares[key].config(image=self.black_images[starting_piece])
            self.squares[key].image = self.black_images[starting_piece]
        for key in dict_rank8_pieces:
            starting_piece = dict_rank8_pieces[key]
            self.squares[key].config(image=self.black_images[starting_piece])
            self.squares[key].image = self.black_images[starting_piece]
        # Place blank images for empty squares
        for rank in range(3, 7):
            for file in range(8):
                starting_piece = "blank.png"
                pos = self.ranks[file]+str(rank)
                self.squares[pos].config(image=self.white_images[starting_piece])
                self.squares[pos].image = self.white_images[starting_piece]

    # -------------------------------
    # Change board color theme
    # -------------------------------
    def change_theme(self, theme):
        light, dark = theme
        for x in range(8):
            for y in range(8):
                pos = self.ranks[y] + str(8 - x)
                color = dark if (x + y) % 2 == 0 else light
                self.squares[pos].config(bg=color, activebackground="lawn green")

    # -------------------------------
    # Make a random AI move for the current player
    # -------------------------------
    def random_ai_move(self):
        enemy_color = "black" if self.turns % 2 == 1 else "white"
        pieces = self.black_pieces if enemy_color == "black" else self.white_pieces
        movable = []
        for sq in self.squares:
            btn = self.squares[sq]
            if btn.image in pieces:
                self.sq1 = sq
                self.sq1_button = btn
                for target_sq in self.squares:
                    self.sq2 = target_sq
                    self.sq2_button = self.squares[target_sq]
                    if self.allowed_piece_move() and not self.friendly_fire():
                        movable.append((sq, target_sq))
        if movable:
            move = random.choice(movable)
            self.sq1, self.sq2 = move
            self.sq1_button = self.squares[self.sq1]
            self.sq2_button = self.squares[self.sq2]
            self.select_piece(self.sq2_button)

# -------------------------------
# Restart the game and reset state
# -------------------------------
def restart_game():
    for square in board.squares.values():
        square.config(image=board.white_images["blank.png"])
        square.image = board.white_images["blank.png"]
    board.set_pieces()
    board.buttons_pressed = 0
    board.turns = 0
    board.wk_moved = board.bk_moved = False
    board.wr1_moved = board.wr2_moved = False
    board.br1_moved = board.br2_moved = False
    board.castled = False
    board.move_listbox.delete(0, tk.END)
    board.move_history.clear()
    board.parent.title("Chess")

# -------------------------------
# Main GUI setup
# -------------------------------
root = tk.Tk()
root.geometry("950x800")  # Make room for move history

# Move history Listbox on the right
move_frame = tk.Frame(root)
move_frame.pack(side="right", fill="y")
tk.Label(move_frame, text="Move History", font=("Arial", 12)).pack()
move_listbox = tk.Listbox(move_frame, width=25, font=("Consolas", 12))
move_listbox.pack(fill="y", expand=True)

# Create the chess board
board = Board(root, 8, 8, move_listbox)

# Bind the "a" key to trigger the AI move
root.bind('a', lambda event: board.random_ai_move())

# Restart button
restart_btn = tk.Button(root, text="Restart", command=restart_game, font=("Arial", 16), bg="red", fg="white")
restart_btn.pack(pady=10)

# --- AI Move button ---
ai_btn = tk.Button(root, text="AI Move", command=board.random_ai_move, font=("Arial", 16), bg="blue", fg="white")
ai_btn.pack(pady=10)

# Theme change buttons
def theme_wood():
    board.change_theme(("burlywood1", "tan4"))

def theme_blue():
    board.change_theme(("light blue", "steel blue"))

def theme_green():
    board.change_theme(("pale green", "dark green"))

theme_frame = tk.Frame(root)
theme_frame.pack(pady=10)

tk.Label(theme_frame, text="Change Theme:", font=("Arial", 12)).pack(side="left")
tk.Button(theme_frame, text="Wood", command=theme_wood).pack(side="left")
tk.Button(theme_frame, text="Blue", command=theme_blue).pack(side="left")
tk.Button(theme_frame, text="Green", command=theme_green).pack(side="left")

# Start the Tkinter event loop
root.mainloop()
