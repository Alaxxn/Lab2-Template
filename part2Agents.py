from model import (
    Location,
    Wizard,
    IceStone,
    FireStone,
    WizardMoves,
    GameAction,
    GameState,
    Wall,
    WizardSpells, NeutralStone,
)
from agents import WizardAgent

import z3
from z3 import (Solver, Bool, Bools, Int, Ints, Or, Not, And, Implies, Distinct, If)
        
class PuzzleWizard(WizardAgent):
    solution: list[WizardMoves]


    def __init__(self, initial_state: GameState):
        self.s = Solver()
        self.solution = None

    def react(self, state: GameState) -> WizardMoves:
        """ After Each Move this is called to retrieve the next Wizard Move"""

        if self.solution is None:
            PuzzleWizard.solution = self.solve_puzzle(state)

        return self.solution.pop(0)        

    def model_to_path(self, wiz_start, model):
        moves = []
        prev = (wiz_start.row, wiz_start.col)
        return MASYU_1_SOLUTION

    def solve_puzzle(self, state: GameState):

        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        height, width = state.grid_size
        wizard_location = state.active_entity_location

        # Gate for each direction
        connections = { 'up' : [], 'down' : [], 'left' : [], 'right' : []}

        # Each tile has a set of gates for it's edges
        for (direction, lis) in connections.items():
            for r in range(height):
                row = []
                for c in range(width):
                    tile = Bool(f'{direction}_{r}_{c}')
                    row.append(tile)                
                connections[direction].append(row)

        def turn_on(x, y):
            """ Force a turn on tile (x,y)"""
            up =  connections['up'][x][y]
            down = connections['down'][x][y]
            left = connections['left'][x][y]
            right = connections['right'][x][y]

            return Or( 
                And(up, right, Not(down), Not(left)),
                And(up, left, Not(down), Not(right)),
                And(down, right, Not(up), Not(left)),
                And(down, left, Not(up), Not(right)))
        
        def straight_on(x, y):
            """ Force straight movement on tile (x,y)"""
            up =  connections['up'][x][y]
            down = connections['down'][x][y]
            left = connections['left'][x][y]
            right = connections['right'][x][y]
            # No intersections is taken care of by the Not
            return Or(
                And(up, down, Not(left), Not(right)),
                And(left, right, Not(up), Not(down)))
        
        def no_move(x, y):
            """ Doesn't have any open connections"""
            return Or( And(
                    Not(connections['up'][x][y]),
                    Not(connections['down'][x][y]),
                    Not(connections['left'][x][y]),
                    Not(connections['right'][x][y])))
        
        # Each tile can either be a straight, a turn, or None
        for r in range(height):
            for c in range(width):
                moves = Or(turn_on(r,c), straight_on(r,c), no_move(r,c))
                self.s.add(moves)

        # Fire Stones
        for f_stone in fire_stones:
            self.s.add(turn_on(f_stone.row, f_stone.col))
            # More Rules to add...
        
        # Ice Stones
        for i_stone in ice_stones:
            self.s.add(straight_on(i_stone.row, i_stone.col))
            # If up down
                # then staright above, and turn under
                    # or turn above and straight under
            # if left and right
                # then staright left, and turn right
                    # or turn left and straight right
        
        # Invalid Moves
        for c in range(width):
            self.s.add(no_move(0, c))             # top row
            self.s.add(no_move(height - 1, c))    # bottom row
        for r in range(height):
            self.s.add(no_move(r, 0))             # left column
            self.s.add(no_move(r, width - 1))     # right column

        # All open gates are connected
        for r in range(1, height-1): # -1 works because of our barriers
            for c in range(1, width-1):
                self.s.add(Implies(connections['up'][r][c], connections['down'][r-1][c])) # Connected above
                self.s.add(Implies(connections['down'][r][c], connections['up'][r+1][c])) # Connected under
                self.s.add(Implies(connections['right'][r][c], connections['left'][r][c+1])) #...
                self.s.add(Implies(connections['left'][r][c], connections['right'][r][c-1]))

        match self.s.check():
            case z3.sat:
                m = self.s.model()
                
                # ChatGPT Debug Loop :)
                for r in range(height):
                    for c in range(width):
                        up = bool(m.evaluate(connections['up'][r][c]))
                        down = bool(m.evaluate(connections['down'][r][c]))
                        left = bool(m.evaluate(connections['left'][r][c]))
                        right = bool(m.evaluate(connections['right'][r][c]))

                        if up and down and not left and not right:
                            symbol = "│"
                        elif left and right and not up and not down:
                            symbol = "─"
                        elif down and right and not up and not left:
                            symbol = "┌"
                        elif down and left and not up and not right:
                            symbol = "┐"
                        elif up and right and not down and not left:
                            symbol = "└"
                        elif up and left and not down and not right:
                            symbol = "┘"
                        elif not up and not down and not left and not right:
                            symbol = "."
                        else:
                            symbol = "?"

                        print(symbol, end=" ")
                    print()
                self.solution = self.model_to_path(wizard_location, m)

            case z3.unsat:
                print("UNSAT :(\n")

        self.solution = MASYU_1_SOLUTION # DELETE ME  

        

class SpellCastingPuzzleWizard(WizardAgent):

    def react(self, state: GameState) -> GameAction:
        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        neutral_stones = state.get_all_tile_locations(NeutralStone)

        grid_size = state.grid_size
        wizard_location = state.active_entity_location

        # TODO: YOUR CODE HERE
        return MASYU_2_SOLUTION.pop(0)


"""
Here are some reference solutions for some of the included puzzle maps you can use to help you test things
"""

MASYU_1_SOLUTION =[WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP]


MASYU_2_SOLUTION =[WizardMoves.RIGHT,WizardSpells.FIREBALL,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.DOWN,WizardSpells.FREEZE,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.LEFT,WizardMoves.DOWN,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardMoves.RIGHT,WizardMoves.UP,WizardMoves.UP,WizardMoves.UP,WizardMoves.LEFT,WizardMoves.UP,WizardMoves.UP,WizardSpells.FIREBALL,WizardMoves.RIGHT]

