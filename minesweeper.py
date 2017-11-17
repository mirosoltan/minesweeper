"""
A remake of the classic Minesweeper game, with class structures

                        made by

--------------------Miroslav Georgiev--------------------------
"""

import pygame, random, sys
import sqlite3 as lite
from pygame.locals import *

# Constants
FPS = 30
BOXSIZE = 30
GAP = 1
MARGIN = 5
SIDELINE = 70
EXPLOSION_DIM = (128, 128)
SIZE_REFERENCE = {10: 'small', 40: 'medium', 100: 'large'}
FONT_REFERENCE = {9: 22, 16: 26, 30: 30}
NEW_GAME_REFERENCE = {'small': [9, 9, 10],
                      'medium': [16, 16, 40],
                      'large': [16, 30, 100]}

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
GRAY     = ( 160, 160, 160)
BLUE     = (   0,   0, 255)   
GREEN    = (  24, 217,  98)
RED      = ( 255,   0,   0)
PURPLE   = ( 128,   0, 128)
TEAL     = (   0, 128, 128)
YELLOW   = ( 232, 179,   5)
AQUA     = (   0, 255, 255)
SILVER   = ( 190, 190, 190) 
# Numbers associative array
NUMBER_COLORS = {1: BLUE, 2: GREEN, 3: RED, 4: PURPLE,
                 5: TEAL, 6: YELLOW, 7: AQUA, 8: SILVER}
BGCOLOR = BLACK

# Helper Queue class
class Queue:
    """
    A simple implementation of a FIFO queue.
    """
    def __init__(self):
        """ 
        Initialize the queue.
        """
        self._items = []

    def __len__(self):
        """
        Return the number of items in the queue.
        """
        return len(self._items)
    
    def __iter__(self):
        """
        Create an iterator for the queue.
        """
        for item in self._items:
            yield item

    def __str__(self):
        """
        Return a string representation of the queue.
        """
        return str(self._items)

    def enqueue(self, item):
        """
        Add item to the queue.
        """        
        self._items.append(item)

    def dequeue(self):
        """
        Remove and return the least recently inserted item.
        """
        return self._items.pop(0)

    def clear(self):
        """
        Remove all items from the queue.
        """
        self._items = []

# Main Minesweeper class
class Minefield():
    def __init__(self, height, width, num_mines, saved_field=None):
        """ Initialize a minefield with height number of rows,
            width number of columns and num_mines number of mines.
            Optional - pass an existing minefield. """
        if saved_field:
            # Used to continue a Saved game; if a previous minefield was passed, get its data
            self.retrieve_state(saved_field)
        else:  
            # Set a new minefield according to given width, height and num_mines
            self._height = height            # minefield dimensions 
            self._width = width
            self._num_mines = num_mines      # number of mines in the minefield
            self._revealed = [[False for num_rows in xrange(self._width)] # array of booleans 
                              for num_cols in xrange(self._height)]       # holding revealed cells 
            self._minefield = [[0 for num_rows in xrange(self._width)]  # array of numbers holding 
                               for num_cols in xrange(self._height)]    # mines and hint numbers
        self._size = SIZE_REFERENCE[self._num_mines]                   # for score tracking purposes     
                                    
    def __str__(self):
        info = ""
        for row in range(self._height):            
            info += str(self._minefield[row])
            info += "\n"
        return info

    def get_height(self):
        return self._height

    def get_width(self):
        return self._width

    def get_num_mines(self):
        return self._num_mines              

    def get_neighbors(self, row, col):
        """ Return all neighbor cells to cell in row, col as a list of tuples """
        ans = []
        if row > 0:
            ans.append((row - 1, col))
        if row < self._height - 1:
            ans.append((row + 1, col))
        if col > 0:
            ans.append((row, col - 1))
        if col < self._width - 1:
            ans.append((row, col + 1))
        if (row > 0) and (col > 0):
            ans.append((row - 1, col - 1))
        if (row > 0) and (col < self._width - 1):
            ans.append((row - 1, col + 1))
        if (row < self._height - 1) and (col > 0):
            ans.append((row + 1, col - 1))
        if (row < self._height - 1) and (col < self._width - 1):
            ans.append((row + 1, col + 1))
        return ans

    def get_cell_clicked(self, x, y):
        """ Return contents of clicked cell """
        cell_x = y // (BOXSIZE + GAP)
        cell_y = x // (BOXSIZE + GAP)        
        return  (cell_x, cell_y)
    
    def build_grid(self, cell_clicked):
        """ Build a two-dimensional array where 0 represents an empty space,
            9 represents a mine, and numbers 1 - 8 inform how many mines
            there are nearby. """
        # seed mines
        self.seed_mines(cell_clicked)
        # update other fields with numbers according to nearby mines
        for row in range(self._height):
            for col in range(self._width):
                if self._minefield[row][col] == 9:
                    continue
                cell = (row, col)
                neighbors = self.get_neighbors(cell[0], cell[1])
                number = 0
                for neighbor in neighbors:
                    if self._minefield[neighbor[0]][neighbor[1]] == 9:
                        number += 1
                self._minefield[row][col] = number          

    def seed_mines(self, cell_clicked):
        """ Update self._minefield with self._num_mines
            placed randomly. """
        self._mine_locs = [] # array to keep track of mine locations
        rem_mines = self._num_mines
        while rem_mines > 0:
            # choose a random location
            random_loc = (random.randrange(self._height),
                          random.randrange(self._width))
            if random_loc == cell_clicked:
                # don't put a mine in the cell clicked
                continue
            elif self._minefield[random_loc[0]][random_loc[1]] == 9:
                # skip the cell if there's already a mine there
                continue
            else:
                # place a mine
                self._minefield[random_loc[0]][random_loc[1]] = 9
                self._mine_locs.append(random_loc)
                rem_mines -= 1
        self._mine_locs = sorted(self._mine_locs)        

    def reveal(self, cell):
        """ Reveal a given cell """
        self._revealed[cell[0]][cell[1]] = True

    def mass_reveal(self, cell):
        """ Reveal recursively given cell and all other neighbor empty cells """
        neighbors = self.get_neighbors(cell[0], cell[1])

        for neighbor in neighbors:
            if self._revealed[neighbor[0]][neighbor[1]]:
                continue
            else:
                self._revealed[neighbor[0]][neighbor[1]] = True
                if self._minefield[neighbor[0]][neighbor[1]] == 0:
                    self.mass_reveal(neighbor)                    
               
    def retrieve_state(self, saved_data):
        """ Set class fields according to saved_data.
            Saved_data is a dictionary """
        self._height = saved_data['height']
        self._width = saved_data['width']
        self._num_mines = saved_data['num_mines']
        self._minefield = saved_data['minefield']
        self._revealed = saved_data['revealed']
        self._mine_locs = saved_data['mine_locs']        

    def draw(self, surface):
         for x_dim in range(self._width):
            for y_dim in range(self._height):                
                if self._revealed[y_dim][x_dim]:                    
                     pygame.draw.rect(surface, WHITE, [(GAP + BOXSIZE) * x_dim + MARGIN,
                                                 (GAP + BOXSIZE) * y_dim + MARGIN,
                                                 BOXSIZE, BOXSIZE])
                     if self._minefield[y_dim][x_dim] == 0 or self._minefield[y_dim][x_dim] == 9:
                         continue                     
                     number_surf = self.draw_number(surface, self._minefield[y_dim][x_dim],
                                                    FONT1, NUMBER_COLORS[self._minefield[y_dim][x_dim]])
                     surface.blit(number_surf, ((GAP + BOXSIZE) * x_dim + MARGIN + 10,
                                  (GAP + BOXSIZE) * y_dim + MARGIN + 3))
                else:
                     surface.blit(box_image, ((GAP + BOXSIZE) * x_dim + MARGIN,
                                                 (GAP + BOXSIZE) * y_dim + MARGIN))                                                                  
                     
    def draw_number(self, surface, number, font, color):
        return font.render(str(number), True, color)

class Game_parameters():
    """ Class manipulating the rest of game parameters """
    def __init__(self, remaining_mines, saved_data=None):
        if saved_data:
            # Pass saved data, if any
            self.retrieve_info(saved_data)
        else:           
            self._marked_fields = [] # holds mines marked by player
            self._questions = []     # holds fields marked as questionable by player
            self._timer = 0          # measures game time
            self._remaining_mines = remaining_mines  # holds number of remaining mines for
            self._first_click = True    # keep track of the first mouseclick to start timer and other stuff
        self._font1 = pygame.font.SysFont("TimesNewRoman", 22)
        self._font2 = pygame.font.SysFont("TimesNewRoman", 16)        
        self._in_progress = True    # keep track of whether the game is still in progress for saving purposes
       
    def get_time(self):
        return self._timer

    def get_remaining_mines(self):
        return self._remaining_mines   

    def define_screensize(self, minefield):
        """ Define the screen dimensions using the minefield dimensions """
        self._screensize_x = minefield.get_width()
        self._screensize_y = minefield.get_height()
        self._screen_middle = ((MARGIN + (BOXSIZE + GAP) * self._screensize_x + MARGIN) // 2,
                              (MARGIN + (BOXSIZE + GAP) * self._screensize_y + MARGIN + SIDELINE) // 2)
        self._font3 = pygame.font.SysFont("TimesNewRoman", FONT_REFERENCE[minefield.get_width()])

    def get_screen_dimensions(self):
        return self._screensize_x, self._screensize_y, self._screen_middle

    def mark_field(self, cell, lst):
        """ Insert a mark into the list lst in appropriate order """
        if not lst:
            lst.append(cell)
        else:           
            # first check edge cases to avoid looping
            if cell < lst[0]:
                lst.insert(0, cell)
            elif cell > lst[-1]:
                lst.append(cell)
            else:
                for marked in lst:
                    if marked < cell:                        
                        continue  # cell is still bigger than marked
                    elif marked == cell:
                        # cell is on the same row as marked; check the column
                        if marked[1] < cell[1]:                            
                            continue
                        else:                            
                            lst.insert(lst.index(marked), cell)
                            break
                    else:                        
                        lst.insert(lst.index(marked), cell)  
                        break
        if lst == self._marked_fields:
            self._remaining_mines -= 1

    def unmark_mine(self, mine):
        """ Remove a mine from the list of marked mines """
        self.mark_field(self._marked_fields.pop(self.find_mine(mine, self._marked_fields, self._marked_fields)),
                        self._questions)
        self._remaining_mines += 1        

    def unmark_question(self, field):
        """ Remove a question mark from the list self._questions """
        self._questions.pop(self.find_mine(field, self._questions, self._questions))

    def close_game(self):
        self._in_progress = False

    def check_first_click(self):
        self._first_click = False

    def find_mine(self, mine, mine_list, original_list):
        """ Do a binary search to find a mine in the list of marked mines;
            Return its index """
        if mine_list[0] == mine:            
            return original_list.index(mine_list[0])
        else:
            current = mine_list[len(mine_list) // 2]
            upper = mine_list[len(mine_list) // 2 + 1:]
            lower = mine_list[:len(mine_list) // 2]

            if current == mine:                
                return original_list.index(current)
            else:               
                if mine > current :
                    return self.find_mine(mine, upper, original_list)
                elif mine < current:
                    return self.find_mine(mine, lower, original_list)                    
                 
    def retrieve_info(self, data):
        """ Get fields from saved data """        
        self._timer = data['timer']
        self._remaining_mines = data['remaining']
        self._marked_fields = data['marked']
        self._questions = data['questions']
        self._first_click = False   
        
    def draw(self, canvas, screensize):
        """ Draw the interface below the playfield, as well as
            marked mines and question marks """
        for mark in state._marked_fields:
            canvas.blit(mine_image, ((BOXSIZE + GAP) * mark[1] + MARGIN,
                                     (BOXSIZE + GAP) * mark[0]  + MARGIN))
        for question in state._questions:
            canvas.blit(question_image, ((BOXSIZE + GAP) * question[1] + MARGIN,
                                     (BOXSIZE + GAP) * question[0]  + MARGIN))     
        
        pygame.draw.rect(canvas, WHITE, [screensize[0] - 100, screensize[1] - 40, 40, 30])
        pygame.draw.rect(canvas, WHITE, [55, screensize[1] - 40, 50, 30])
        # draw timer
        time, time_rect = makeText("game time:", FONT3, WHITE)
        time_num, time_num_rect = makeText(str(self._timer), FONT1, BLACK)
        canvas.blit(time, (80 - time_rect.centerx, screensize[1] - 65))
        canvas.blit(time_num, (80 - time_num_rect.centerx, screensize[1] - 38))
        #  draw mines counter
        rem_mines, rem_mines_rect = makeText("mines remaining:", FONT3, WHITE)
        num_rem_mines, num_rem_mines_rect = makeText(str(self._remaining_mines), FONT1, BLACK)
        canvas.blit(num_rem_mines, ((screensize[0] - 81) - num_rem_mines_rect.centerx,
                                  screensize[1] - 38))
        canvas.blit(rem_mines, ((screensize[0] - 81) - rem_mines_rect.centerx,
                               screensize[1] - 65))
        

# ------------------------ Main program ---------------------------------------- #
def main():
    global SCREEN, SCREENSIZE, CLOCK, FONT1, FONT3
    global grid, state, box_image, mine_image, question_image, med_button_image, explosion_image

    pygame.init()
    CLOCK = pygame.time.Clock()
    pygame.time.set_timer(USEREVENT+1, 1000)
    FONT1 = pygame.font.SysFont("TimesNewRoman", 22)
    FONT3 = pygame.font.SysFont("TimesNewRoman", 16)
    pygame.display.set_caption("My minesweeper")
    box_image = pygame.image.load('box_image.png')
    mine_image = pygame.image.load('mine_image.png')
    question_image = pygame.image.load('question.png')
    med_button_image = pygame.image.load('button_medium.png')
    explosion_image = pygame.image.load('explosion_alpha.png')
    # Start sequence
    start_game()
    
    state.define_screensize(grid)      
    GRIDSIZEX, GRIDSIZEY, MIDDLE = state.get_screen_dimensions()
    SCREENSIZE = ((MARGIN + (BOXSIZE + GAP) * GRIDSIZEX + MARGIN),
                  (MARGIN + (BOXSIZE + GAP) * GRIDSIZEY + MARGIN + SIDELINE))
    SCREEN = pygame.display.set_mode(SCREENSIZE)

    while True:
        # Main loop
        click = check_for_mouseclick()
        if click:               
            mouse_x = click.pos[0] - 6
            mouse_y = click.pos[1] - 6
            if click.pos[0] < 5 or click.pos[0] > ((MARGIN + (BOXSIZE + GAP) * GRIDSIZEX)) or \
                   click.pos[1] < 5 or click.pos[1] > ((MARGIN + (BOXSIZE + GAP) * GRIDSIZEY)):
                   pass             # ignore click if outside the grid
            else:
                cell = grid.get_cell_clicked(mouse_x, mouse_y)
                if click.button == 1:
                    if state._first_click:
                        # build mines array and dependent data on the first click
                        grid.build_grid(cell)
                        state.check_first_click()                       
                        if grid._minefield[cell[0]][cell[1]] == 0:
                            grid.reveal(cell)
                            grid.mass_reveal(cell)
                        else:
                            grid.reveal(cell)
                    else:
                        
                        if grid._minefield[cell[0]][cell[1]] == 9:
                            # you hit a mine, game over!
                            explode(click.pos)
                            game_over("You lose!")

                        else:
                            if grid._minefield[cell[0]][cell[1]] == 0:
                                grid.reveal(cell)
                                grid.mass_reveal(cell)
                            else:
                                grid.reveal(cell)
                    
                elif click.button == 3:
                    # handle right-clicks
                    if cell in state._marked_fields:
                        state.unmark_mine(cell)
                    elif cell in state._questions:
                        state.unmark_question(cell)
                    else:
                        if not grid._revealed[cell[0]][cell[1]]:
                            state.mark_field(cell, state._marked_fields)
                        if grid._mine_locs == state._marked_fields:
                            game_over("You win!")                   
        
        SCREEN.fill(BGCOLOR)
        # drawing
        grid.draw(SCREEN)
        state.draw(SCREEN, SCREENSIZE)                  
                
        pygame.display.update()
        CLOCK.tick(FPS)

def check_for_mouseclick():
    """ Check the event queue for MOUSECLICK and some other events; return
        the first MOUSEBUTTONUP event """
    for event in pygame.event.get():
        if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
            if state._in_progress and state._first_click:
                terminate()
            elif state._in_progress:
                if querry(SCREEN, SCREENSIZE, "Save your game?"):
                    terminate(True)
                else:
                    terminate()
            else:
                terminate()
        if event.type == USEREVENT+1 and not state._first_click:
            state._timer += 1
        if event.type == MOUSEBUTTONUP:            
            return event

def makeText(text, font, color):
    """ Return a tuple of a text surface with given font and color, and a text rect """
    textSurf = font.render(text, True, color)
    textRect = textSurf.get_rect()
    textRect.centerx = textRect.width // 2
    textRect.centery = textRect.height // 2
    return (textSurf, textRect)

def loadButton(text, textColor, font, image, top, left):
    """ Return a tuple with a button with a given text centralized on it,
        and also return its Rect """
    textSurf, textRect = makeText(text, font, textColor)
    imageRect = image.get_rect()
    imageRect.center = (imageRect[2] // 2, imageRect[3] // 2)
    imageSurf = pygame.Surface ((imageRect[2], imageRect[3]))
    imageSurf.blit(image, imageRect)
    imageSurf.blit(textSurf, (imageRect.center[0] - textRect.centerx,
                                      imageRect.center[1] - textRect.centery))
    imageRect.topleft = (top, left)          
    return (imageSurf, imageRect)

def querry(surface, screensize, message):
    """ Display a querry window with a given message 
        and buttons for a Yes / No answer """
    MIDDLE = (screensize[0] // 2, screensize[1] // 2)
    
    yesButton, yesButtonRect = loadButton("Yes", BLACK, FONT3, med_button_image,
                                          MIDDLE[0] - 100, MIDDLE[1]) 
    noButton, noButtonRect = loadButton("No, thanks", RED, FONT3,  med_button_image,
                                        MIDDLE[0], MIDDLE[1])
    text, textRect = makeText(message, FONT1, BLACK)    
    
    while True:
        for event in pygame.event.get():    # Event handling
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONUP:
                if yesButtonRect.collidepoint(event.pos[0], event.pos[1]):
                    return True
                elif noButtonRect.collidepoint(event.pos[0], event.pos[1]):
                    return False                    

        surface.fill(BGCOLOR)
        pygame.draw.rect(surface, WHITE, [MIDDLE[0] - 152, MIDDLE[1] - 67, 304, 134])
        pygame.draw.rect(surface, SILVER, [MIDDLE[0] - 150, MIDDLE[1] - 65, 300, 130])
        surface.blit(text, (MIDDLE[0] - textRect.centerx, MIDDLE[1] - 50))
        surface.blit(yesButton, yesButtonRect)
        surface.blit(noButton, noButtonRect)
        
        pygame.display.update()
        CLOCK.tick(FPS)
    
def start_game():
    """ Show the starting screen, do necessary stuff """
    global grid, state
    GRIDSIZEX = 12
    GRIDSIZEY = 6
    FONT = pygame.font.SysFont("TimesNewRoman", 22)
    SCREENSIZE = ((MARGIN + (BOXSIZE + GAP) * GRIDSIZEX + MARGIN),
              (MARGIN + (BOXSIZE + GAP) * GRIDSIZEY + MARGIN))
    MIDDLE = (SCREENSIZE[0] // 2, SCREENSIZE[1] // 2)
    screen = pygame.display.set_mode(SCREENSIZE)
    new_game = False
    
    # access database file
    con = lite.connect("mines_data.db")
    cursor = con.cursor()
    try:        
        cursor.execute("SELECT best_time FROM results")        
    except:
        # the case of the very first game on a machine, when the DB hasn't been created yet
        cursor.execute("CREATE TABLE results(id TEXT, best_time INT)")
        con.commit()
        con.close()
    try:
        # attempt to access a minefield record - if successful, ask         
        cursor.execute("SELECT * FROM minefield")
        if querry(screen, SCREENSIZE, "Continue your saved game?"):
            # user decided to continue saved game; retrieve the data
            grid_data, state_data = retrieve_saved_data(con, cursor)        
            grid = Minefield(9, 9, 10, grid_data)           
            state = Game_parameters(10, state_data)           
            return   
        else:
            # user decided to start a new game, delete saved game data
            drop_data(con, cursor)
            con.commit()
            con.close()
            new_game = True
    except:
        # no saved game
        con.close()
        new_game = True

    if new_game:    
        smallButton, smallRect = loadButton("Small", BLACK, FONT1, med_button_image, 40, 100)
        mediumButton, mediumRect = loadButton("Medium", BLACK, FONT1, med_button_image, 145, 100)
        largeButton, largeRect = loadButton("Large", BLACK, FONT1, med_button_image, 250, 100)
        text, textRect = makeText("Please choose size of field:", FONT, WHITE)
        
        done = False
        while not done:
            for event in pygame.event.get():    # Event handling
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    terminate()
                if event.type == MOUSEBUTTONUP:
                    if smallRect.collidepoint(event.pos[0], event.pos[1]):
                        grid = Minefield(9, 9, 10)
                        state = Game_parameters(10)
                        done = True
                    elif mediumRect.collidepoint(event.pos[0], event.pos[1]):
                        grid = Minefield(16, 16, 40)
                        state = Game_parameters(40)
                        done = True
                    elif largeRect.collidepoint(event.pos[0], event.pos[1]):
                        grid = Minefield(16, 30, 100)
                        state = Game_parameters(100)
                        done = True  

            screen.fill(BGCOLOR)
            screen.blit(text, (MIDDLE[0] - textRect.centerx, MIDDLE[1] - 60))
            screen.blit(smallButton, smallRect)
            screen.blit(mediumButton, mediumRect)
            screen.blit(largeButton, largeRect)

            pygame.display.update()
            CLOCK.tick(FPS)       

def explode(pos):
    """ Draw the explosion animation and mine locations. 
        This happens when the player hits a mine."""
    time = 0
    done = False
    while not done:        
        SCREEN.fill(BGCOLOR)
        grid.draw(SCREEN)
        state.draw(SCREEN, SCREENSIZE)
        # draw mine locations as red circles
        for mine in grid._mine_locs:
            pygame.draw.circle(SCREEN, RED, (mine[1] * (BOXSIZE + GAP) + 20,
                                             mine[0] * (BOXSIZE + GAP) + 20), 10)
        # draw the explosion animation    
        SCREEN.blit(explosion_image, [pos[0] - EXPLOSION_DIM[0] // 2,
                                      pos[1] - EXPLOSION_DIM[1] //2,
                                      EXPLOSION_DIM[0], EXPLOSION_DIM[1]],
                    [EXPLOSION_DIM[0] * time, 0, EXPLOSION_DIM[0], EXPLOSION_DIM[1]])
        time += 1
        if time > 24:
            done = True
        pygame.display.update()
        CLOCK.tick(FPS)    
    
def game_over(message):
    """ Terminate the game, either because player won
        or hit a mine. Update database as necessary. """
    global grid, state
    state.close_game()
    rec_message = ""
    # get previous results from the database, if any
    con = lite.connect("mines_data.db")
    cur = con.cursor()        
    cur.execute("SELECT best_time FROM results WHERE id=?", (grid._size,))
    rec = cur.fetchone()    
    if message == "You win!":
        # Update the game database. ASSUME that one exists already,
        # and there are some basic records in it        
        if rec:
            # try to find the record for this grid size, create it if unsuccessful            
            if state.get_time() < rec[0]:                
                # you've achieved a new record, store it, update rec_message
                cur.execute("UPDATE results SET best_time=? WHERE id=?", (state.get_time(), grid._size))
                rec_message = "NEW RECORD! " + str(state.get_time())
            else:                
                rec_message = "Your time: " + str(state.get_time()) + "; Best time: " + str(rec[0])
        else:
            # There was no record for this size, create it
            rec_message = "No best time yet" 
            cur.execute("INSERT INTO results VALUES(?, ?)", (grid._size, state._timer))  
    else:
        if rec:
            rec_message = "Best time for this size: " + str(rec[0])
        else:
            rec_message = "No best time yet"
    con.commit()
    con.close()

    done = False
    GRIDSIZEX, GRIDSIZEY, MIDDLE = state.get_screen_dimensions()    
    yesButton, yesButtonRect = loadButton("YES!!!", PURPLE, FONT1, med_button_image,
                                          MIDDLE[0] - 100, MIDDLE[1] + 50) 
    noButton, noButtonRect = loadButton("No, exit", RED, FONT1, med_button_image,
                                        MIDDLE[0], MIDDLE[1] + 50)
    text, textRect = makeText(message, FONT1, RED)
    text2, text2Rect = makeText(rec_message, FONT3, BLACK)
    text3, text3Rect = makeText("Care for another game?", FONT3, BLACK)    
    
    while not done:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                terminate()
            if event.type == MOUSEBUTTONUP:
                if yesButtonRect.collidepoint(event.pos[0], event.pos[1]):
                    new_game_data = NEW_GAME_REFERENCE[grid._size]
                    grid = Minefield(new_game_data[0], new_game_data[1], new_game_data[2])
                    state = Game_parameters(new_game_data[2])
                    state.define_screensize(grid)
                    done = True
                elif noButtonRect.collidepoint(event.pos[0], event.pos[1]):
                    terminate()                        
                
        SCREEN.fill(SILVER)

        SCREEN.blit(text, (MIDDLE[0] - textRect.centerx, MIDDLE[1] - 100))
        SCREEN.blit(text2, (MIDDLE[0] - text2Rect.centerx, MIDDLE[1] - 50))
        SCREEN.blit(text3, (MIDDLE[0] - text3Rect.centerx, MIDDLE[1]))
        
        SCREEN.blit(yesButton, yesButtonRect)
        pygame.draw.rect(SCREEN, GREEN, [yesButtonRect[0] - 3, yesButtonRect[1] - 3, yesButtonRect[2] + 5,
                                          yesButtonRect[3] + 5], 4)
        SCREEN.blit(noButton, noButtonRect)
        pygame.draw.rect(SCREEN, RED, [noButtonRect[0] - 3, noButtonRect[1] - 3, noButtonRect[2] + 5,
                                          noButtonRect[3] + 5], 4)

        pygame.display.update()
        CLOCK.tick(FPS)
        
def adapt_list(lst):
    """ Convert a list of numbers or booleans into string """
    if type(lst[0]) == bool:
        result = []
        for itm in lst:
            if itm:
                result.append(1)
            else:
                result.append(0)        
        return ",".join(str(num) for num in result)
        
    return  ",".join(str(num) for num in lst)

def adapt_tuple(t):
    """ Convert a tuple into a string """
    return ",".join(str(num) for num in t)
        
def convert_into_num_list(s):
    """ Convert a string into a list of numbers """
    return map(int, s.split(","))

def convert_into_tuple(s):
    """ Convert a string into a tuple """
    return tuple(map(int, s.split(",")))

def convert_into_bool(s):
    """ Convert a string into a list of booleans """
    result = []
    temp = map(int, s.split(","))
    for itm in temp:
        if itm == 0:
            result.append(False)
        else:
            result.append(True)
    return result   
 
def drop_data(connection, cursor):
    """ Synthactic sugar: clear a series of tables from the db """
    cursor.execute("DROP TABLE IF EXISTS main_data")
    cursor.execute("DROP TABLE IF EXISTS minefield")
    cursor.execute("DROP TABLE IF EXISTS revealed")
    cursor.execute("DROP TABLE IF EXISTS mine_locs")
    cursor.execute("DROP TABLE IF EXISTS marked")
    cursor.execute("DROP TABLE IF EXISTS questions")
   
    connection.commit()
    
def retrieve_saved_data(con, cursor):
    """ Access a database file and get the necessary data
        to start a new game """
    grid_data = {}
    state_data = {}
    
    # get main game data
    cursor.execute("SELECT * FROM main_data")
    main_data = cursor.fetchone()    
    grid_data['height'] = main_data[0]
    grid_data['width'] = main_data[1]
    grid_data['num_mines'] = main_data[2]
    state_data['remaining'] = main_data[3]
    state_data['timer'] = main_data[4]
   
    # get the minefield
    cursor.execute("SELECT * from minefield")
    field = [convert_into_num_list(row[0]) for row in cursor.fetchall()]      
    grid_data['minefield'] =  field
    # get the revealed cells
    cursor.execute("SELECT * from revealed")
    revealed = [convert_into_bool(row[0]) for row in cursor.fetchall()]        
    grid_data['revealed'] = revealed
    # get mine locations
    cursor.execute("SELECT * from mine_locs")
    locs = [convert_into_tuple(row[0]) for row in cursor.fetchall()]
    grid_data['mine_locs'] = locs
    # get marked cells
    cursor.execute("SELECT * from marked")
    marked = [convert_into_tuple(row[0]) for row in cursor.fetchall()]
    state_data['marked'] = marked
    cursor.execute("SELECT * from questions")
    question = [convert_into_tuple(row[0]) for row in cursor.fetchall()]
    state_data['questions'] = question
    
    # finished retrieving, drop the tables and close connection
    drop_data(con, cursor)    
    con.commit()
    con.close()
    return grid_data, state_data         
      
def terminate(save=False):
    """ Terminate the program. Save data to db as necessary """
    con = lite.connect("mines_data.db")
    cur = con.cursor()
    
    if save:       
        # the game is in progress; save game data so that
        # it can be resumed later; First create the tables:
        cur.execute("DROP TABLE IF EXISTS main_data")
        cur.execute("DROP TABLE IF EXISTS minefield")
        cur.execute("DROP TABLE IF EXISTS revealed")
        cur.execute("DROP TABLE IF EXISTS mine_locs")
        cur.execute("DROP TABLE IF EXISTS marked")
        cur.execute("DROP TABLE IF EXISTS questions")
        
        cur.execute("CREATE TABLE main_data(height INT, width INT, num_mines INT, remaining INT, timer INT)")
        cur.execute("CREATE TABLE minefield(row TEXT)")
        cur.execute("CREATE TABLE revealed(row TEXT)")
        cur.execute("CREATE TABLE mine_locs(tup TEXT)")
        cur.execute("CREATE TABLE marked(tup TEXT)")
        cur.execute("CREATE TABLE questions(tup TEXT)")
        # populate tables one by one
        cur.execute("INSERT INTO main_data VALUES(?, ?, ?, ?, ?)",
                    (grid.get_height(), grid.get_width(), grid.get_num_mines(),
                     state.get_remaining_mines(), state.get_time()))
        for row in grid._minefield:
            cur.execute("INSERT INTO minefield VALUES(?)", (adapt_list(row),))

        for row in grid._revealed:
            cur.execute("INSERT INTO revealed VALUES(?)", (adapt_list(row),))

        for tup in grid._mine_locs:
            cur.execute("INSERT INTO mine_locs VALUES(?)", (adapt_tuple(tup),))

        for tup in state._marked_fields:
            cur.execute("INSERT INTO marked VALUES(?)", (adapt_tuple(tup),))

        for tup in state._questions:
            cur.execute("INSERT INTO questions VALUES(?)", (adapt_tuple(tup),))
            
        con.commit()
        con.close()
        
    pygame.quit()
    sys.exit()    

if __name__ == '__main__':
    main()
