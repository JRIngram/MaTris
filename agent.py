"""
Module used to create a Tetris playing agent
Created by JRIngram 
"""
import copy, time, random, csv
from tetrominoes import list_of_tetrominoes

import keras
from keras.models import Sequential
from keras.layers import Dense
import tensorflow as tf
import numpy as np

class board():
    """
    Representation of the board as an array of numbers.
    0 = empty.
    1 = full.
    """
    boardRepresentation = []
    board_height = 0
    cum_height = 0 #Cumulative height of the board
    column_heights = 0
    holes_per_column = []
    column_differences = []
    
    def __init__(self, boardRepresentation=[]):
        self.boardRepresentation = boardRepresentation
        
    def update_board_representation(self, boardRepresentation):
        """
        Creates an update board representation
        """
        self.boardRepresentation = boardRepresentation

    def get_board_representation(self):    
        """
        Returns the current board representation
        """
        return self.boardRepresentation

    def __str__(self):
        """
        Returns the board as a series of rows, each corresponding to a row in the board.
        """
        #Note: board will be 22 in height as Matris uses the top two columns as the initial appearance of tetrominos on the board
        boardString = ""
        for row in self.boardRepresentation:
            for x in range(len(row)):
                if(x == len(row) - 1):
                    boardString = boardString + str(row[x]) + "\n"
                else:
                    boardString = boardString + str(row[x]) + ","
        return boardString

    def set_board_height(self):
        """
        Calculates the highest column height in the board.
        Also assigns cumulative height value: column1(height) + column2(height) + ... + columnN(height)
        """
        column_heights = [];
        for x in range(len(self.boardRepresentation[0])): #Number of columns
            for y in range (len(self.boardRepresentation)): #Number of rows
                if(self.boardRepresentation[y][x] == 1):
                    column_heights.append(22 - y) #Matris height is 22
                    break
                elif(y == 21): #Column is empty
                    column_heights.append(0)
        self.board_height = max(column_heights)
        self.cum_height = sum(column_heights)
        self.column_heights = column_heights
    
    def get_board_height(self):
        """
        Returns the board height.
        """
        return self.board_height

    def get_cum_height(self):   
        """
        Returns cumulative height of the the board
        """
        return self.cum_height
    
    def set_holes(self):
        """
        Calculates the number of holes in each column.
        A hole is a cell that is below a full cell in a column:
            e.g. if cell was full at height 3, and all cells below that were empty, there would be 2 holes.  
        """
        holes_per_column = []
        for x in range(len(self.boardRepresentation[0])): #Number of columns
            holes_in_column = 0
            below_full_cell = False
            for y in range (len(self.boardRepresentation)): #Number of rows
                if(self.boardRepresentation[y][x] == 1 and below_full_cell == False):
                    below_full_cell = True
                if(below_full_cell == True and self.boardRepresentation[y][x] == 0):
                    holes_in_column = holes_in_column + 1
            holes_per_column.append(holes_in_column)
        self.holes_per_column = holes_per_column
    
    def get_holes(self):
        return sum(self.holes_per_column)
    
    def skyline_occuppied(self):
        """
        Checks if the top two rows of the board representation is occupied, which signals that the skyline is occupied.
        Returns true if occupied;false if unoccupied. 
        """
        for x in range (len(self.boardRepresentation[0])): #[0] and [1] will always be the same length
            if self.boardRepresentation[0][x] or self.boardRepresentation[1][x] == 1:
                return True
        return False
    
    def set_column_differences(self):
        """
        Calculates the difference in height between a column and the column to the left of it.
        This is calculate for all columns and then returned as a list.
        """
        column_heights = [];
        for x in range(len(self.boardRepresentation[0])): #Number of columns
            for y in range (len(self.boardRepresentation)): #Number of rows
                if(self.boardRepresentation[y][x] == 1):
                    column_heights.append(22 - y) #Matris height is 22
                    break
                elif(y == 21): #Column is empty
                    column_heights.append(0)
        column_differences = [0] * len(column_heights)
        for x in range(len(column_heights)):
            if x == 0:
                column_differences[x] = 0
            else:
                column_differences[x] = column_heights[x-1] - column_heights[x]
        self.column_differences = column_differences
    
class agent():
    """
    Agent that will learn to play Tetris.
    Stores the current tetromino and a representation of the board.
    """
    agent_tetromino = []
    current_board = None
    number_of_episodes = 1
    current_episode=0
    lines_cleared = 0
    score = 0
    
    #Determines how moves are made
    random_moves = True
    rand = None
    
    #Variables used in DQN
    epsilon=0
    epsilon_decay=0
    discount = 0
    event_memory = []
    memory_size = 0
    sample_size = 0
    reset_steps = 0 
    random_moves = True
    event_memory = None
    
    #Used for state action recording
    previous_state = None
    previous_action = None
    
    def __init__(self, tetromino=[], episodes=1, random_moves=True, epsilon=0.1, discount=0.99,  epsilon_decay=0, memory_size=1000, sample_size=50, reset_steps=1000):
        self.agent_tetromino = tetromino
        self.number_of_episodes = episodes
        self.rand = random.Random(self.load_new_seed())
        self.random_moves = random_moves
        
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.discount = discount
        self.event_memory = []
        self.memory_size = memory_size
        self.event_memory = []
        self.sample_size = sample_size
        self.reset_steps = reset_steps 
                
        #Initialize action-value function Q with random weights
        self.current_net = Sequential()
        #26 inputs, one for each possible tetromino cell (4 * 4) and one for each column height difference
        self.current_net.add(Dense(3, input_dim=26, activation='tanh'))
        #40 outputs, one for each possible action: 10 columns * 4 rotations.
        self.current_net.add(Dense(40, activation='linear'))
        self.current_net.compile(loss='mean_squared_error',
              optimizer='adam',
              metrics=['accuracy'])
        
        #Initialize target action-value function Q
        self.target_net = copy.deepcopy(self.current_net)
    
    def set_agent_tetromino(self, tetromino):
        """
        Stores the current tetromino and all rotations of that tetromino. 
        Each tetromino is stored 4 times as the tetromino can rotate 4 times.
        Tetromino is stored as 0 for an empty cell in the matrix or 1 for a full cell in the matrix.
        E.g. an "L" tetromino is stored as
            [[0,1,0]
             [0,1,0]
             [0,1,1]]
        """
        self.agent_tetromino = []
        self.agent_tetromino.append(self.convert_tetromino(tetromino))
        for x in range (0,3):
            self.agent_tetromino.append(self.rotate_agent_tetromino(self.agent_tetromino[x]))
    
    def convert_tetromino(self, tetromino):
        """
        Converts a tetromino from the O,X representation in tetrominos.py to the 0 and 1 representation used by the agent.
        """
        tetromino_array = []
        for x in range(len(tetromino[2])):
            tetromino_row = []
            for y in range(len(tetromino[2][x])):
                if tetromino[2][x][y] == 'X':
                    tetromino_row.append(1)
                else:
                    tetromino_row.append(0)
            tetromino_array.append(tetromino_row)
        return tetromino_array
    
    def get_agent_tetromino(self):
        """
        Returns the agent's tetromino
        """
        return self.agent_tetromino
    
    def rotate_agent_tetromino(self, tetromino):
        """
        Returns a rotation of the agent's current tetromino.
        Used to calculate all rotations for that tetromino in set_agent_tetromino
        """
        rotating_tetromino = tetromino
        rotated_tetromino = []
        for x in range(len(rotating_tetromino)):
            column = []
            for y in range(len(rotating_tetromino)):
                column.append(rotating_tetromino[y][x])
            rotated_tetromino.append(list(reversed(column)))
        return rotated_tetromino
    
    def set_current_board(self, board):
        """
        Sets the current board representation for the 
        """
        self.current_board = board  
    
    def get_current_board(self):
        return self.current_board
    
    def make_move(self):
        game_over = self.check_game_over()
        if game_over == False:
            if self.random_moves == True:
                placement = self.choose_random_tetromino_placement()
                return placement
            else:
                placement = self.dqn_move()
                return placement
        else:
            return False
    
    def check_game_over(self):
        if self.current_board.skyline_occuppied() == True:
            print("Game Over: Skyline occupied")
            return True
        possible_placements = self.find_valid_placements()
        rotations_with_remaining_placements = []
        for x in range(4):
            if len(possible_placements[x]) > 0:
                rotations_with_remaining_placements.append(x)
        if len(rotations_with_remaining_placements) == 0:
            print("Game Over: No rotations with remaining placements.")
            return True
        
        return False
        
    def choose_random_tetromino_placement(self):
        """
        Chooses a random valid placement on the Tetris board to place a tetromino
        Returns false if agent declares a GameOver scenario
        """
        t = time.time()
        possible_placements = self.find_valid_placements()
        #Check which rotations still have valid placements
        rotations_with_remaining_placements = []
        for x in range(4):
            if len(possible_placements[x]) > 0:
                rotations_with_remaining_placements.append(x)
                print("Valid placements: " + str(x) + ":" + str(len(possible_placements[x])))
        rotation = rotations_with_remaining_placements[random.randint(0, len(rotations_with_remaining_placements) - 1)]         
        number_of_placements = len(possible_placements[rotation])-1
        if number_of_placements < 0:
            print("Game Over: Rotation with no remaining placements chosen.")
            elapsed = time.time() - t
            print("Time Taken:" + str(elapsed))
            return False
        placement_option = random.randint(0,number_of_placements)
        #rotation,height,column
        placement = [rotation,possible_placements[rotation][placement_option][0][2],possible_placements[rotation][placement_option][0][1]]
        
        #Checks if top two columns are filled by the chosen placement
        self.chosen_board_representation = []
        for option in range(len(possible_placements[placement[0]])):
            if possible_placements[placement[0]][option][0][1] == placement[2]:
                self.chosen_board_representation = possible_placements[placement[0]][option][1].boardRepresentation
                break
                
        if 1 in self.chosen_board_representation[0] or 1 in self.chosen_board_representation[0]:
            print("Game Over: Option chosen where skyline occupied")
            elapsed = time.time() - t
            print("Time Taken:" + str(elapsed))
            return False
        elapsed = time.time() - t
        #Check if top two rows filled
        print("Time Taken:" + str(elapsed))
        placement[2] = placement[2] - possible_placements[rotation][placement_option][0][3] #Corrects column placement after trimming
        return placement
        
    def dqn_move(self):
        choose_optimal = self.rand.random()
        tetromino_input = [[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]]
        for tetromino_height in range(0, len(self.agent_tetromino[0])):
            #Fills the tetromino_input; used as part of the ANN input
            for tetromino_width in range (0, len(self.agent_tetromino[0][tetromino_height])):
                tetromino_input[tetromino_height][tetromino_width] = self.agent_tetromino[0][tetromino_height][tetromino_width]
        if choose_optimal > self.epsilon:
            possible_actions = self.find_valid_placements()     
            state = np.array([[#Tetromino being used
                                      tetromino_input[0][0],tetromino_input[0][1],tetromino_input[0][2],tetromino_input[0][3],
                                      tetromino_input[1][0],tetromino_input[1][1],tetromino_input[1][2],tetromino_input[1][3],
                                      tetromino_input[2][0],tetromino_input[2][1],tetromino_input[2][2],tetromino_input[2][3],
                                      tetromino_input[3][0],tetromino_input[3][1],tetromino_input[3][2],tetromino_input[3][3],
                                      #Current state of the board (differences in column height
                                      self.current_board.column_differences[0],self.current_board.column_differences[1],
                                      self.current_board.column_differences[2],self.current_board.column_differences[3],
                                      self.current_board.column_differences[4],self.current_board.column_differences[5],
                                      self.current_board.column_differences[6],self.current_board.column_differences[7],
                                      self.current_board.column_differences[8],self.current_board.column_differences[9],                      
                            ]])
            predicted_values = self.query(state)
            optimal_placement = None
                        #rotation                #height                    #column - left trimmed
            #placement = [optimal_placement[0][0], optimal_placement[0][2], optimal_placement[0][1] - - optimal_placement[0][3]]
            #Choose optimal move
            for rotation in range(0,len(possible_actions)): 
                for option in range(0,len(possible_actions[rotation])):
                    #For each option for each rotation check the value
                    #ISSUE ACCESSING DUE TO CHANGE IN ANN TOPOLOGY
                    output_node = (rotation*10) + option #output node to retrieve the predicted value from.
                    node_value = predicted_values[0][output_node]
                    if optimal_placement == None:
                        optimal_placement = [possible_actions[rotation][option][0], node_value]
                    elif node_value > optimal_placement[1]:
                        optimal_placement = [possible_actions[rotation][option][0], node_value]
            #rotation,height,column (corrected by trim)
            placement = [optimal_placement[0][0], optimal_placement[0][2], optimal_placement[0][1] - optimal_placement[0][3]]
                        
        else:
            placement = self.choose_random_tetromino_placement()
        
        previous_column_diffs = copy.deepcopy(self.current_board.column_differences)
        self.previous_state = [#Tetromino being used
                                tetromino_input[0][0],tetromino_input[0][1],tetromino_input[0][2],tetromino_input[0][3],
                                tetromino_input[1][0],tetromino_input[1][1],tetromino_input[1][2],tetromino_input[1][3],
                                tetromino_input[2][0],tetromino_input[2][1],tetromino_input[2][2],tetromino_input[2][3],
                                tetromino_input[3][0],tetromino_input[3][1],tetromino_input[3][2],tetromino_input[3][3],
                                #Current state of the board (differences in column height) being stored to record S,A,R,S
                                previous_column_diffs[0],previous_column_diffs[1],
                                previous_column_diffs[2],previous_column_diffs[3],
                                previous_column_diffs[4],previous_column_diffs[5],
                                previous_column_diffs[6],previous_column_diffs[7],
                                previous_column_diffs[8],previous_column_diffs[9]]
        self.previous_action = copy.deepcopy(placement)
        return placement
    
    def query(self, state, current_net=True):
        """
        Returns a predicted value for a state-action pair.
        If current_net is true then the current_net is used for this prediction.
        If current_net is false then the target_net is used for this prediction.
        """
        if(current_net == True):
            value_prediction = self.current_net.predict(state, batch_size=1)
        else:
            value_prediction = self.target_net.predict(state, batch_size=1)
        return value_prediction
    
    def find_valid_placements(self, agent_tetromino=None, board_representation=None):
        """
        Searches the board for valid placements
        Searches the top of each column on the board for valid placement.
        """
        if(agent_tetromino==None):
            agent_tetromino = self.agent_tetromino
        if(board_representation==None):
            board_representation = self.current_board
            
        valid_placements = []
        #Hard coded as only 4 possible rotations
        valid_placements.append(self.find_valid_placements_for_rotation(agent_tetromino, 0, board_representation))
        valid_placements.append(self.find_valid_placements_for_rotation(agent_tetromino, 1, board_representation))
        valid_placements.append(self.find_valid_placements_for_rotation(agent_tetromino, 2, board_representation))
        valid_placements.append(self.find_valid_placements_for_rotation(agent_tetromino, 3, board_representation))
        return valid_placements
        
        
    def find_valid_placements_for_rotation(self, agent_tetromino, rotation, board):
        """
        Searches the board for valid placements for a rotation of a tetromino
        This is performed 4 times. Once for each tetromino.
        """
        
        column_heights = board.column_heights
        tetromino, left_trimmed = self.trim_tetromino(agent_tetromino,rotation)
        #Used for debugging
        tetromino_width_stats = self.calculate_tetromino_width(agent_tetromino, rotation)
        tetromino_height_stats = self.calculate_tetromino_height(agent_tetromino, rotation)
        #Need to trim None values and find empty column get a more realistic shape of the tetromino
        tetromino_width = len(tetromino[0])
        tetromino_height = len(tetromino) - 1 
                
        #Calculate rows below full cell
        
        #Check column height and for each column
        valid_placements = []
        for column in range(len(column_heights)-(tetromino_width-1)): #For each column
            test_board = copy.deepcopy(board) #Create copy of board
            placeable_height = 21 - column_heights[column] #For the current column, what height can the tetromino be placed at
            for tet_height in range(tetromino_height + 1): #for each row in the tetromino
                for tet_width in range(tetromino_width): #for each column in tetromino
                                                    #moves up the placeable row   #the x-axis to place the tetromino
                                                      
                    test_board.boardRepresentation[placeable_height - tet_height][column+tet_width] = test_board.boardRepresentation[placeable_height - tet_height][column+tet_width] + tetromino[tetromino_height - tet_height][tet_width]
            
            #Checks if the current position being tested allows for valid placement
            can_place = True
            for check_row in range(len(test_board.boardRepresentation)):
                for check_column in range(len(test_board.boardRepresentation[check_row])):
                    if test_board.boardRepresentation[check_row][check_column] != 1 and test_board.boardRepresentation[check_row][check_column] != 0:
                        can_place = False
                        break
                if can_place == False:
                    break
            #Creates a list with data relating to placement
            if can_place == True:
                    coordinate_tag = []
                    coordinate_tag.append(rotation)
                    coordinate_tag.append(column)
                    coordinate_tag.append(placeable_height)
                    coordinate_tag.append(left_trimmed)
                    placeable_position = []
                    placeable_position.append(coordinate_tag)
                    placeable_position.append(test_board)
                    valid_placements.append(placeable_position)
        return valid_placements
        
    def calculate_tetromino_width(self, agent_tetromino, rotation):
        """
        Calculates the width of the current tetromino.
        Finds out how many cells on the X axis are actually filled.
        """
        potential_width = len(agent_tetromino[rotation][0]) #number of columns
        full_columns = [None]*potential_width
        for x in range(len(agent_tetromino[rotation])): #for each row
            for y in range(len(agent_tetromino[rotation][0])):
                if agent_tetromino[rotation][x][y] == 1:
                    full_columns[y] = 1
            #TODO Add break once full_columns is full?
        return full_columns
            
    def calculate_tetromino_height(self, agent_tetromino, rotation):
        """
        Calculates the width of the current tetromino.
        Finds out how many cells on the Y axis are actually filled.
        """
        potential_height = len(agent_tetromino[rotation])
        full_rows = [None]*potential_height
        for x in range(len(agent_tetromino[rotation])):
            for y in range(len(agent_tetromino[rotation][0])):
                if agent_tetromino[rotation][y][x] == 1:
                    full_rows[y] = 1
            #TODO Add break once full_rows is full?
        return full_rows
    
    def get_current_episode(self):
        """
        Returns the current episode of the agent
        """
        return self.current_episode
    
    def get_number_of_episodes(self):
        """
        Returns the total number of episodes that will be ran
        """
        return self.number_of_episodes
    
    def complete_episode(self):
        """
        Writes the results of the current episode and increases the current episode by 1
        """
        self.write_results_to_csv()
        self.current_episode = self.current_episode + 1
        self.score = 0
        
    def set_lines_cleared(self, lines_cleared):
        """
        Changes the value of lines_cleared, 
        the total number of lines the agent has cleared this episode
        """
        self.lines_cleared = lines_cleared
    
    def write_results_to_csv(self):
        """
        Called at the end of an episode, this appends the episode number and 
        number of lines cleared to the file results.csv
        """
        episode_results = [str(self.current_episode),str(self.lines_cleared)]
        with open('results.csv', 'a') as results:
            writer = csv.writer(results)
            writer.writerow(episode_results)
            results.close()
    
    def load_new_seed(self):
        """
        Loads the seed for the corresponding episode
        Takes the seed from seeds.csv which may be generated by the generate_seeds module
        """
        with open('seeds.csv', 'r') as seed_csv:
            seed_reader = csv.reader(seed_csv, delimiter=',', quotechar='|')
            for seed in seed_reader:
                if int(seed[0]) == self.current_episode:
                    return seed[1]
    
    def trim_tetromino(self,tetromino, rotation):
        """
        Removes empty rows and columns from a tetromino with a specific rotation
        Returns both the number of left columns trimmed and the trimmed tetromino
        The number of left columns trimmed is used in additional calculations as to where the tetromino should be placed.
        """
        trimmed_tetromino = copy.deepcopy(tetromino[rotation])
        tetromino_matrix_height = len(trimmed_tetromino)
        tetromino_matrix_width = len(trimmed_tetromino[0])

        trimming_left = True
        trimming_right = False
        left_columns_trimmed = 0
        right_columns_trimmed = 0
        columns_trimmed = 0
        loop_without_trim = False
        
        #Trim empty columns
        while loop_without_trim == False:
            """
            Loops through rows within columns and lists cell values within each column.
            If a column is "empty" i.e. full of 0s then the cell is removed and the loop process is restarted.
            This continues until the tetromino is looped through without trimming
            """
            loop_without_trim = True
            for x in range(len(trimmed_tetromino[0])):
    
                column = []
                for y in range(tetromino_matrix_height):
                    column.append(trimmed_tetromino[y][x])
                if 1 not in column:
                    loop_without_trim = False
                    columns_trimmed = columns_trimmed + 1
                    if trimming_left == True:
                        left_columns_trimmed = left_columns_trimmed + 1
                    else:
                        right_columns_trimmed = right_columns_trimmed + 1
                    for y in range(tetromino_matrix_height):
                        trimmed_tetromino[y].pop(x)
                    break
                if 1 in column and trimming_left == True and trimming_right == False:
                    trimming_left = False
                    trimming_right = False
        
        #Trim empty rows
        loop_without_trim = False
        while loop_without_trim == False:
                """
                Loops through cells within row and lists cell values within each row.
                If a row is "empty" i.e. full of 0s then the cell is removed and the loop process is restarted.
                This continues until the tetromino is looped through without trimming
                """
                loop_without_trim = True
                for x in range(len(trimmed_tetromino)):
                    row = []
                    for y in range(len(trimmed_tetromino[0])):
                        row.append(trimmed_tetromino[x][y])
                    if 1 not in row:
                        loop_without_trim = False 
                        trimmed_tetromino.pop(x)
                        break
        
        return trimmed_tetromino, left_columns_trimmed
    
    def update_score(self, score):
        """
        Updates the Agent's score and returns the reward from the current update.
        """
        reward = score - self.score
        self.score = score
        return reward
    
    def remember_state_action(self,previous_state, previous_action, reward, new_board, terminal_state):
        self.event_memory.append([previous_state, previous_action, reward, copy.deepcopy(new_board), terminal_state])
        if len(self.event_memory) > self.memory_size:
            self.event_memory.pop(0)
    
    def update_approximater(self):
        """
        Replays N memories.
        Updates the current_net based on a target which is:
            reward from the state (if terminal state)
            Max predicted reward from next state (if non-terminal state)
        Gradient descent is then performed on the current_net
        """
        if len(self.event_memory) < self.sample_size:
            memory_samples = random.sample(self.event_memory, len(self.event_memory))
        else:
            memory_samples = random.sample(self.event_memory, self.sample_size)
            
        for memory in memory_samples:
            previous_state = memory[0]
            action = memory[1]
            reward = memory[2]
            next_state = memory[3]
        return False
        
    