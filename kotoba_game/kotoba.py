# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 12:36:23 2024

@author: sakuramau
"""

import pygame
import random
import json
import sys
import webbrowser

# Initialize pygame
pygame.init()

# Game settings
WIDTH, HEIGHT = 900, 615
GRID_SIZE = 10  # 10x10
TILE_SIZE = 50
BOARD_OFFSET_Y = 60
BOARD_OFFSET_X = 325

CHAR_HEIGHT = 30
SCROLL_SPEED = 300

# Load Japanese font

FONT = pygame.font.Font("NotoSansJP-Black.ttf", 36)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)
BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
NAVY = (0, 0, 128)

# Set up the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Japanese Word Game")

# Load word list
with open("japanese_words.json", "r", encoding="utf-8") as f:
    word_list = json.load(f)

# Complete list of Hiragana characters
hiragana_list = [
    "あ", "い", "う", "え", "お",
    "か", "き", "く", "け", "こ",
    "さ", "し", "す", "せ", "そ",
    "た", "ち", "つ", "て", "と",
    "な", "に", "ぬ", "ね", "の",
    "は", "ひ", "ふ", "へ", "ほ",
    "ま", "み", "む", "め", "も",

    "ら", "り", "る", "れ", "ろ",

    "が", "ぎ", "ぐ", "げ", "ご",
    "ざ", "じ", "ず", "ぜ", "ぞ",
    "だ", "ぢ", "づ", "で", "ど",
    "ば", "び", "ぶ", "べ", "ぼ",
    "ぱ", "ぴ", "ぷ", "ぺ", "ぽ",
    "や", "ゆ", "よ",
    "わ", "を", "ん",
    "ゃ", "ゅ", "ょ", "っ",
    "ー"
]

# Initialize variables for dragging tiles
dragged_tile = None
dragged_tile_pos = (0, 0)
scroll_offset = 0  # Offset for scrolling in the sidebar
score = 0  # Initial score
score_history = [0]  # Start with the initial score of 0
selected_index = 0  # Default starting index for the sidebar character selection
sidebar_dragging = False
sidebar_drag_start_y = 0
used_tiles = set()  # Keep track of used tiles
initial_tile_positions = []


def generate_board():
    global initial_tile_positions  # Keeps track of pre-placed tiles
    board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    initial_tile_positions = []  # List to store initial tile positions

    # Place random tiles at the start of the game
    INITIAL_TILES_COUNT = 15  # Adjust the number as needed
    for _ in range(INITIAL_TILES_COUNT):
        row = random.randint(0, GRID_SIZE - 1)
        col = random.randint(0, GRID_SIZE - 1)
        while board[row][col] is not None:  # Ensure no duplicate placement
            row = random.randint(0, GRID_SIZE - 1)
            col = random.randint(0, GRID_SIZE - 1)
        board[row][col] = random.choice(hiragana_list)
        initial_tile_positions.append((row, col))  # Track the position of pre-placed tiles

    # Place unusable tiles
    num_unusable_tiles = 10  # Adjust the number of unusable tiles as needed
    for _ in range(num_unusable_tiles):
        while True:
            row = random.randint(0, GRID_SIZE - 1)
            col = random.randint(0, GRID_SIZE - 1)
            if board[row][col] is None:  # Only place on empty cells
                board[row][col] = "#"  # Use "#" to mark unusable tiles
                break

    # Initialize detected words from the starting configuration
    initialize_detected_words(board)

    return board

SIDEBAR_COLUMNS = 5
SIDEBAR_WIDTH = SIDEBAR_COLUMNS * TILE_SIZE


def draw_sidebar():
    global scroll_offset, selected_index
    y_offset = scroll_offset

    for i, char in enumerate(hiragana_list):
        row = i // SIDEBAR_COLUMNS
        col = i % SIDEBAR_COLUMNS

        char_x = col * TILE_SIZE
        char_y = row * TILE_SIZE + y_offset

        char_surface = FONT.render(char, True, TEXT_COLOR)  # Default color
        char_rect = pygame.Rect(char_x, char_y, TILE_SIZE, TILE_SIZE)

        # Check if the tile is used, and if it is, set its background and text color
        if char in used_tiles:
            char_surface = FONT.render(char, True, (100, 100, 100))  # Gray text for used tiles
            background_color = (200, 200, 200)  # Light gray background
        else:
            # Apply color based on index
            if i % 3 == 0:
                background_color = GREEN
            elif i % 3 == 1:
                background_color = YELLOW
            else:
                background_color = BLUE

        # Draw the background and border
        pygame.draw.rect(screen, background_color, char_rect)
        pygame.draw.rect(screen, BLACK, char_rect, 2)  # Border

        # Render the character on all tiles (including used ones)
        screen.blit(char_surface, (
            char_rect.x + (TILE_SIZE - char_surface.get_width()) // 2,
            char_rect.y + (TILE_SIZE - char_surface.get_height()) // 2
        ))


def handle_sidebar_click(mouse_x, mouse_y):
    global dragged_tile, dragged_tile_pos, selected_index, sidebar_dragging, sidebar_drag_start_y, used_tiles

    # Adjust the mouse position to account for scroll offset
    adjusted_y = mouse_y - scroll_offset
    row = adjusted_y // TILE_SIZE
    col = mouse_x // TILE_SIZE

    # Calculate the flat index from row and column
    index = row * SIDEBAR_COLUMNS + col

    if index < len(hiragana_list):
        dragged_tile = hiragana_list[index]
        if dragged_tile not in used_tiles:  # Only allow unused tiles
            dragged_tile_pos = (mouse_x, mouse_y)
            sidebar_dragging = True
            sidebar_drag_start_y = mouse_y
        else:
            # If the tile is in used_tiles, reset drag variables to prevent dragging
            dragged_tile = None
            sidebar_dragging = False


# Function to handle dragging and placing tiles
def handle_tile_drag(pos):
    global dragged_tile, dragged_tile_pos, sidebar_dragging
    col, row = pos
    if dragged_tile:
        dragged_tile_pos = (col, row)


def draw_board(board):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(col * TILE_SIZE + BOARD_OFFSET_X, BOARD_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, WHITE, rect)  # Grid cells in white
            pygame.draw.rect(screen, GRID_COLOR, rect, 2)

            if board[row][col]:
                char = board[row][col]

                if char == "#":  # Unusable tile
                    pygame.draw.rect(screen, (50, 50, 50), rect)  # Dark gray for unusable tiles
                else:
                    # If the tile is pre-placed (randomly generated initially), use orange
                    if (row, col) in initial_tile_positions:  # This will ensure only pre-placed tiles are orange
                        background_color = ORANGE
                    else:
                        # Retain the original color (green, yellow, or blue) based on hiragana list index
                        tile_index = hiragana_list.index(char)
                        if tile_index % 3 == 0:
                            background_color = GREEN
                        elif tile_index % 3 == 1:
                            background_color = YELLOW
                        else:
                            background_color = BLUE

                    # Draw the tile with the corresponding background color
                    text = FONT.render(char, True, TEXT_COLOR)
                    text_rect = text.get_rect(center=rect.center)
                    pygame.draw.rect(screen, background_color, rect)  # Background color for pre-placed tiles
                    pygame.draw.rect(screen, GRID_COLOR, rect, 2)  # Border
                    screen.blit(text, text_rect)


# Function to draw the dragged tile while dragging
def draw_dragged_tile():
    if dragged_tile:
        # Determine the color for the dragged tile based on the index in the hiragana_list
        tile_index = hiragana_list.index(dragged_tile)

        # Assign colors based on index (green, yellow, or blue)
        if tile_index % 3 == 0:
            background_color = GREEN
        elif tile_index % 3 == 1:
            background_color = YELLOW
        else:
            background_color = BLUE

        # Draw the dragged tile at the current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        tile_surface = FONT.render(dragged_tile, True, TEXT_COLOR)

        # Create background rectangle and follow mouse
        tile_rect = pygame.Rect(mouse_x - TILE_SIZE // 2, mouse_y - TILE_SIZE // 2, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, background_color, tile_rect)  # Keep the dragged tile's original color
        pygame.draw.rect(screen, GRID_COLOR, tile_rect, 2)  # Border
        screen.blit(tile_surface, (tile_rect.x + (TILE_SIZE - tile_surface.get_width()) // 2,
                                   tile_rect.y + (TILE_SIZE - tile_surface.get_height()) // 2))


# Global set to store already detected words
detected_words = set()


def initialize_detected_words(board):
    global detected_words
    detected_words = set()

    def extract_word(start, end, fixed, is_row):
        if is_row:
            return [board[fixed][c] for c in range(start, end + 1) if board[fixed][c] is not None]
        else:
            return [board[r][fixed] for r in range(start, end + 1) if board[r][fixed] is not None]

    def generate_substrings(word):
        substrings = []
        # Filter out None values from the word
        word = [tile for tile in word if tile is not None]

        for i in range(len(word)):
            for j in range(i + 2, len(word) + 1):  # Substrings of length ≥ 2
                substrings.append("".join(word[i:j]))
        return substrings

    # Scan horizontally
    for row in range(GRID_SIZE):
        start = None
        for col in range(GRID_SIZE):
            if board[row][col] in hiragana_list:
                if start is None:
                    start = col
            else:
                if start is not None:
                    if col - start >= 2:  # Word of length ≥ 2
                        word = extract_word(start, col - 1, row, is_row=True)
                        detected_words.update(generate_substrings(word))
                    start = None
        # Handle end of row
        if start is not None and GRID_SIZE - start >= 2:
            word = extract_word(start, GRID_SIZE - 1, row, is_row=True)
            detected_words.update(generate_substrings(word))

    # Scan vertically
    for col in range(GRID_SIZE):
        start = None
        for row in range(GRID_SIZE):
            if board[row][col] in hiragana_list:
                if start is None:
                    start = row
            else:
                if start is not None:
                    if row - start >= 2:  # Word of length ≥ 2
                        word = extract_word(start, row - 1, col, is_row=False)
                        detected_words.update(generate_substrings(word))
                    start = None
        # Handle end of column
        if start is not None and GRID_SIZE - start >= 2:
            word = extract_word(start, GRID_SIZE - 1, col, is_row=False)
            detected_words.update(generate_substrings(word))


def collect_new_words(row, col, board):
    current_words = set()  # Track words formed in this move only

    # Helper function to extract a contiguous sequence of tiles
    def extract_word(start, end, fixed, is_row):
        if is_row:
            return [board[fixed][c] for c in range(start, end + 1) if board[fixed][c] is not None]
        else:
            return [board[r][fixed] for r in range(start, end + 1) if board[r][fixed] is not None]

    # Helper function to generate all substrings of length ≥ 2
    def generate_substrings(word):
        substrings = []
        word = [tile for tile in word if tile is not None]  # Filter out None values
        for i in range(len(word)):
            for j in range(i + 2, len(word) + 1):  # Substrings of length ≥ 2
                substrings.append("".join(word[i:j]))
        return substrings

    # Horizontal word detection
    start_col = col
    end_col = col

    # Move left to find the start of the horizontal word
    while start_col > 0 and board[row][start_col - 1] in hiragana_list:
        start_col -= 1
    # Move right to find the end of the horizontal word
    while end_col < GRID_SIZE - 1 and board[row][end_col + 1] in hiragana_list:
        end_col += 1

    # Process horizontal word
    if end_col - start_col + 1 >= 2:
        horizontal_word = extract_word(start_col, end_col, row, is_row=True)
        current_words.update(generate_substrings(horizontal_word))

    # Vertical word detection
    start_row = row
    end_row = row

    # Move up to find the start of the vertical word
    while start_row > 0 and board[start_row - 1][col] in hiragana_list:
        start_row -= 1
    # Move down to find the end of the vertical word
    while end_row < GRID_SIZE - 1 and board[end_row + 1][col] in hiragana_list:
        end_row += 1

    # Process vertical word
    if end_row - start_row + 1 >= 2:
        vertical_word = extract_word(start_row, end_row, col, is_row=False)
        current_words.update(generate_substrings(vertical_word))

    # Only return words that weren't previously detected
    new_words = [word for word in current_words if word not in detected_words]

    return new_words


# Function to check if the square is adjacent to a letter (other placed tile with letters)
def is_valid(row, col, board):
    # Define the directions to check for adjacent tiles (left, right, up, down)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Iterate over the directions to check the adjacent tiles
    for dr, dc in directions:
        adj_row, adj_col = row + dr, col + dc

        # Check if the adjacent tile is within the grid bounds
        if 0 <= adj_row < GRID_SIZE and 0 <= adj_col < GRID_SIZE:
            # Check if the adjacent tile is a letter
            if board[adj_row][adj_col] in hiragana_list:
                return True  # Add the adjacent tile's character to form a word

    return False  # No adjacent letter found


def update_score(new_words):
    global score, score_history, word_list, used_words

    for word in new_words:
        if word in word_list and word not in used_words:  # Ensure the word is not already scored in this move
            if len(word) > 2:  # Only count words longer than 2 characters
                score += 1  # Increment the score
            used_words.append(word)  # Add to the list of user words
    # Push the updated score onto the history stack
    score_history.append(score)


def draw_score():
    score_surface = FONT.render(f"Score: {score}", True, WHITE)
    # Center horizontally and offset vertically by 10 pixels
    score_rect = score_surface.get_rect(center=(WIDTH // 2, 30))
    screen.blit(score_surface, score_rect)


def draw_button(x, y, width, height, text, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
    button_font = pygame.font.Font(None, 24)
    button_text = button_font.render(text, True, text_color)
    screen.blit(button_text, (x + (width - button_text.get_width()) // 2, y + (height - button_text.get_height()) // 2))
    return pygame.Rect(x, y, width, height)


def draw_undo():
    undo_button = pygame.Rect(525, HEIGHT - 50, 100, 37)
    pygame.draw.rect(screen, (200, 200, 200), undo_button)
    undo_text = FONT.render("Undo", True, BLACK)
    screen.blit(undo_text, (525, HEIGHT - 60))
    return undo_button


used_words = []  # Words created by the user


def display_word_list():
    global scroll_offset
    running = True
    global used_words
    used_words = list(set(used_words))

    while running:
        screen.fill(NAVY)
        y_offset = 50 - scroll_offset
        word_rects = []  # To store the clickable areas for each word

        # Get the current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Render each word and check if the mouse hovers over it
        for word in used_words:
            word_surface = FONT.render(word, True, WHITE)
            word_rect = word_surface.get_rect(topleft=(50, y_offset))
            word_rects.append((word_rect, word))  # Store the rect and word

            # If hovered, render the letter with a white border
            if word_rect.collidepoint(mouse_x, mouse_y):
                # Simulate an outline by rendering the text multiple times in white
                for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:  # Diagonal offsets
                    outline_surface = FONT.render(word, True, RED)
                    screen.blit(outline_surface, (word_rect.x + dx, word_rect.y + dy))
                # Render the main text on top
                screen.blit(word_surface, word_rect.topleft)
            else:
                # Regular rendering without outline
                screen.blit(word_surface, word_rect.topleft)

            y_offset += 40

        # Draw buttons for closing or starting a new game
        close_button = draw_button(WIDTH // 2 - 50, HEIGHT - 70, 100, 40, "Close", RED, WHITE)
        new_game_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 120, 150, 50, "New Game", GREEN, WHITE)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos

                # Check if any word was clicked
                for word_rect, word in word_rects:
                    if word_rect.collidepoint(mouse_x, mouse_y):
                        # Open Jisho.org search for the clicked word
                        jisho_url = f"https://jisho.org/search/{word}"
                        webbrowser.open(jisho_url)

                # Check if buttons were clicked
                if close_button.collidepoint(event.pos):
                    running = False
                    game_loop()
                elif new_game_button.collidepoint(event.pos):
                    running = False
                    new_game()

            # Scroll with arrow keys
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    scroll_offset += SCROLL_SPEED
                elif event.key == pygame.K_UP:
                    scroll_offset = max(0, scroll_offset - SCROLL_SPEED)

        pygame.display.flip()


placed_tiles = []  # Stack to track placed tiles


def return_tile_to_sidebar(tile):
    if tile in used_tiles:
        used_tiles.remove(tile)  # Mark the tile as unused


def undo_last_placement(board):
    global score, placed_tiles, score_history, detected_words

    if placed_tiles:
        # Undo the last placement
        row, col, tile = placed_tiles.pop()
        board[row][col] = None  # Clear the board cell
        return_tile_to_sidebar(tile)  # Return the tile to the sidebar

        # Reset detected words and reinitialize from current board state
        detected_words.clear()
        initialize_detected_words(board)

        # Revert score to the previous value in score_history
        if len(score_history) > 1:  # Ensure there's a previous score to revert to
            score_history.pop()  # Remove the current score
            score = score_history[-1]  # Set score to the previous value


def new_game():
    global score, score_history, detected_words, used_tiles, scroll_offset, dragged_tile, dragged_tile_pos, placed_tiles
    placed_tiles=[]
    score = 0
    score_history = [0]
    detected_words = set()
    used_tiles = set()
    scroll_offset = 0
    dragged_tile = None
    dragged_tile_pos = (0, 0)
    global used_words
    used_words = []
    game_loop()


def end_game():
    global running
    screen.fill(BLACK)
    final_score_text = FONT.render("Game complete!", True, WHITE)
    screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 50))

    word_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 50, 150, 50, "Show Words", ORANGE, WHITE)
    close_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 120, 150, 50, "Quit", RED, WHITE)
    new_game_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 190, 150, 50, "New Game", GREEN, WHITE)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if word_button.collidepoint(event.pos):
                    display_word_list()
                elif close_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif new_game_button.collidepoint(event.pos):
                    running = False
                    new_game()

        pygame.display.flip()


def game_loop():
    global dragged_tile, dragged_tile_pos, sidebar_dragging, sidebar_drag_start_y, scroll_offset, selected_index, placed_tiles, score
    min_scroll_offset = 0
    num_rows = (len(hiragana_list) + SIDEBAR_COLUMNS - 1) // SIDEBAR_COLUMNS
    max_scroll_offset = -(num_rows * TILE_SIZE - HEIGHT)

    # Initialize the board
    board = generate_board()
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill(BLACK)

        # Draw components
        draw_sidebar()
        draw_board(board)
        draw_score()

        if dragged_tile:
            draw_dragged_tile()

        # Draw Undo
        undo_button = draw_undo()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button click
                    mouse_x, mouse_y = event.pos

                    # Check if we clicked on the Undo
                    if undo_button.collidepoint(event.pos):
                        undo_last_placement(board)


                    # Check if we clicked on a tile in the sidebar
                    elif mouse_x < SIDEBAR_WIDTH:
                        handle_sidebar_click(mouse_x, mouse_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button release
                    if dragged_tile:
                        mouse_x, mouse_y = event.pos
                        col = (mouse_x - BOARD_OFFSET_X) // TILE_SIZE
                        row = (mouse_y - BOARD_OFFSET_Y) // TILE_SIZE
                        # Check if the tile is placed within the grid bounds
                        if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
                            if board[row][col] is None:
                                board[row][col] = dragged_tile
                                new_words = collect_new_words(row, col, board)

                                # Check if placement creates at least one new valid word
                                valid_placement = any(word in word_list for word in new_words)

                                if valid_placement:
                                    used_tiles.add(dragged_tile)
                                    detected_words.update(new_words)  # Add new words to detected set
                                    update_score(new_words)
                                    placed_tiles.append((row, col, dragged_tile))
                                else:
                                    board[row][col] = None  # Invalid placement, revert
                        # Reset dragged tile
                        dragged_tile = None

            elif event.type == pygame.MOUSEMOTION:
                if dragged_tile:
                    handle_tile_drag(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:  # Move sidebar down
                    scroll_offset = max(scroll_offset - SCROLL_SPEED, max_scroll_offset)
                elif event.key == pygame.K_UP:  # Move sidebar up
                    scroll_offset = min(scroll_offset + SCROLL_SPEED, min_scroll_offset)
                elif event.key == pygame.K_ESCAPE:
                    running = False  # Exit game when Escape is pressed
                elif event.key == pygame.K_z:
                    undo_last_placement(board)

        if score >= 20:
            end_game()

            # Update display
        pygame.display.flip()
        clock.tick(120)

    pygame.quit()


if __name__ == "__main__":
    game_loop()
