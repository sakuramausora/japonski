import pygame
import random
import json
import sys
import requests
import webbrowser



pygame.init()
# Game settings
WIDTH, HEIGHT = 900, 660
GRID_SIZE = 10  # 10x10
TILE_SIZE = 50
BOARD_OFFSET_Y = 60
BOARD_OFFSET_X = 60
CHAR_HEIGHT = 30

FONT = pygame.font.Font("NotoSansJP-Black.ttf", 36)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100, 128)
RED = (255, 0, 0)
BRIGHT_YELLOW = (255, 255, 0)
# Initialize score as a global variable
score = 0
used_words = []
session = requests.Session()  # Persistent session
hovered_word_data_cache = {}  # Cache for storing word details

# Set up the screen
# Use double buffering for smoother rendering
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN])

pygame.display.set_caption("Japanese Word Game")

with open("kanjis.json", "r", encoding="utf-8") as f:
    kanji_dict = json.load(f)
    kanji_list = list(kanji_dict.keys())  # Get just the kanji characters as a list

# Load word list
with open("kanji_words.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract the list of words
aword_list = data.get("words", [])
# Filter words that contain only kanji characters
kword_list = []
for word in aword_list:
    if len(word)>1 and all(char in kanji_list for char in word):  # Check if all characters are in kanji_list
        kword_list.append(word)

def generate_board():
    board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    words_to_place = random.sample(kword_list, 20)

    placed_words = []

    for word in words_to_place:
        placed = False
        while not placed:
            horizontal = random.choice([True, False])
            if horizontal:
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - len(word))
                can_place = all(board[row][col + i] in (None, word[i]) for i in range(len(word)))
                if can_place:
                    for i, char in enumerate(word):
                        board[row][col + i] = char
                    placed = True
            else:
                row = random.randint(0, GRID_SIZE - len(word))
                col = random.randint(0, GRID_SIZE - 1)
                can_place = all(board[row + i][col] in (None, word[i]) for i in range(len(word)))
                if can_place:
                    for i, char in enumerate(word):
                        board[row + i][col] = char
                    placed = True

        if placed:
            placed_words.append(word)

    # Step 3: Fill remaining empty spaces with random kanji
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] is None:
                board[row][col] = random.choice(kanji_list)
    return board, placed_words

# Add new variables for tile selection
selected_tiles = []
active_word = ""

def draw_board(board):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(col * TILE_SIZE + BOARD_OFFSET_X,
                              BOARD_OFFSET_Y + row * TILE_SIZE,
                              TILE_SIZE, TILE_SIZE)

            pygame.draw.rect(screen, GREEN, rect)

            # Draw a gradient effect
            for i in range(10):
                pygame.draw.rect(screen, (0, 240, 150, 255 - i),
                                 (rect.x + i, rect.y + i, rect.width - 2 * i, rect.height - 2 * i))

            # Fill the rest of the rectangle with the main color
            pygame.draw.rect(screen, GREEN, (rect.x + 8, rect.y + 8, rect.width - 8, rect.height - 8))

            pygame.draw.rect(screen, GRID_COLOR, rect, 2)


            if board[row][col]:
                text = FONT.render(board[row][col], True, TEXT_COLOR)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
            if (row, col) in selected_tiles:
                    pygame.draw.rect(screen, RED, rect, 4)



def handle_tile_click(row, col, board):
    global selected_tiles, active_word, score, used_words

    # If there are already selected tiles, check if the clicked tile is a valid continuation
    if selected_tiles:
        last_row, last_col = selected_tiles[-1]
        # Ensure the clicked tile is adjacent and in the same row or column
        if not ((row == last_row and abs(col - last_col) == 1) or
                (col == last_col and abs(row - last_row) == 1)):
            # Clear selection if the clicked tile is not a valid continuation
            selected_tiles = []
            active_word = ""
            return

    # Add the clicked tile to the selection
    if board[row][col]:
        selected_tiles.append((row, col))
        active_word += board[row][col]

        # Check if the selected tiles form a valid word
        if active_word in kword_list and active_word not in used_words:
            used_words.append(active_word)
            flash([active_word], board)
            selected_tiles = []
            active_word = ""


def handle_tile_hover(row, col, board):
    if board[row][col] in kanji_dict:
        kanji = board[row][col]
        readings_kun = kanji_dict[kanji]["readings_kun"]
        readings_on = kanji_dict[kanji]["readings_on"]
        meanings = kanji_dict[kanji]["meanings"]

        # Create a surface to display the info
        block_width, block_height = 300, 200

        block_surface = pygame.Surface((block_width, block_height))
        block_surface.set_alpha(240)  # Set alpha value to make it semi-transparent

        # Draw a gradient effect to give the illusion of rounded corners
        for i in range(10):
            pygame.draw.rect(block_surface, (255, 255, 0, 255 - i * 25),
                             (i, i, block_width - 2 * i, block_height - 2 * i))

        # Fill the rest of the rectangle with the main color
        pygame.draw.rect(block_surface, YELLOW, (10, 10, block_width - 20, block_height - 20))
        # Set up font and starting positions
        block_font = pygame.font.Font('NotoSansJP-Black.ttf', 16)
        y_offset = 10  # Initial vertical offset for text

        # Render the text for Readings (Kun)
        kun_text = block_font.render("Readings (くん):", True, BLACK)
        block_surface.blit(kun_text, (10, y_offset))
        y_offset += 20
        kun_readings = ", ".join(readings_kun)  # Join readings with commas
        reading_text = block_font.render(kun_readings, True, BLACK)
        block_surface.blit(reading_text, (10, y_offset))
        y_offset += 30

        # Render the text for Readings (On)
        on_text = block_font.render("Readings (おん):", True, BLACK)
        block_surface.blit(on_text, (10, y_offset))
        y_offset += 20
        on_readings = ", ".join(readings_on)  # Join readings with commas
        reading_text = block_font.render(on_readings, True, BLACK)
        block_surface.blit(reading_text, (10, y_offset))
        y_offset += 30

        # Render the text for Meanings
        meanings_text = block_font.render("Meanings:", True, BLACK)
        block_surface.blit(meanings_text, (10, y_offset))
        y_offset += 20

        # Split meanings into multiple lines if necessary
        max_width = block_width - 20
        lines = []
        current_line = ""
        for meaning in meanings:
            if block_font.size(current_line + ", " + meaning)[0] > max_width:
                lines.append(current_line + ", ")
                current_line = meaning
            else:
                if current_line:
                    current_line += ", "
                current_line += meaning
        lines.append(current_line)

        # Render the text for Meanings
        for i, line in enumerate(lines):
            meanings_text = block_font.render(line, True, BLACK)
            block_surface.blit(meanings_text, (10, y_offset + i * 20))

        # Display the block on the screen
        block_x = BOARD_OFFSET_X + col * TILE_SIZE + TILE_SIZE + 10
        block_y = BOARD_OFFSET_Y + row * TILE_SIZE

        # Check if the block fits in the window
        remaining_height = HEIGHT - block_y
        if block_height > remaining_height:
            block_y -= block_height - remaining_height

        screen.blit(block_surface, (block_x, block_y))
        pygame.draw.rect(screen, BLACK, (block_x, block_y, block_width, block_height), 2)


def draw_score():
    global score
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


def new_game():
    global score, displayed_words, used_words
    score = 0
    displayed_words = []
    used_words = []
    game_loop()


def end_game():
    global running, displayed_words

    while True:
        screen.fill(BLACK)

        # Redraw words and handle hover/clicks
        displayed_word_rects = draw_centered_words()

        # Display "Game complete!" and the final score
        final_score_text = FONT.render("Game Complete!", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WIDTH // 2, 100))
        screen.blit(final_score_text, final_score_rect)

        # Create buttons for "New Game" and "Quit"
        new_game_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 120, 150, 50, "New Game", GREEN, WHITE)
        close_button = draw_button(WIDTH // 2 - 75, HEIGHT // 2 + 190, 150, 50, "Quit", RED, WHITE)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if new_game_button.collidepoint(mouse_x, mouse_y):
                    new_game()
                elif close_button.collidepoint(mouse_x, mouse_y):
                    running = False
                    pygame.quit()
                    sys.exit()

                else:
                    for word, rect in displayed_word_rects:
                        if rect.collidepoint(mouse_x, mouse_y):
                            if hovered_word_data_cache.get(word, [""])[
                                1] == "//no dictionary match - click on word for google search//":
                                webbrowser.open(f"https://www.google.com/search?q={word}&hl=ja&lr=lang_ja")
                            else:
                                webbrowser.open(f"https://jisho.org/search/{word}")

        # Update the display
        pygame.display.flip()


# Global list to store displayed words
displayed_words = []

def flash(new_words, board):
    global selected_tiles, score

    # Clear selected tiles to remove the red frame
    selected_tiles = []

    # Cache the original screen once
    original_surface = screen.copy()

    for word in new_words:
        if word in kword_list:
            # Identify the positions of the tiles that form the word
            word_positions = []

            # Search for the word horizontally or vertically
            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE - len(word) + 1):
                    if ''.join(board[row][col:col + len(word)]) == word:
                        word_positions = [(row, col + i) for i in range(len(word))]
                        break
            if not word_positions:  # Vertical search
                for col in range(GRID_SIZE):
                    for row in range(GRID_SIZE - len(word) + 1):
                        if ''.join(board[row + i][col] for i in range(len(word))) == word:
                            word_positions = [(row + i, col) for i in range(len(word))]
                            break

            if word_positions:
                # Create a translucent surface for flashing
                flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((0, 0, 0, 0))  # Transparent base

                for (row, col) in word_positions:
                    rect = pygame.Rect(
                        col * TILE_SIZE + BOARD_OFFSET_X,
                        BOARD_OFFSET_Y + row * TILE_SIZE,
                        TILE_SIZE, TILE_SIZE
                    )
                    pygame.draw.rect(flash_surface, YELLOW, rect)

                # Display the flash effect
                screen.blit(original_surface, (0, 0))  # Restore the original screen
                screen.blit(flash_surface, (0, 0))  # Overlay the flash

                # Render kanji, readings, and meaning
                readings, meaning = get_word_info_cached(word)
                draw_word_details(word, readings, meaning)
                pygame.display.flip()
                pygame.time.wait(1000)

                # Update the score and mark the word as used
                score += 1
                used_words.append(word)
                displayed_words.append(word)


def get_word_info_cached(word):
    """
    Fetch word details from the cache or fetch from the Jisho API if not cached.
    Handles partial matches, no matches, and errors, while caching results.
    """
    global hovered_word_data_cache

    # Check cache first
    if word in hovered_word_data_cache:
        return hovered_word_data_cache[word]

    try:
        # Fetch from Jisho API
        response = session.get(f"https://jisho.org/api/v1/search/words?keyword={word}")
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                # Iterate through results to find exact or partial matches
                for word_data in data['data']:
                    for japanese_entry in word_data.get("japanese", []):
                        if japanese_entry.get("word") == word or japanese_entry.get("reading") == word:
                            readings = [japanese_entry.get("reading", "")]
                            meanings = word_data['senses'][0]['english_definitions']
                            result = (readings, ", ".join(meanings))
                            hovered_word_data_cache[word] = result  # Cache the result
                            return result

                # No exact match, but partial data exists
                partial_result = [""], "//partial match - click on word to see meaning//"
                hovered_word_data_cache[word] = partial_result  # Cache partial result
                return partial_result

            # No dictionary match
            no_match_result = [""], "//no dictionary match - click on word for google search//"
            hovered_word_data_cache[word] = no_match_result  # Cache no match result
            return no_match_result

        # Non-200 response code
        error_result = [""], f"Error: API returned status code {response.status_code}"
        hovered_word_data_cache[word] = error_result  # Cache the error
        return error_result

    except Exception as e:
        # Handle network or JSON parsing errors
        error_result = ["Error"], f"Error: {str(e)}"
        hovered_word_data_cache[word] = error_result  # Cache the error
        return error_result


def draw_word_details(word, readings, meaning):
    """
    Display the selected word, its readings, and meanings at the bottom of the screen.
    """
    # Clear the bottom area for text
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - 100, WIDTH, 100))

    # Render kanji
    kanji_surface = FONT.render(word, True, WHITE)
    kanji_rect = kanji_surface.get_rect(topleft=(100, HEIGHT - 80))
    screen.blit(kanji_surface, kanji_rect)

    # Render furigana (readings)
    furigana_surface = pygame.font.Font("NotoSansJP-Black.ttf", 16).render(", ".join(readings), True, WHITE)
    furigana_rect = furigana_surface.get_rect(midbottom=(kanji_rect.centerx, kanji_rect.top + 10))
    screen.blit(furigana_surface, furigana_rect)

    # Render meaning
    meaning_surface = pygame.font.Font("NotoSansJP-Black.ttf", 20).render(f"- {meaning}", True, WHITE)
    meaning_x = kanji_rect.midright[0] + 10
    meaning_y = kanji_rect.midright[1]
    meaning_rect = meaning_surface.get_rect(midleft=(meaning_x, meaning_y))
    screen.blit(meaning_surface, meaning_rect)

    pygame.display.flip()



hovered_word = None  # Current hovered word
last_hovered_word = None  # Last hovered word and its info
last_hovered_data = None  # Stores data for the last hovered word (readings, meaning)


def draw_right_words():
    global displayed_words, hovered_word, hovered_word_data_cache

    mouse_x, mouse_y = pygame.mouse.get_pos()
    y_offset = BOARD_OFFSET_Y
    displayed_word_rects = []  # Cache word rects for click handling

    for word in displayed_words:
        # Render the displayed word
        word_surface = FONT.render(word, True, WHITE)
        word_rect = screen.blit(word_surface, (WIDTH - 200, y_offset))
        displayed_word_rects.append((word, word_rect))  # Store for click detection

        # Check if the mouse is hovering over this word
        if word_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BRIGHT_YELLOW, word_rect.inflate(10, 10), 2)  # Highlight on hover

            # Fetch word data only if necessary
            if hovered_word != word:
                hovered_word = word
                if word not in hovered_word_data_cache:
                    readings, meaning = get_word_info_cached(word)
                    hovered_word_data_cache[word] = (readings, meaning)


            # Ensure both readings and meaning are defined
            readings, meaning = hovered_word_data_cache.get(word, ([""], "//no dictionary match - click on word for google search//"))

            # Display the Kanji
            kanji_surface = FONT.render(word, True, WHITE)
            kanji_rect = kanji_surface.get_rect(topleft=(100, HEIGHT - 80))
            screen.blit(kanji_surface, kanji_rect)

            # Display the Furigana (above the Kanji)
            furigana_surface = pygame.font.Font("NotoSansJP-Black.ttf", 16).render(
                ", ".join(readings), True, WHITE
            )
            furigana_rect = furigana_surface.get_rect(midbottom=(kanji_rect.centerx, kanji_rect.top + 10))
            screen.blit(furigana_surface, furigana_rect)

            # Display the Meaning (to the right of the Kanji, middle-left aligned with Kanji's middle-right)
            meaning_surface = pygame.font.Font("NotoSansJP-Black.ttf", 20).render(f"- {meaning}", True, WHITE)
            meaning_x = kanji_rect.midright[0] + 10  # 10 pixels to the right of the Kanji
            meaning_y = kanji_rect.midright[1]  # Align vertically with the middle of the Kanji
            meaning_rect = meaning_surface.get_rect(midleft=(meaning_x, meaning_y))
            screen.blit(meaning_surface, meaning_rect)

        y_offset += 60

    return displayed_word_rects


def draw_centered_words():
    global displayed_words, hovered_word, hovered_word_data_cache

    mouse_x, mouse_y = pygame.mouse.get_pos()
    displayed_word_rects = []  # Cache word rects for click handling

    start_x = WIDTH // 3  # Start position for the first column
    start_y = 3 * BOARD_OFFSET_Y
    column_offset = WIDTH // 3  # Distance between columns
    words_per_column = 5  # Number of words per column

    for i, word in enumerate(displayed_words):
        col = i // words_per_column  # Determine the column based on index
        row = i % words_per_column  # Determine the row within the column

        x_offset = start_x + col * column_offset  # Offset for the column
        y_offset = start_y + row * 60  # Offset for the row

        # Render the displayed word
        word_surface = FONT.render(word, True, WHITE)
        word_rect = word_surface.get_rect(center=(x_offset, y_offset))
        screen.blit(word_surface, word_rect)
        displayed_word_rects.append((word, word_rect))  # Store for click detection

        # Check if the mouse is hovering over this word
        if word_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BRIGHT_YELLOW, word_rect.inflate(10, 10), 2)  # Highlight on hover

            # Fetch word data only if necessary
            if hovered_word != word:
                hovered_word = word
                if word not in hovered_word_data_cache:
                    readings, meaning = get_word_info_cached(word)
                    hovered_word_data_cache[word] = (readings, meaning)


            # Ensure both readings and meaning are defined
            readings, meaning = hovered_word_data_cache.get(word, (
            [""], "//no dictionary match - click on word for google search//"))

            # Display the kanji, furigana, and meaning at the bottom of the screen
            kanji_surface = FONT.render(word, True, WHITE)
            kanji_rect = kanji_surface.get_rect(topleft=(100, HEIGHT - 80))
            screen.blit(kanji_surface, kanji_rect)

            furigana_surface = pygame.font.Font("NotoSansJP-Black.ttf", 16).render(
                ", ".join(hovered_word_data_cache[word][0]), True, WHITE
            )
            furigana_rect = furigana_surface.get_rect(midbottom=(kanji_rect.centerx, kanji_rect.top + 10))
            screen.blit(furigana_surface, furigana_rect)

            # Display the meaning
            meaning_surface = pygame.font.Font("NotoSansJP-Black.ttf", 20).render(f"- {meaning}", True, WHITE)
            # Position the meaning's middle left at the middle of the Kanji's right
            meaning_x = kanji_rect.midright[0] + 10  # 10 pixels to the right of the Kanji
            meaning_y = kanji_rect.midright[1]  # Align vertically with the middle of the Kanji
            meaning_rect = meaning_surface.get_rect(midleft=(meaning_x, meaning_y))
            screen.blit(meaning_surface, meaning_rect)

    # Handle clicks on words for Google search during gameplay
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            for word, rect in displayed_word_rects:
                if rect.collidepoint(event.pos):
                    # Check if meaning is found
                    if hovered_word_data_cache.get(word, [""])[1] == "//no dictionary match - click on word for google search//":
                        webbrowser.open(f"https://www.google.com/search?q={word}&hl=ja&lr=lang_ja")
                    else:
                        webbrowser.open(f"https://jisho.org/search/{word}")

    return displayed_word_rects


def game_loop():
    global score, valid_words, selected_tiles, active_word
    board, valid_words = generate_board()
    clock = pygame.time.Clock()
    hovered_tile = None  # Tracks the currently hovered tile (row, col)

    running = True
    while running:
        screen.fill(BLACK)
        draw_board(board)
        draw_score()

        # Display words on the right side
        displayed_word_rects = draw_right_words()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                col = (mouse_x - BOARD_OFFSET_X) // TILE_SIZE
                row = (mouse_y - BOARD_OFFSET_Y) // TILE_SIZE
                if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
                    hovered_tile = (row, col)
                else:
                    hovered_tile = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                col = (mouse_x - BOARD_OFFSET_X) // TILE_SIZE
                row = (mouse_y - BOARD_OFFSET_Y) // TILE_SIZE
                if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
                    handle_tile_click(row, col, board)
                else:
                    selected_tiles = []
                    active_word = ""

                # Check for clicks on displayed words
                for word, rect in displayed_word_rects:
                    if rect.collidepoint(mouse_x, mouse_y):
                        if hovered_word_data_cache.get(word, [""])[1] == "//no dictionary match - click on word for google search//":
                            webbrowser.open(f"https://www.google.com/search?q={word}&hl=ja&lr=lang_ja")
                        else:
                            webbrowser.open(f"https://jisho.org/search/{word}")

        if hovered_tile:
            row, col = hovered_tile
            handle_tile_hover(row, col, board)

        if score >= 10:
            end_game()

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()


if __name__ == "__main__":
    game_loop()

