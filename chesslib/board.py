from itertools import groupby
from copy import deepcopy

import pieces
import re

class ChessError(Exception): pass
class InvalidCoord(ChessError): pass
class InvalidColor(ChessError): pass
class InvalidMove(ChessError): pass
class Check(ChessError): pass
class CheckMate(ChessError): pass
class Draw(ChessError): pass
class NotYourTurn(ChessError): pass

FEN_STARTING = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
RANK_REGEX = re.compile(r"^[A-Z][1-8]$")

class Board(dict):
    '''
       Board

       A simple chessboard class

       TODO:

        * PGN export
        * En passant
        * Castling
        * Promoting pawns
        * Fifty-move rule
    '''

    axis_y = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    axis_x = tuple(range(1,9)) # (1,2,3,...8)

    captured_pieces = { 'white': [], 'black': [] }
    player_turn = None
    castling = '-'
    en_passant = '-'
    halfmove_clock = 0
    fullmove_number = 1
    history = []

    def __init__(self, fen = None):
        if fen is None: self.load(FEN_STARTING)
        else: self.load(fen)

    def __getitem__(self, coord):
        if isinstance(coord, str):
            coord = coord.upper()
            if not re.match(RANK_REGEX, coord.upper()): raise KeyError
        elif isinstance(coord, tuple):
            coord = self.letter_notation(coord)
        try:
            return super(Board, self).__getitem__(coord)
        except KeyError:
            return None

    def save_to_file(self): pass

    def is_in_check_after_move(self, p1, p2):
        # Create a temporary board
        tmp = deepcopy(self)
        tmp._do_move(p1,p2)
        return tmp.is_in_check(self[p1].color)


    def computer_move(self,color):

        if(color not in ("black", "white")): raise InvalidColor

        [action,value] = self.alphaBeta(-1000000,+1000000,3,color)
        p1 = action[0]          #initial position
        p2 = action[1]          #final position
        self.move(p1,p2)    


    def evaluate(self,color):
        val = 0
        antival = 0
        mobility = 0

        enemy = self.get_enemy(color)
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color: 
                val += self[coord].weight
            if (self[coord] is not None) and self[coord].color == enemy: 
                antival += self[coord].weight    
                #mobility += len(self.all_possible_moves(color))

        return val-antival  

    def alphaBeta(self,alpha,beta,depthleft,color):
        if (depthleft == 0):
            return [[], self.evaluate(color)]

        enemy = self.get_enemy(color)

        actions = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].possible_moves(coord)
                for move in moves:
                    actions.append([coord,move])

        bestAction = []
        bestscore = -1000000
        for action in actions:
            temp =  deepcopy(self)
            p1 = action[0]
            p2 = action[1]
            temp._do_move(p1,p2)
            #self._do_move(p1,p2)
            tt = temp.alphaBetaMin(-beta,-alpha,depthleft - 1,enemy)
            #tt = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            score = tt[1]
            #[[],score] = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            #self._undo_move(p1,p2)

            if score >= beta:                      #fail-hard beta-cutoff
                return [action,score]

            if score > bestscore:                      #alpha acts like max in minimax
                bestscore = score
                bestAction = action

            if score > alpha:
                alpha = score                 
                    
        return[bestAction,bestscore]    



    def alphaBetaMax(self,alpha,beta,depthleft,color):
        if depthleft == 0:
            return [[], self.evaluate(color)]

        enemy = self.get_enemy(color)
    

        actions = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].possible_moves(coord)
                for move in moves:
                    actions.append([coord,move])

        bestAction = []
        for action in actions:
            temp =  deepcopy(self)
            p1 = action[0]
            p2 = action[1]
            temp._do_move(p1,p2)
            #self._do_move(p1,p2)
            tt = temp.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            #tt = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            score = tt[1]
            #[[],score] = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            #self._undo_move(p1,p2)

            if score >= beta:                      #fail-hard beta-cutoff
                return [action,beta]

            if score > alpha:                      #alpha acts like max in minimax
                alpha = score
                bestAction = action             
                    
        return[bestAction,alpha]  

    def alphaBetaMin(self,alpha,beta,depthleft,color):
        if depthleft == 0:
            return [[], -self.evaluate(color)]

        enemy = self.get_enemy(color)
    
        actions = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].possible_moves(coord)
                for move in moves:
                    actions.append([coord,move])

        bestAction = []
        for action in actions:
            temp =  deepcopy(self)
            p1 = action[0]
            p2 = action[1]
            temp._do_move(p1,p2)
            #self._do_move(p1,p2)
            tt = temp.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            #tt = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)

            score = tt[1]
            #[[],score] = self.alphaBetaMin(alpha,beta,depthleft - 1,enemy)
            #self._undo_move(p1,p2)
            if score <= alpha:                   #fail-hard alpha cutoff
                return [action,alpha]

            if score < beta:                     #beta acts like min in minimax
                beta = score
                bestAction = action             
                    
        return[bestAction,beta]  
                 
    def move(self, p1, p2):
        p1, p2 = p1.upper(), p2.upper()
        piece = self[p1]
        dest  = self[p2]

        if (self[p1] is None):
            raise InvalidMove

       # print("1", self[p1], piece.color)
       # print("2", self[p2])

       # print("here we go sir",self)

        if self.player_turn != piece.color:
            raise NotYourTurn("Not " + piece.color + "'s turn!")

        enemy = self.get_enemy(piece.color)
        possible_moves = piece.possible_moves(p1)
        # 0. Check if p2 is in the possible moves
        if p2 not in possible_moves:
            raise InvalidMove

        #print("Possible Moves are", possible_moves)

        # If enemy has any moves look for check
        if self.all_possible_moves(enemy):
            #x = self.all_possible_moves(enemy)
            #print("x is")
            #print(x)
            if self.is_in_check_after_move(p1,p2):
                raise Check

        if not possible_moves and self.is_in_check(piece.color):
            raise CheckMate
        elif not possible_moves:
            raise Draw
        else:
            self._do_move(p1, p2)
            self._finish_move(piece, dest, p1,p2)

    def get_enemy(self, color):
        if color == "white": return "black"
        else: return "white"

    def _do_move(self, p1, p2):
        '''
            Move a piece without validation
        '''
        piece = self[p1]
        dest  = self[p2]
        del self[p1]
        self[p2] = piece

    def _undo_move(self, p1,p2):
        '''
        Undo a Move

        '''
        piece = self[p2]
        dest = self[p1]
        del self[p2]
        self[p1] = piece    

    def _finish_move(self, piece, dest, p1, p2):
        '''
            Set next player turn, count moves, log moves, etc.
        '''
        enemy = self.get_enemy(piece.color)
        if piece.color == 'black':
            self.fullmove_number += 1
        self.halfmove_clock +=1
        self.player_turn = enemy
        abbr = piece.abbriviation
        if abbr == 'P':
            # Pawn has no letter
            abbr = ''
            # Pawn resets halfmove_clock
            self.halfmove_clock = 0
        if dest is None:
            # No capturing
            movetext = abbr +  p2.lower()
        else:
            # Capturing
            movetext = abbr + 'x' + p2.lower()
            # Capturing resets halfmove_clock
            self.halfmove_clock = 0

        self.history.append(movetext)


    def all_possible_moves(self, color):
        '''
            Return a list of `color`'s possible moves.
            Does not check for check.
        '''
        if(color not in ("black", "white")): raise InvalidColor
        result = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].possible_moves(coord)
                if moves: result += moves

       # print(result)        
        return result

    def occupied(self, color):
        '''
            Return a list of coordinates occupied by `color`
        '''
        result = []
        if(color not in ("black", "white")): raise InvalidColor

        for coord in self:
            if self[coord].color == color:
                result.append(coord)
        return result

    def is_king(self, piece):
        return isinstance(piece, pieces.King)


    def get_king_position(self, color):
        for pos in self.keys():
            if self.is_king(self[pos]) and self[pos].color == color:
                return pos

    def get_king(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        return self[self.get_king_position(color)]

    def is_in_check(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        king = self.get_king(color)
        enemy = self.get_enemy(color)
        return king in map(self.__getitem__, self.all_possible_moves(enemy))

    def letter_notation(self,coord):
        if not self.is_in_bounds(coord): return
        try:
            return self.axis_y[coord[1]] + str(self.axis_x[coord[0]])
        except IndexError:
            raise InvalidCoord

    def number_notation(self, coord):
        return int(coord[1])-1, self.axis_y.index(coord[0])

    def is_in_bounds(self, coord):
        if coord[1] < 0 or coord[1] > 7 or\
           coord[0] < 0 or coord[0] > 7:
            return False
        else: return True

    def load(self, fen):
        '''
            Import state from FEN notation
        '''
        self.clear()
        # Split data
        fen = fen.split(' ')
        # Expand blanks
        def expand(match): return ' ' * int(match.group(0))

        fen[0] = re.compile(r'\d').sub(expand, fen[0])

        for x, row in enumerate(fen[0].split('/')):
            for y, letter in enumerate(row):
                if letter == ' ': continue
                coord = self.letter_notation((7-x,y))
                self[coord] = pieces.piece(letter)
                self[coord].place(self)

        if fen[1] == 'w': self.player_turn = 'white'
        else: self.player_turn = 'black'

        self.castling = fen[2]
        self.en_passant = fen[3]
        self.halfmove_clock = int(fen[4])
        self.fullmove_number = int(fen[5])

    def export(self):
        '''
            Export state to FEN notation
        '''
        def join(k, g):
            if k == ' ': return str(len(g))
            else: return "".join(g)

        def replace_spaces(row):
            # replace spaces with their count
            result = [join(k, list(g)) for k,g in groupby(row)]
            return "".join(result)


        result = ''
        for number in self.axis_x[::-1]:
            for letter in self.axis_y:
                piece = self[letter+str(number)]
                if piece is not None:
                    result += piece.abbriviation
                else: result += ' '
            result += '/'

        result = result[:-1] # remove trailing "/"
        result = replace_spaces(result)
        result += " " + (" ".join([self.player_turn[0],
                         self.castling,
                         self.en_passant,
                         str(self.halfmove_clock),
                         str(self.fullmove_number)]))
        return result
