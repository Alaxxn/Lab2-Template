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
        self.solution = None

    def react(self, state: GameState) -> WizardMoves:
        """ After Each Move this is called to retrieve the next Wizard Move"""

        if self.solution is None:
            PuzzleWizard.solution = self.solve_puzzle(state)

        return self.solution.pop(0)        

    def get_next_location (self, model, connections, prev : Location, curr : Location):
        """ returns the move to get to the next location, and the resulting tile"""
        x,y = (curr.row, curr.col)

        outputs = {
            'up': (WizardMoves.UP, Location(curr.row - 1, curr.col)),
            'down': (WizardMoves.DOWN, Location(curr.row + 1, curr.col)),
            'left': (WizardMoves.LEFT, Location(curr.row, curr.col - 1)),
            'right': (WizardMoves.RIGHT, Location(curr.row, curr.col + 1))
        }
        
        gates = []
        for direction in connections:
            is_open = model.evaluate(connections[direction][x][y])
            if (is_open): 
                gates.append(direction)

        if (prev == None): # is Start
            next_gate = gates.pop() # Choose any direction
            return outputs[next_gate]

        # Remove gate we came in from
        if (prev.col < curr.col):
            gates.pop(gates.index("left"))
        elif (prev.col > curr.col):
            gates.pop(gates.index("right"))
        elif (prev.row < curr.row):
            gates.pop(gates.index("up"))
        else:
            gates.pop(gates.index("down"))

        # This is where we have to be going
        next_gate = gates.pop()
        return outputs[next_gate]

    def model_to_path(self, model, wiz : Location, connections):

        moves = []
        prev = None
        curr = wiz
        next_tile = None

        while (True):
            if (next_tile == wiz): # Cycle Complete
                break
            move, next_tile = self.get_next_location(model, connections, prev, curr)
            moves.append(move)
            prev = curr
            curr = next_tile
        
        print(moves)
        return moves

    def solve_puzzle(self, state: GameState):

        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        walls = state.get_all_tile_locations(Wall)
        height, width = state.grid_size
        wizard_location = state.active_entity_location
        s = Solver()

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
                s.add(moves)

        # Fire Stones
        for f_stone in fire_stones:
            r, c = (f_stone.row, f_stone.col)
            s.add(turn_on(r, c)) # Tile rule

            s.add(Implies( # Each type of turn's outer tiles are straight
                And(connections['up'][r][c], connections['right'][r][c]), # we don't care about direction
                And(straight_on(r - 1, c), straight_on(r, c + 1))))
            s.add(Implies( 
                And(connections['up'][r][c], connections['left'][r][c]),
                And(straight_on(r - 1, c), straight_on(r, c - 1))))
            s.add(Implies( 
                And(connections['down'][r][c], connections['left'][r][c]),
                And(straight_on(r + 1, c), straight_on(r, c - 1))))
            s.add(Implies( 
                And(connections['down'][r][c], connections['right'][r][c]),
                And(straight_on(r + 1, c), straight_on(r, c + 1))))

        # Ice Stones
        for i_stone in ice_stones:
            (r, c) = (i_stone.row, i_stone.col)
            s.add(straight_on(r, c)) # Tile rule
            
            # Atleast one turn before or after the tile
            s.add(Implies(And(connections['up'][r][c], connections['down'][r][c]),
                    Or(turn_on(r-1, c), turn_on(r+1, c))))
            s.add(Implies(And(connections['left'][r][c], connections['right'][r][c]),
                    Or(turn_on(r, c+1), turn_on(r, c-1))))
    
        # Invalid Moves (Walls)
        for wall in walls:
            s.add(no_move(wall.row, wall.col))

        # All open gates are connected
        for r in range(1, height-1):
            for c in range(1, width-1):
                s.add(Implies(connections['up'][r][c], connections['down'][r-1][c])) # Connected up
                s.add(Implies(connections['down'][r][c], connections['up'][r+1][c])) # Connected down
                s.add(Implies(connections['right'][r][c], connections['left'][r][c+1])) #...
                s.add(Implies(connections['left'][r][c], connections['right'][r][c-1]))

        dist = [] # Each tile has distance from the start
        for r in range(height):
            row = []
            for c in range(width):
                row.append(Int(f"dist_{r}_{c}"))
            dist.append(row)

        # The starting tile (distance == 0)
        s.add(Not(no_move(wizard_location.row, wizard_location.col)))
        s.add(dist[wizard_location.row][wizard_location.col] == 0)
    
        max_dist = height * width # visiting every tile
        # Other tiles Initialized
        for r in range(height):
            for c in range(width):
                in_path = Not(no_move(r, c))
                s.add(Implies(in_path, And(dist[r][c] >= 0, dist[r][c] <= max_dist))) # is a valid dist
                s.add(Implies(no_move(r, c), dist[r][c] == -1)) # Not part of path
        
        # A single cycle
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                in_path = Not(no_move(r, c))
                is_start = And(r == wizard_location.row, c == wizard_location.col)

                has_previous_path_tile = Or( # The current tile is only a distance of +1 from the path to start
                    And(connections['up'][r][c], dist[r-1][c] == dist[r][c] - 1),
                    And(connections['down'][r][c], dist[r+1][c] == dist[r][c] - 1),
                    And(connections['left'][r][c], dist[r][c-1] == dist[r][c] - 1),
                    And(connections['right'][r][c], dist[r][c+1] == dist[r][c] - 1))
                
                # Every tile used is a valid distance away
                s.add(Implies(And(in_path, Not(is_start)), has_previous_path_tile)) # Path Moves Forward
                        

        match s.check():
            case z3.sat:
                m = s.model()
                self.solution = self.model_to_path(m, wizard_location, connections)
            case z3.unsat:
                print("UNSAT :(\n")
    

class SpellCastingPuzzleWizard(PuzzleWizard):
    solution: list[WizardMoves]

    def react(self, state: GameState) -> GameAction:

        if self.solution is None:
            PuzzleWizard.solution = self.solve_magic_puzzle(state)

        return self.solution.pop(0)
    
    def solve_magic_puzzle(self, state):

        if (len(neutral_stones) == 0): # Don't need to do anything
            self.solve_puzzle(state)
            return 

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

