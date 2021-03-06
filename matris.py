#!/usr/bin/env python
import pygame
from pygame import Rect, Surface
import random
import os
import kezmenu
import agent
import sys
import pickle

from tetrominoes import list_of_tetrominoes
from tetrominoes import rotate

from scores import load_score, write_score

class GameOver(Exception):
    """Exception used for its control flow properties"""

def get_sound(filename):
    return pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "resources", filename))

BGCOLOR = (15, 15, 20)
BORDERCOLOR = (140, 140, 140)

BLOCKSIZE = 30
BORDERWIDTH = 10

MATRIS_OFFSET = 20

MATRIX_WIDTH = 10
MATRIX_HEIGHT = 22

LEFT_MARGIN = 340

WIDTH = MATRIX_WIDTH*BLOCKSIZE + BORDERWIDTH*2 + MATRIS_OFFSET*2 + LEFT_MARGIN
HEIGHT = (MATRIX_HEIGHT-2)*BLOCKSIZE + BORDERWIDTH*2 + MATRIS_OFFSET*2

TRICKY_CENTERX = WIDTH-(WIDTH-(MATRIS_OFFSET+BLOCKSIZE*MATRIX_WIDTH+BORDERWIDTH*2))/2

VISIBLE_MATRIX_HEIGHT = MATRIX_HEIGHT - 2

class Matris(object):
    board = agent.board()
    agent_mode = True #used to check if agent is playing. Causes hard-drops to always happen.
    if agent_mode == True:
        if (sys.argv[1] == "-hh"):
            #Creates an agent that takes column differences, holes and height of the tallest column as inputs
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000, height=True, holes=True)
        elif (sys.argv[1] == "-ho"):
            #Creates an agent that takes column differences and holes as inputs
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000, holes=True)
        elif (sys.argv[1] == "-hi"):
            #Creates an agent that takes column differences and height of the tallest column as inputs
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000, height=True)
        elif (sys.argv[1] == "-no"):
            #Creates an agent that takes column differences as inputs only
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000)
        elif (sys.argv[1] == "-ra"):
            #Creates an agent that plays randomly
            agent = agent.agent([],int(sys.argv[2]), random_moves = True)
        elif (sys.argv[1] == "-lo"):
            #Loads an agent that has previously been trained in MaTris. Loads .obj file.
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000, filepath = sys.argv[3])
        elif (sys.argv[1] == "-lt"):
            #Loads an agent that has previously been trained using supervised learning in MaTris-O. Loads .obj file.
            agent = agent.agent([],int(sys.argv[2]), random_moves = False, rewards_as_lines=True, epsilon=1, epsilon_decay=0.01, epsilon_minimum=0.01, memory_size=1000, sample_size=32, reset_steps=1000, filepath = sys.argv[3], supervised=True)
          
        else:
            raise Exception( error_message = "\n\nError inputting command line arguments\nUsage:\n[mode] [number of episodes]\nmode:\n\t-hh - holes and height and column differences\n\t-ho - holes and column differences\n\t-hi - height and column differences\n\t-no - column differences only\n\tLoad ANN\nSecond argument should be number of episodes\n third argument should be filepath if file is being loaded.")
    seed = agent.load_new_seed()
    random.seed(seed)
    tetromino_placement = None

    def __init__(self):
        self.surface = screen.subsurface(Rect((MATRIS_OFFSET+BORDERWIDTH, MATRIS_OFFSET+BORDERWIDTH),
                                              (MATRIX_WIDTH * BLOCKSIZE, (MATRIX_HEIGHT-2) * BLOCKSIZE)))
        
        self.matrix = dict()
        for y in range(MATRIX_HEIGHT):
            for x in range(MATRIX_WIDTH):
                self.matrix[(y,x)] = None
        """
        `self.matrix` is the current state of the tetris board, that is, it records which squares are
        currently occupied. It does not include the falling tetromino. The information relating to the
        falling tetromino is managed by `self.set_tetrominoes` instead. When the falling tetromino "dies",
        it will be placed in `self.matrix`.
        """

        self.next_tetromino = random.choice(list_of_tetrominoes)
        self.set_tetrominoes()

        if self.agent_mode == True:
            #Creates a representation of the initial board
            self.board.update_board_representation(self.create_board_representation())
            self.board.set_board_height()
            self.board.set_holes()
            self.board.set_column_differences()
            print(str(self.board))
            print("Column Height Differences:" + str(self.board.get_column_differences()))

            #Set up the the agent
            self.agent.set_current_board(self.board)
            self.agent.set_agent_tetromino(self.current_tetromino)

        self.tetromino_rotation = 0
        self.downwards_timer = 0
        self.base_downwards_speed = 0.4 # Move down every 400 ms

        self.movement_keys = {'left': 0, 'right': 0}
        self.movement_keys_speed = 0.05
        self.movement_keys_timer = (-self.movement_keys_speed)*2

        self.level = 1
        self.score = 0
        self.lines = 0

        self.combo = 1 # Combo will increase when you clear lines with several tetrominos in a row

        self.paused = False

        self.highscore = load_score()
        self.played_highscorebeaten_sound = False

        self.levelup_sound  = get_sound("levelup.wav")
        self.gameover_sound = get_sound("gameover.wav")
        self.linescleared_sound = get_sound("linecleared.wav")
        self.highscorebeaten_sound = get_sound("highscorebeaten.wav")

        if self.agent_mode == True:
            #Agent's first move
            self.tetromino_placement = self.agent.make_move()
            self.tetromino_position = (0,self.tetromino_placement[2])
            for rotations in range(self.tetromino_placement[0]):
                self.request_rotation()


    def set_tetrominoes(self):
        """
        Sets information for the current and next tetrominos
        """
        self.current_tetromino = self.next_tetromino
        self.next_tetromino = random.choice(list_of_tetrominoes)
        self.surface_of_next_tetromino = self.construct_surface_of_next_tetromino()
        self.tetromino_position = (0,4) if len(self.current_tetromino.shape) == 2 else (0, 3)
        self.tetromino_rotation = 0
        self.tetromino_block = self.block(self.current_tetromino.color)
        self.shadow_block = self.block(self.current_tetromino.color, shadow=True)


    def hard_drop(self):
        """
        Instantly places tetrominos in the cells below
        """
        amount = 0
        while self.request_movement('down'):
            amount += 1
        self.score += 10*amount

        self.lock_tetromino()


    def update(self, timepassed):
        """
        Main game loop
        """
        try:
            self.needs_redraw = False
    
            if self.agent_mode == True:
                self.hard_drop()
    
            else:
                #Handles player input
                pressed = lambda key: event.type == pygame.KEYDOWN and event.key == key
                unpressed = lambda key: event.type == pygame.KEYUP and event.key == key
    
                events = pygame.event.get()
                #Controls pausing and quitting the game.
                for event in events:
                    if pressed(pygame.K_p):
                        self.surface.fill((0,0,0))
                        self.needs_redraw = True
                        self.paused = not self.paused
                    elif event.type == pygame.QUIT:
                        self.gameover(full_exit=True)
                    elif pressed(pygame.K_ESCAPE):
                        self.gameover()
    
                if self.paused:
                    return self.needs_redraw
    
                for event in events:
                    #Handles player input
                    #Controls movement of the tetromino
                    if pressed(pygame.K_SPACE):
                        self.hard_drop()
                    elif pressed(pygame.K_UP) or pressed(pygame.K_w):
                        self.request_rotation()
                    elif pressed(pygame.K_LEFT) or pressed(pygame.K_a):
                        self.request_movement('left')
                        self.movement_keys['left'] = 1
                    elif pressed(pygame.K_RIGHT) or pressed(pygame.K_d):
                        self.request_movement('right')
                        self.movement_keys['right'] = 1
    
                    elif unpressed(pygame.K_LEFT) or unpressed(pygame.K_a):
                        self.movement_keys['left'] = 0
                        self.movement_keys_timer = (-self.movement_keys_speed)*2
                    elif unpressed(pygame.K_RIGHT) or unpressed(pygame.K_d):
                        self.movement_keys['right'] = 0
                        self.movement_keys_timer = (-self.movement_keys_speed)*2
    
    
    
    
                    self.downwards_speed = self.base_downwards_speed ** (1 + self.level/10.)
    
                    self.downwards_timer += timepassed
                    downwards_speed = self.downwards_speed*0.10 if any([pygame.key.get_pressed()[pygame.K_DOWN],
                                                                            pygame.key.get_pressed()[pygame.K_s]]) else self.downwards_speed
                    if self.downwards_timer > downwards_speed:
                        if not self.request_movement('down'): #Places tetromino if it cannot move further down
                            self.lock_tetromino()
    
                        self.downwards_timer %= downwards_speed
    
    
                    if any(self.movement_keys.values()):
                        self.movement_keys_timer += timepassed
                    if self.movement_keys_timer > self.movement_keys_speed:
                        self.request_movement('right' if self.movement_keys['right'] else 'left')
                        self.movement_keys_timer %= self.movement_keys_speed

        except:
            print("Error in agent running")
            print("Manually causing gameover. Preserves continuation of agent running with minor potential impediment on learning.")
            self.gameover()
            self.needs_redraw = True
        return self.needs_redraw

    def draw_surface(self):
        """
        Draws the image of the current tetromino
        """
        with_tetromino = self.blend(matrix=self.place_shadow())

        for y in range(MATRIX_HEIGHT):
            for x in range(MATRIX_WIDTH):

                #                                       I hide the 2 first rows by drawing them outside of the surface
                block_location = Rect(x*BLOCKSIZE, (y*BLOCKSIZE - 2*BLOCKSIZE), BLOCKSIZE, BLOCKSIZE)
                if with_tetromino[(y,x)] is None:
                    self.surface.fill(BGCOLOR, block_location)
                else:
                    if with_tetromino[(y,x)][0] == 'shadow':
                        self.surface.fill(BGCOLOR, block_location)

                    self.surface.blit(with_tetromino[(y,x)][1], block_location)
                

    def gameover(self, full_exit=False):
        """
        Gameover occurs when a new tetromino does not fit after the old one has died, either
        after a "natural" drop or a hard drop by the player. That is why `self.lock_tetromino`
        is responsible for checking if it's game over.
        """

        write_score(self.score)

        if full_exit:
            if self.agent_mode == True:
                print("Runs completed.")
                self.serialize_agent()
            exit()
        else:
            if self.agent_mode == True:
                self.agent.complete_episode()
                #Manages the starting of a new game
                if self.agent.get_current_episode() < self.agent.get_number_of_episodes():
                    #Resets the board
                    self.matrix = dict()
                    for y in range(MATRIX_HEIGHT):
                        for x in range(MATRIX_WIDTH):
                            self.matrix[(y,x)] = None
                    self.score = 0
                    self.lines = 0
                    self.board = agent.board(self.create_board_representation())
                    self.board.set_board_height()
                    self.board.set_holes()
                    self.board.set_column_differences()
                    self.agent.set_current_board(self.board)
                    print(str(self.board))
                    new_seed = self.agent.load_new_seed()
                    if new_seed == None:
                        try:
                            raise ValueError("Not enough seeds for current experiment!");
                        except:
                            print("\nNot enough seeds for current experiment!\nExiting Matris...")
                            exit()
                    print("Generating new game with seed: " + str(new_seed))
                    random.seed(new_seed)
                    self.set_tetrominoes()
                    self.next_tetromino = random.choice(list_of_tetrominoes)
                    self.agent.set_agent_tetromino(self.current_tetromino)

                    #Agent's first move of the new game
                    self.tetromino_placement = self.agent.make_move()
                    self.tetromino_position = (0,self.tetromino_placement[2])
                    for rotations in range(self.tetromino_placement[0]):
                        self.request_rotation()

                else:
                    print("Runs completed.")
                    self.serialize_agent()
                    exit()
            else:
                raise GameOver("Sucker!")

    def place_shadow(self):
        """
        Draws shadow of tetromino so player can see where it will be placed
        """
        posY, posX = self.tetromino_position
        while self.blend(position=(posY, posX)):
            posY += 1

        position = (posY-1, posX)

        return self.blend(position=position, shadow=True)

    def fits_in_matrix(self, shape, position):
        """
        Checks if tetromino fits on the board
        """
        posY, posX = position
        for x in range(posX, posX+len(shape)):
            for y in range(posY, posY+len(shape)):
                if self.matrix.get((y, x), False) is False and shape[y-posY][x-posX]: # outside matrix
                    return False

        return position


    def request_rotation(self):
        """
        Checks if tetromino can rotate
        Returns the tetromino's rotation position if possible
        """
        rotation = (self.tetromino_rotation + 1) % 4
        shape = self.rotated(rotation)

        y, x = self.tetromino_position

        position = (self.fits_in_matrix(shape, (y, x)) or
                    self.fits_in_matrix(shape, (y, x+1)) or
                    self.fits_in_matrix(shape, (y, x-1)) or
                    self.fits_in_matrix(shape, (y, x+2)) or
                    self.fits_in_matrix(shape, (y, x-2)))
        # ^ That's how wall-kick is implemented

        if position and self.blend(shape, position):
            self.tetromino_rotation = rotation
            self.tetromino_position = position

            self.needs_redraw = True
            return self.tetromino_rotation
        else:
            return False

    def request_movement(self, direction):
        """
        Checks if teteromino can move in the given direction and returns its new position if movement is possible
        """
        posY, posX = self.tetromino_position
        if direction == 'left' and self.blend(position=(posY, posX-1)):
            self.tetromino_position = (posY, posX-1)
            self.needs_redraw = True
            return self.tetromino_position
        elif direction == 'right' and self.blend(position=(posY, posX+1)):
            self.tetromino_position = (posY, posX+1)
            self.needs_redraw = True
            return self.tetromino_position
        elif direction == 'up' and self.blend(position=(posY-1, posX)):
            self.needs_redraw = True
            self.tetromino_position = (posY-1, posX)
            return self.tetromino_position
        elif direction == 'down' and self.blend(position=(posY+1, posX)):
            self.needs_redraw = True
            self.tetromino_position = (posY+1, posX)
            return self.tetromino_position
        else:
            return False

    def rotated(self, rotation=None):
        """
        Rotates tetromino
        """
        if rotation is None:
            rotation = self.tetromino_rotation
        return rotate(self.current_tetromino.shape, rotation)

    def block(self, color, shadow=False):
        """
        Sets visual information for tetromino
        """
        colors = {'blue':   (105, 105, 255),
                  'yellow': (225, 242, 41),
                  'pink':   (242, 41, 195),
                  'green':  (22, 181, 64),
                  'red':    (204, 22, 22),
                  'orange': (245, 144, 12),
                  'cyan':   (10, 255, 226)}


        if shadow:
            end = [90] # end is the alpha value
        else:
            end = [] # Adding this to the end will not change the array, thus no alpha value

        border = Surface((BLOCKSIZE, BLOCKSIZE), pygame.SRCALPHA, 32)
        border.fill(list(map(lambda c: c*0.5, colors[color])) + end)

        borderwidth = 2

        box = Surface((BLOCKSIZE-borderwidth*2, BLOCKSIZE-borderwidth*2), pygame.SRCALPHA, 32)
        boxarr = pygame.PixelArray(box)
        for x in range(len(boxarr)):
            for y in range(len(boxarr)):
                boxarr[x][y] = tuple(list(map(lambda c: min(255, int(c*random.uniform(0.8, 1.2))), colors[color])) + end)

        del boxarr # deleting boxarr or else the box surface will be 'locked' or something like that and won't blit.
        border.blit(box, Rect(borderwidth, borderwidth, 0, 0))


        return border

    def lock_tetromino(self):
        """
        This method is called whenever the falling tetromino "dies". `self.matrix` is updated,
        the lines are counted and cleared, and a new tetromino is chosen.
        """
        self.matrix = self.blend()

        lines_cleared = self.remove_lines()

        if lines_cleared == -1: #Indicates that clearing the lines failed. This is due to the tetromino reaching higher than 2 above the skyline.
            """
            End episode:
                game will be in a terminal state as the skyline was occupied 3 cells high
                however MaTris can only handle the skyline being occupied by 2 cells high.

            This causes the memory to be stored as if it were a terminal state.
            The board is then cleared, and a new episode restarted.
            """
            self.agent.remember_state_action(self.agent.previous_state, self.agent.previous_action, -1000, self.agent.get_current_board(), True)
            self.agent.update_approximater()
            self.agent.reset_approximaters()
            self.gameover()

        else:
            self.lines += lines_cleared

            if lines_cleared:
                self.score += 100 * (lines_cleared**2) * self.combo

                if not self.played_highscorebeaten_sound and self.score > self.highscore:
                    self.played_highscorebeaten_sound = True

            if self.lines >= self.level*10:
                self.level += 1

                self.combo = self.combo + 1 if lines_cleared else 1

        self.set_tetrominoes()

        if not self.blend() and lines_cleared != -1:
            self.gameover()

        self.needs_redraw = True

        if self.agent_mode == True:
            #Collects information from the board.
            self.board.update_board_representation(self.create_board_representation())
            self.board.set_board_height()
            self.board.set_holes()
            self.board.set_column_differences()
            print(str(self.board))
            print("Column Height Differences:" + str(self.board.get_column_differences()))
            if self.agent.holes == True:
                print("Holes: " + str(self.board.get_holes()))
            if self.agent.height == True:
                print("Height: " + str(self.board.get_board_height()))
            print(str(self.tetromino_placement))
            print("\nTetromino:")
            for line in range(0,len(self.agent.agent_tetromino[0])):
                print(str(self.agent.agent_tetromino[0][line]))
            print("Epsilon: " + str(self.agent.epsilon))
            reward = self.agent.update_score_and_lines(self.score, self.lines)
            print("Score: " + str(self.agent.score))
            print("Lines Cleared: " + str(self.agent.lines_cleared))
            print("Current Episode number: " + str(self.agent.current_episode+1) + " / " + str(self.agent.number_of_episodes))
            print("**********************************")


            #Passes tetromino and board information to the agent.
            self.agent.set_agent_tetromino(self.current_tetromino)
            self.agent.set_current_board(self.board)

            #Remembers previous S,A,R,S
            if self.agent.check_game_over() and lines_cleared != -1:  #Ends episode if previous turn was terminal
                #End of episode
                if self.agent.random_moves == False:
                    self.agent.remember_state_action(self.agent.previous_state, self.agent.previous_action, -1000, self.agent.get_current_board(), True)
                    self.agent.update_approximater()
                    self.agent.reset_approximaters()
                self.gameover()
            else:   #Continue episode as not in terminal state
                self.tetromino_placement = self.agent.make_move()

                if self.tetromino_placement == False:
                    #Tetromino placed in state that causes a game over
                    if self.agent.random_moves == False:
                        #Tetromino placed in state that causes a game over
                        self.agent.remember_state_action(self.agent.previous_state, self.agent.previous_action, -1000, self.agent.get_current_board(), True)
                        self.agent.update_approximater()
                        self.agent.reset_approximaters()
                    self.gameover()
                else:
                    #Tetromino placed in a non-terminal state.
                    if self.agent.random_moves == False:
                        self.agent.remember_state_action(self.agent.previous_state, self.agent.previous_action, reward, self.agent.get_current_board(), False)
                        self.agent.update_approximater()
                        self.agent.reset_approximaters()
                    self.tetromino_position = (0,self.tetromino_placement[2])
                    for rotations in range(self.tetromino_placement[0]):
                        self.request_rotation()

    def remove_lines(self):
        """
        Removes lines from the board
        """
        try:
            lines = []
            for y in range(MATRIX_HEIGHT):
                #Checks if row if full, for each row
                line = (y, [])
                for x in range(MATRIX_WIDTH):
                    if self.matrix[(y,x)]:
                        line[1].append(x)
                if len(line[1]) == MATRIX_WIDTH:
                    lines.append(y)

            for line in sorted(lines):
                #Moves lines down one row
                for x in range(MATRIX_WIDTH):
                    self.matrix[(line,x)] = None
                for y in range(0, line+1)[::-1]:
                    for x in range(MATRIX_WIDTH):
                        self.matrix[(y,x)] = self.matrix.get((y-1,x), None)

            return len(lines)
        except:
            print("ERROR REMOVING LINES:\t DEBUG INFORMATION")
            print(self.tetromino_placement)
            print(self.board.board_representation)
            return -1

    def blend(self, shape=None, position=None, matrix=None, shadow=False):
        """
        Does `shape` at `position` fit in `matrix`? If so, return a new copy of `matrix` where all
        the squares of `shape` have been placed in `matrix`. Otherwise, return False.

        This method is often used simply as a test, for example to see if an action by the player is valid.
        It is also used in `self.draw_surface` to paint the falling tetromino and its shadow on the screen.
        """
        if shape is None:
            shape = self.rotated()
        if position is None:
            position = self.tetromino_position

        copy = dict(self.matrix if matrix is None else matrix)
        posY, posX = position
        for x in range(posX, posX+len(shape)):
            for y in range(posY, posY+len(shape)):
                if (copy.get((y, x), False) is False and shape[y-posY][x-posX] # shape is outside the matrix
                    or # coordinate is occupied by something else which isn't a shadow
                    copy.get((y,x)) and shape[y-posY][x-posX] and copy[(y,x)][0] != 'shadow'):

                    return False # Blend failed; `shape` at `position` breaks the matrix

                elif shape[y-posY][x-posX]:
                    copy[(y,x)] = ('shadow', self.shadow_block) if shadow else ('block', self.tetromino_block)

        return copy

    def construct_surface_of_next_tetromino(self):
        """
        Draws the image of the next tetromino
        """
        shape = self.next_tetromino.shape
        surf = Surface((len(shape)*BLOCKSIZE, len(shape)*BLOCKSIZE), pygame.SRCALPHA, 32)

        for y in range(len(shape)):
            for x in range(len(shape)):
                if shape[y][x]:
                    surf.blit(self.block(self.next_tetromino.color), (x*BLOCKSIZE, y*BLOCKSIZE))
        return surf

    def create_board_representation(self):
        lines = []
        for y in range(MATRIX_HEIGHT):
            #Checks if row if full, for each row
            line = (y, [])
            for x in range(MATRIX_WIDTH):
                if self.matrix[(y,x)]:
                    line[1].append(1)
                else:
                    line[1].append(0)
            lines.append(line[1])
        board = []
        for i in range (len(lines)):
            board.append(lines[i])

        return board

    def serialize_agent(self):
        """
        Serializes the agent.
        This saves the epsilon value, whether holes or height was used and the current ANN of the agent.
        """
        agent_information = [self.agent.epsilon, self.agent.holes, self.agent.height, self.agent.current_net]
        handler = open(self.agent.file_path + ".obj", 'wb')
        pickle.dump(agent_information, handler)
        handler.close()

class Game(object):
    def main(self, screen):
        """
        Main loop for game
        Redraws scores and next tetromino each time the loop is passed through
        """
        clock = pygame.time.Clock()
        self.matris = Matris()

        screen.blit(construct_nightmare(screen.get_size()), (0,0))

        matris_border = Surface((MATRIX_WIDTH*BLOCKSIZE+BORDERWIDTH*2, VISIBLE_MATRIX_HEIGHT*BLOCKSIZE+BORDERWIDTH*2))
        matris_border.fill(BORDERCOLOR)
        screen.blit(matris_border, (MATRIS_OFFSET,MATRIS_OFFSET))

        self.redraw()

        while True:
            try:
                timepassed = clock.tick(50)
                if self.matris.update((timepassed / 1000.) if not self.matris.paused else 0):
                    try:
                        self.redraw()
                    except:
                        print("Error when placing agent tetromino. Starting a new game.")
                        for line in range(0,len(self.matris.agent.agent_tetromino[0])):
                            print(str(self.matris.agent.agent_tetromino[0][line]))
                        self.matris.gameover()
            except GameOver:
                return


    def redraw(self):
        """
        Redraws the information panel and next termoino panel
        """
        if not self.matris.paused:
            self.blit_next_tetromino(self.matris.surface_of_next_tetromino)
            self.blit_info()

            self.matris.draw_surface()

        pygame.display.flip()


    def blit_info(self):
        """
        Draws information panel
        """
        textcolor = (255, 255, 255)
        font = pygame.font.Font(None, 30)
        width = (WIDTH-(MATRIS_OFFSET+BLOCKSIZE*MATRIX_WIDTH+BORDERWIDTH*2)) - MATRIS_OFFSET*2

        def renderpair(text, val):
            text = font.render(text, True, textcolor)
            val = font.render(str(val), True, textcolor)

            surf = Surface((width, text.get_rect().height + BORDERWIDTH*2), pygame.SRCALPHA, 32)

            surf.blit(text, text.get_rect(top=BORDERWIDTH+10, left=BORDERWIDTH+10))
            surf.blit(val, val.get_rect(top=BORDERWIDTH+10, right=width-(BORDERWIDTH+10)))
            return surf

        #Resizes side panel to allow for all information to be display there.
        scoresurf = renderpair("Score", self.matris.score)
        levelsurf = renderpair("Level", self.matris.level)
        linessurf = renderpair("Lines", self.matris.lines)
        combosurf = renderpair("Combo", "x{}".format(self.matris.combo))

        height = 20 + (levelsurf.get_rect().height +
                       scoresurf.get_rect().height +
                       linessurf.get_rect().height +
                       combosurf.get_rect().height )

        #Colours side panel
        area = Surface((width, height))
        area.fill(BORDERCOLOR)
        area.fill(BGCOLOR, Rect(BORDERWIDTH, BORDERWIDTH, width-BORDERWIDTH*2, height-BORDERWIDTH*2))

        #Draws side panel
        area.blit(levelsurf, (0,0))
        area.blit(scoresurf, (0, levelsurf.get_rect().height))
        area.blit(linessurf, (0, levelsurf.get_rect().height + scoresurf.get_rect().height))
        area.blit(combosurf, (0, levelsurf.get_rect().height + scoresurf.get_rect().height + linessurf.get_rect().height))

        screen.blit(area, area.get_rect(bottom=HEIGHT-MATRIS_OFFSET, centerx=TRICKY_CENTERX))


    def blit_next_tetromino(self, tetromino_surf):
        """
        Draws the next tetromino in a box to the side of the board
        """
        area = Surface((BLOCKSIZE*5, BLOCKSIZE*5))
        area.fill(BORDERCOLOR)
        area.fill(BGCOLOR, Rect(BORDERWIDTH, BORDERWIDTH, BLOCKSIZE*5-BORDERWIDTH*2, BLOCKSIZE*5-BORDERWIDTH*2))

        areasize = area.get_size()[0]
        tetromino_surf_size = tetromino_surf.get_size()[0]
        # ^^ I'm assuming width and height are the same

        center = areasize/2 - tetromino_surf_size/2
        area.blit(tetromino_surf, (center, center))

        screen.blit(area, area.get_rect(top=MATRIS_OFFSET, centerx=TRICKY_CENTERX))

class Menu(object):
    """
    Creates main menu
    """
    running = True
    def main(self, screen):
        clock = pygame.time.Clock()
        menu = kezmenu.KezMenu(
            ['Play!', lambda: Game().main(screen)],
            ['Quit', lambda: setattr(self, 'running', False)],
        )
        menu.position = (50, 50)
        menu.enableEffect('enlarge-font-on-focus', font=None, size=60, enlarge_factor=1.2, enlarge_time=0.3)
        menu.color = (255,255,255)
        menu.focus_color = (40, 200, 40)

        nightmare = construct_nightmare(screen.get_size())
        highscoresurf = self.construct_highscoresurf() #Loads highscore onto menu

        timepassed = clock.tick(30) / 1000.

        Game().main(screen)

        
        while self.running:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    exit()

            menu.update(events, timepassed)

            timepassed = clock.tick(30) / 1000.

            if timepassed > 1: # A game has most likely been played
                highscoresurf = self.construct_highscoresurf()

            screen.blit(nightmare, (0,0))
            screen.blit(highscoresurf, highscoresurf.get_rect(right=WIDTH-50, bottom=HEIGHT-50))
            menu.draw(screen)
            pygame.display.flip()
        


    def construct_highscoresurf(self):
        """
        Loads high score from file
        """
        font = pygame.font.Font(None, 50)
        highscore = load_score()
        text = "Highscore: {}".format(highscore)
        return font.render(text, True, (255,255,255))

def construct_nightmare(size):
    """
    Constructs background image
    """
    surf = Surface(size)

    boxsize = 8
    bordersize = 1
    vals = '1235' # only the lower values, for darker colors and greater fear
    arr = pygame.PixelArray(surf)
    for x in range(0, len(arr), boxsize):
        for y in range(0, len(arr[x]), boxsize):

            color = int(''.join([random.choice(vals) + random.choice(vals) for _ in range(3)]), 16)

            for LX in range(x, x+(boxsize - bordersize)):
                for LY in range(y, y+(boxsize - bordersize)):
                    if LX < len(arr) and LY < len(arr[x]):
                        arr[LX][LY] = color
    del arr
    return surf


if __name__ == '__main__':
    pygame.init()

    screen = screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MaTris")
    Menu().main(screen)
