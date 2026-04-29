import z3
from z3 import (Solver, Bool, Bools, Int, Ints, Or, Not, And, Implies, Xor, BitVec, BV2Int, Reals, Distinct, If)

"""
Suppose we want to find a satisfying assignment for the expression (a || !b) && (!a || c). 
That means we’re looking for values of a, b, and c that make the entire expression evaluate to true.

One way to approach this is by checking all possible combinations of truth values for a, b, and c. 
Since each variable can be either true or false, there are 2^3=8 possible combinations.

Can you list all 8 combinations of a, b, and c?

In general, for n variables, there will be 2^n possible assignments, so the approach of "trying everything" 
is not efficient for large n. In fact, this is the SAT ("satisfiability") problem, which is NP-complete, 
meaning that it is "one of the hardest problems to which solutions can be verified quickly. 
But this difficult problem is exactly what tools like the Z3 SMT solver! Here’s how we can solve the problem using the Z3:
"""

def boolean_expressions():
    a = Bool('a')
    b = Bool('b')
    c = Bool('c')

    s = Solver()

    clause_1 = Or(a,Not(b))
    clause_2 = Or(Not(a),c)

    s.add(clause_1)
    s.add(clause_2)

    match s.check():
        case z3.sat:
            f_1_model = s.model()
            print(f_1_model)

    """
    The output says that the formula (a || !b) && (!a || c) will be true when a, b, and c are all false.

    But what if we want a different solution?

    In this case, we can add an additional constraint that says that we don’t want the solution where a, b, and c are all false.
    """


    clause_3 = Not(And(Not(a),Not(b),Not(c)))
    s.add(clause_3)

    match s.check():
        case z3.sat:
            f_2_model = s.model()
            print(f_2_model)

    """
    This output says that the formula (a || !b) && (!a || c) will be true 
    when b is false and c is true (it doesn’t matter what a is).

    Let’s try adding one more constraint
    """

    clause_4 = (And(Not(a),b))
    s.add(clause_4)
    match s.check():
        case z3.unsat:
            print("Unsatisfiable")
    """
    The output unsat means unsatisfiable. 
    The solver is telling us that there is no possible choice of a, b, c that makes the current constraints true.
    """

"""
Z3 can find solutions to more than just SAT problems – it is an SMT solver.

SMT stands for SAT modulo theories; it generalizes SAT to formulas involving integers, strings, arrays, 
and so on (the details of how it can do this are interesting but complicated, and we probably wont be able 
to get to them in class). For example, we can use Z3 to find a solution for the system of equations 3x - 2y = 1, y - x = 1.
"""
def integer_expressions():
    x,y = Ints('x y')
    s=Solver()
    s.add(3*x - 2*y == 1)
    s.add(y - x == 1)

    match s.check():
        case z3.sat:
            model = s.model()
            print(model)

"""
In addition to integers Z3 can solve systems of equations that use real numbers. 
These can get quite complex and also very useful potentially for some of your final projects.
"""

def real_artithmetic():
    x, y = Reals('x y')
    s=Solver()
    s.add(x != 0)
    s.add(y != 0)
    s.add(x + y == 4 * x * y)
    match s.check():
        case z3.sat:
            print (f"Model: {s.model()}")

        case z3.unsat:
            print ("UNSAT")

"""
One of the most prominent uses of SMT in industry (especially now when so much software is being 
produced with little else to ensure correctness) is in software verification. You can see how we 
can prove interesting properties about programs including relating logical properties with 
underlying representation properties.
"""

def integer_overflow():
    # Note this takes a long time to process!
    x = BitVec('x', 16)
    y = BitVec('y', 16)

    s=Solver()
    s.add((BV2Int(x) + BV2Int(y)) != BV2Int(x+y))
    match s.check():
        case z3.sat:
            print (f"Model: {s.model()}")

        case z3.unsat:
            print ("UNSAT")


"""
Often, SMT solvers are not used to find a solution, but to prove that no solution exists. 
For instance, say that we want to prove the mathematical fact y > 0 ==> x + y > x. 
How might we do this using z3?
"""
def proof_by_unsat():
    # y>0 => x+y > x
    x,y = Ints('x y')
    s = Solver()

    # Negating implication
    # showing the negation isn't possible
    # i.e if y > 0 then x + y > 0 cannot be false
    s.add(Not( Implies((y > 0), (x + y > x))))

    match s.check():
        case z3.unsat:
           print("The formula is UNSAT, meaning no contradiction can be found. " \
           "Therefore the original formula must always be true.  QED. \n")


"""
Similarly, how might we try to generally prove any valid logical formula such as De Morgan's Laws?
"""
def demorgans_proof():
    p, q = Bools('p q')
    demorgan = And(p, q) == Not(Or(Not(p), Not(q)))

    def prove(f):
        """
        Print "No counterexample can be found, therefore the statement is true" if the given 
        formula f is true, otherwise print "The formula f is false, with counterexample 
        given by: " and the model that shows the formula to be false.
        """
        s = Solver()
        s.add(Not(f))

        match s.check():
            case z3.unsat:
                print("No counterexample can be found, therefore the statement is true\n")
            case z3.sat:
                print(f"The formula f is false, with counterexample given by: {s.model()}\n")

    prove(demorgan)


"""
Let us try to use z3 to solve a classic kind of puzzle. You will need to come up with an 
encoding of the relevant part of the puzzle into variables and constraints as well 
translate the output of the solver into a solution.
"""

def wedding_planning():
    """
    You need to assign seating for a table of three potentially contentious wedding guests.

    There are three seats: left, middle, right.
    There are three guests: Alice, Bob, Charlie.

    The requirements are that:

    - Alice does not sit next to Charlie

    - Alice does not sit on the leftmost chair

    - Bob does not sit to the right of Charlie


    Can you find a seating arrangement that satisfies all of the guests?

    Print out either:
        The satisfying arrangement in the form "Alice sits on the left, Charlie in the middle, and Bob on the right."
    or
        "There is no acceptable seating arraignment"
    """
    

    s = Solver()

    l, m, r = Ints('l m r')
    alice, bob, charlie = Ints('alice bob charlie')

    # Define seat values
    s.add(l == 1, m == 2, r ==3)

    # Assign Seats
    s.add(Or(alice == l, alice == m, alice == r))
    s.add(Or(bob == l, bob == m, bob == r))
    s.add(Or(charlie == l, charlie == m, charlie == r))

    # Cannot share the same seat
    s.add(Distinct(alice, bob, charlie))

    # expnasion of diff(x,y) != 1
        # x-y != 1 and x-y != -1 ===> not to my left and not to my right (not next to me)
    s.add(And(alice - charlie != 1, alice - charlie != -1))
    
    # alice != left
    s.add(alice != l)

    # # Bob is not to the right of charlie
    s.add(Not(bob > charlie))

    match s.check():
        case z3.unsat:
            print("There is no acceptable seating arraignment")
        case z3.sat:
            seats = ['left', 'middle', 'right']
            people = ['bob', 'charlie', 'alice']
            arrangement = [None] * len(seats)

            m = s.model()
            for x in m.decls():
                person = x.name()
                if (person in people):
                    seat = m[x].as_long() - 1
                    arrangement[seat] = person
    
            seat_map = dict(zip(seats, arrangement))

            print(f"{seat_map['left']} sits on the left, "
                f"{seat_map['middle']} in the middle, "
                f"and {seat_map['right']} on the right.")

# wedding_planning()


"""
Lets try to solve a more complex puzzle like sudoku, given an arbitrary input.

In case you do not know, sudoku is a puzzle where the goal is to insert numbers in boxes to satisfy the 
following condition: each row, column, and 3x3 box must contain the digits 1 through 9 exactly once.

You will need to transform an arbitrary sudoku puzzle template (where zero represents the unfilled boxes) 
into a solved puzzle (or show that the puzzle is impossible).
"""

def print_sudoku(grid):
    for i,row in enumerate(grid):
        if i%3==0:
            print('-'*25)
        print(f'| {row[0]} {row[1]} {row[2]} | {row[3]} {row[4]} {row[5]} | {row[6]} {row[7]} {row[8]} |')
    print('-'*25)


def sudoku(puzzle):

    """
    Use print_sudoku to print your solution to puzzle or otherwise print "The puzzle is impossible.".
    """

    s = Solver()

    # Every position has an identifier with a value = (1-9)
    board = []
    for row in range(len(puzzle)):
        row_values = []
        for col in range(len(puzzle[0])): 
            x = Int(f'{row}_{col}')
            if (puzzle[row][col] == 0):
                s.add(And(0 < x, x < 10)) # Range of values
            else:
                s.add(x == puzzle[row][col]) # intial board
            row_values.append(x)
        board.append(row_values)
    
    # Each Row needs to have values 1-9
    for row_values in board:
        s.add(Distinct(*row_values))
    
    # Distinct Columnns
    for col in range(len(board[0])):
        col_values = []
        for row in range(len(board)):
            col_values.append(board[row][col])
        s.add(Distinct(*col_values))
    
    # Distinct 3x3 Boxess
    for row in range (0, len(board), 3):
        for col in range (0, len(board[0]), 3):
            #Note: Could use NumPy here instead
            box_values = []
            for i in range(3):
                for x in range(3):
                    box_values.append(board [row + i][col + x])
            s.add(Distinct(*box_values))

    # Solve
    match s.check():
        case z3.unsat:
            print("The puzzle is impossible.")
        case z3.sat:
            m = s.model()
            solved = []
            for row in range(9):
                solved_row = []
                for col in range(9):
                    val = m.evaluate(board[row][col]).as_long()
                    solved_row.append(val)
                solved.append(solved_row)

            print_sudoku(solved)


instance = ((0,0,0,0,9,4,0,3,0),
            (0,0,0,5,1,0,0,0,7),
            (0,8,9,0,0,0,0,4,0),
            (0,0,0,0,0,0,2,0,8),
            (0,6,0,2,0,1,0,5,0),
            (1,0,2,0,0,0,0,0,0),
            (0,7,0,0,0,0,5,2,0),
            (9,0,0,0,6,5,0,0,0),
            (0,4,0,9,7,0,0,0,0))

# sudoku(instance)


"""
The final puzzle you will solve using Z3 is the Coin Sum problem. Here in the US we have (or used to have)
pennies worth 1 cent, nickels worth 5 cents, dimes worth 10 cents, quarters worth 25 cents, half dollar 
coins worth 50 cents, and dollar coins worth 100 cents.

It is possible to make $2 using these coins in the following way:

    1 * 1$ + 1*50c + 1*25c + 1*10c + 2*5c + 5*1c

The question is: How many ways can $2 be made using any number of coins?
"""

def get_model(s : Solver): 
    match s.check():
        case z3.unsat:
            return None
        case z3.sat:
            m = s.model()
            return m
        
def model_to_clause(m):
    clause_list = []
    for x in m.decls():
        var = x()  # get the Z3 variable
        clause_list.append(var == m[x])
    return And(clause_list)

def coin_sum(total : float):
    """ Print the number of ways the total (in dolalrs)
    can be made using any number of the above coins. """

    p,n,di,q,h,d = Ints('p n di q h d')
    t_cents = Int('t')
    s = Solver()

    # The Function
    d_x = d * 100
    h_y = h * 50
    q_z = q * 25
    di_i = di * 10
    n_j = n * 5
    p_k = p * 1
    t_cents = int(round(total * 100))
    f = d_x + h_y + q_z + di_i + n_j + p_k == t_cents

    # Constraint
    s.add(f)
    # Values are positive
    s.add(p >= 0, n >= 0, di >= 0, q >= 0, h >= 0, d >= 0)

    count = 0
    solution = get_model(s)
    while (solution != None):
        clause = model_to_clause(solution)
        s.add(Not(clause)) # Remove model from space 
        count+= 1
        solution = get_model(s)
    
    print(count)
    return

coin_sum(2.00)