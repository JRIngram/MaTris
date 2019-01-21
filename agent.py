"""
Module used to create a Tetris playing agent
Created by JRIngram 
"""
import copy

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
    
    def __init__(self, boardRepresentation=[]):
        self.boardRepresentation = boardRepresentation
        
    
    def update_board_representation(self, boardRepresentation):
        self.boardRepresentation = boardRepresentation
        
    def get_board_representation(self):
        return self.boardRepresentation
    
    def __str__(self):
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
        return self.board_height
    
    def get_cum_height(self):
        return self.cum_height
    
    def set_holes(self):
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
    
class agent():
    
    agent_tetromino = []
    current_board = None
    
    def __init__(self, tetromino=[]):
        self.agent_tetromino = tetromino
    
    def set_agent_tetromino(self, tetromino):
        self.agent_tetromino = []
        tetromino_array = []
        for x in range(len(tetromino[2])):
            tetromino_row = []
            for y in range(len(tetromino[2][x])):
                if tetromino[2][x][y] == 'X':
                    tetromino_row.append(1)
                else:
                    tetromino_row.append(0)
            tetromino_array.append(tetromino_row)
        self.agent_tetromino.append(tetromino_array)
        for x in range (0,3):
            self.agent_tetromino.append(self.rotate_agent_tetromino(self.agent_tetromino[x]))
    
    def get_agent_tetromino(self, tetromino):
        return self.agent_tetromino
    
    def rotate_agent_tetromino(self, tetromino):
        rotating_tetromino = tetromino
        rotated_tetromino = []
        for x in range(len(rotating_tetromino)):
            column = []
            for y in range(len(rotating_tetromino)):
                column.append(rotating_tetromino[y][x])
            rotated_tetromino.append(list(reversed(column)))
        return rotated_tetromino
    
    def set_current_board(self, board):
        self.current_board = board  
        
    def find_valid_placements(self):
        valid_placements = []
        #Hard coded as only 4 possible rotations
        valid_placements.append(self.find_valid_placements_for_rotation(0))
        valid_placements.append(self.find_valid_placements_for_rotation(1))
        valid_placements.append(self.find_valid_placements_for_rotation(2))
        valid_placements.append(self.find_valid_placements_for_rotation(3))
        
        
    def find_valid_placements_for_rotation(self, rotation):
        column_heights = self.current_board.column_heights
        tetromino = self.agent_tetromino
        tetromino_width_stats = self.calculate_tetromino_width(rotation)
        tetromino_height_stats = self.calculate_tetromino_height(rotation)
        #Need to trim None values and find empty column get a more realistic shape of the tetromino
        tetromino_width = len(tetromino_width_stats)
        tetromino_height = len(tetromino_width_stats) -1
        '''
        for x in range(len(tetromino_width_stats)):
            if tetromino_width_stats[x] == 1 or tetromino_width_stats[x] == None:
                tetromino_width = tetromino_width + 1
        for x in range(len(tetromino_height_stats)):
            if tetromino_height_stats[x] == 1 or tetromino_height_stats[x] == None:
                tetromino_height = tetromino_height + 1
        tetromino_width = tetromino_width + 1
        '''
                
        #Calculate rows below full cell
        
        #Check column height and for each column
        valid_placements = []
        for column in range(len(column_heights)-(tetromino_width-1)):
            test_board = copy.deepcopy(self.current_board)
            placeable_height = 21 - column_heights[column]
            for tet_height in range(tetromino_height+1): #for each row in the tetromino
                for tet_width in range(tetromino_width): #for each column in tetromino
                                                    #moves up the placeable row   #the x-axis to place the tetromino
                    test_board.boardRepresentation[placeable_height - tet_height][column+tet_width] = test_board.boardRepresentation[placeable_height - tet_height][column+tet_width] + self.agent_tetromino[rotation][tetromino_height - tet_height][tet_width]
            
            can_place = True
            for check_row in range(len(test_board.boardRepresentation)):
                for check_column in range(len(test_board.boardRepresentation[check_row])):
                    if test_board.boardRepresentation[check_row][check_column] != 1 and test_board.boardRepresentation[check_row][check_column] != 0:
                        can_place = False
                        break
                if can_place == False:
                    break
            if can_place == True:
                    coordinate_tag = []
                    coordinate_tag.append(rotation)
                    coordinate_tag.append(column)
                    coordinate_tag.append(placeable_height)
                    placeable_position = []
                    placeable_position.append(coordinate_tag)
                    placeable_position.append(test_board)
                    valid_placements.append(placeable_position)
        return valid_placements
        
    def calculate_tetromino_width(self,rotation):
        potential_width = len(self.agent_tetromino[rotation][0]) #number of columns
        full_columns = [None]*potential_width
        for x in range(len(self.agent_tetromino[rotation])): #for each row
            for y in range(len(self.agent_tetromino[rotation][0])):
                if self.agent_tetromino[rotation][x][y] == 1:
                    full_columns[y] = 1
            #TODO Add break once full_columns is full?
        return full_columns
            
    def calculate_tetromino_height(self, rotation):
        potential_height = len(self.agent_tetromino[rotation])
        full_rows = [None]*potential_height
        for x in range(len(self.agent_tetromino[rotation])):
            for y in range(len(self.agent_tetromino[rotation][0])):
               if self.agent_tetromino[rotation][y][x] == 1:
                   full_rows[y] = 1
             #TODO Add break once full_rows is full?
        return full_rows
            
    
    