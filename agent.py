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
    
    def __init__(self, boardRepresentation=[]):
        self.boardRepresentation = boardRepresentation
        
    
    def update_board_representation(self, boardRepresentation):
        self.boardRepresentation = boardRepresentation