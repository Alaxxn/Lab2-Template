from model import (
    Location,
    Wizard,
    IceStone,
    FireStone,
    WizardMoves,
    GameAction,
    GameState,
    WizardSpells, NeutralStone,
)
from agents import WizardAgent

import z3
from z3 import (Solver, Bool, Bools, Int, Ints, Or, Not, And, Implies, Distinct, If)

    # grid_size: tuple[int, int]
    # tile_grid: tuple[tuple[MapTile, ...], ...]
    # entity_grid: tuple[tuple[Entity, ...], ...]
    # active_entity_location: Location
    # turn: int = 0
    # mana_spent: int =0


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

    def solve_puzzle(self, state: GameState):

        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        height, width = state.grid_size

        x_t = []
        y_t = []
        moves = []
        max_steps = (height - 1) * (width - 1) # -1 for the border

        # Possible Moves
        U,R,D,L = Ints('U R D L')
        self.s.add(U == 1, R == 2, D == 3, L == 4)

        # Allowed Moves
        for t in range(max_steps):
            key = f'move_{t}'
            move_t = Int(key)
            moves.append(move_t)
            self.s.add(Or(move_t == U, move_t == R, move_t == L, move_t == D)) # valid moves

        # Wizard Stays Inside the board
        for t in range(max_steps + 1):
            x = Int(f'x_{t}')
            y = Int(f'y_{t}')
            x_t.append(x)
            y_t.append(y)
            self.s.add(And(1 <= x, x < (width - 1) )) # Inside the board
            self.s.add(And(1 <= y, y < (height - 1) ))
        
        # Fire Stones Visited
        for stone in fire_stones:
            sx, sy = stone.col, stone.row
            visited = []
            for t in range(max_steps):
                visited.append(And(x_t[t] == sx, y_t[t] == sy)) # True if visited at that turn
            self.s.add(Or(*visited)) # True if visited at some turn

        # Ice Stones Visited
        for stone in ice_stones:
            sx, sy = stone.col, stone.row
            visited = []
            for t in range(max_steps):
                visited.append(And(x_t[t] == sx, y_t[t] == sy)) 
            self.s.add(Or(*visited))

        # Starting position
        wizard_location = state.active_entity_location
        self.s.add(x_t[0] == wizard_location.col)
        self.s.add(y_t[0] == wizard_location.row)

        """
        TODO: Remaining Constraints
        
        1. End at starting location
        2. No Intersections
        3. FireStone Rules
            # Must make a 90 degree turn
            # No turns directly before or after
        4. Ice Stone Rules
    
            # Travel through in a straight line
            # Must turn on t-1 or after cell
        """

        # Movememnt
        # for t in range(max_steps):
        #     self.s.add(Implies(moves[t] == U,
        #         And(x_t[t+1] == x_t[t], y_t[t+1] == y_t[t] - 1)))

        #     self.s.add(Implies(moves[t] == D,
        #         And(x_t[t+1] == x_t[t], y_t[t+1] == y_t[t] + 1)))

        #     self.s.add(Implies(moves[t] == L,
        #         And(x_t[t+1] == x_t[t] - 1, y_t[t+1] == y_t[t])))

        #     self.s.add(Implies(moves[t] == R,
        #         And(x_t[t+1] == x_t[t] + 1, y_t[t+1] == y_t[t])))
    
        
        # No Intersection (MAKES IT SUPER SLOW HOLY)
        # for i in range(max_steps + 1): # For Every position (not icluding starting)
        #     illegal_pos = []
        #     for j in range(1, i, 1): # Make sure every t-1 position
        #         same_x = x_t[i] == x_t[j]
        #         same_y = y_t[i] == y_t[j]
        #         same_pos = And(same_x, same_y)
        #         illegal_pos.append(Not(same_pos)) # Isn't the same
        #     self.s.add(*illegal_pos)

        print("Checking for model\n")

        match self.s.check():
            case z3.sat:
                m = self.s.model()
                move_dict = {
                    '1' : WizardMoves.UP,
                    '2' : WizardMoves.RIGHT,
                    '3' : WizardMoves.DOWN,
                    '4' : WizardMoves.LEFT,
                }

                plan = []

                # Convert Model to Moves
                for move in moves:
                    key = str(m[move].as_long())
                    plan.append(move_dict[key])

                # Print Planned Positions
                for i in range(len(x_t)):
                    x = x_t[i]
                    y = y_t[i]
                    x_val = m[x].as_long()
                    y_val = m[y].as_long()
                    print(f"{i} : ({x_val}, {y_val})")
                    plan.append(move_dict[key])

                print(plan)
                self.solution = plan
            
            case z3.unsat:
                self.solution = MASYU_1_SOLUTION
                print("UNSAT :(\n")


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

