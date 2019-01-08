"""
Module used to create a Tetris playing agent
Created by JRIngram 
"""
class board():
    """
    Representation of the board as an array of numbers.
    0 = empty.
    1 = full.
    """
    
    boardRepresentation = []
    board_height = 0
    cum_height = 0
    holes_per_column = []
    
    def __init__(self, boardRepresentation=[]):
        self.boardRepresentation = boardRepresentation
        
    
    def update_board_representation(self, boardRepresentation):
        self.boardRepresentation = boardRepresentation
    
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
    
    def get_board_height(self):
        return self.board_height
    
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
    
    
    
    
    
    
    
    
    
    