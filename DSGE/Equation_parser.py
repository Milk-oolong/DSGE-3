import ply.lex as lex
import ply.yacc as yacc

from numpy.random import normal

########################################################################
# MODULE DESCRIPTION
#
# This module contains the class responsible for parsing the variables 
# definition. It implements a PLY parser and lexer.
#

########################################################################
# TO DO LIST
#
# Add lag operator (complicated to add, but important)
# Add a uminus rules for atom
#       For the moment, only exists for number
# Add new functions (e.g. exp, log) from numpy (easy to do)
# Check why get_dependencies needs [] as a second argument
#       If second argument is blank, it creates a single list of
#       dependencies for all variables
# Add docstring
# check why p_number_binop_atom rule is required
#       I should not need it theoretically, but string such as
#       2+A won't parse otherwise
# Add reconciliation rules for variables defined twice
#       e.g. what to do if parsing Y=A and Y=B?
#


########################################################################
# CONSTANTS AND FUNCTIONS
#
# This module relies on two constants:
#      FUNCTIONS: mapping of function names (str) to actual python 
#                 functions
#      LAMBDA_BINOP: Mapping of string representation of binary
#                    operators to lambda function
#      get_dependencies: Retrieve dependencies of a variable from its
#                        function tree
#

FUNCTIONS = {
    'N': normal     #Normal law N(mu,sigma) from numpy
    }


LAMBDA_BINOP = {
    '+': lambda x, y : x + y,
    '-': lambda x, y : x - y,
    '/': lambda x, y : x - y,
    '*': lambda x, y : x * y,
    '**': lambda x, y : x ** y
    }

def get_dependencies(tree,acc = []):
    """
    Description
    -----------
    Takes a function tree from and returns a list of its arguments through a recursive loop

    Arguments
    ---------
    * tree: A function tree
    * acc: Accumulator used to store arguments during recursive loops

    Returns
    ------
    A list of str where each element is an argument of the function represented by the function tree
    
    """
    if tree[0] is None:
        #If tree is none, then the 2nd element is either a variable argument (str) or a numeric argument. We only retrieve str here
        if type(tree[1]) == str:
            acc.append(tree[1])
    else:
        for t in tree[1:]:
            #Recursive loops over all arguments of the current branch of the tree
            get_dependencies(t,acc)
    return acc


########################################################################
# BASE CLASS FOR PARSER
#
# Based on examples from https://github.com/dabeaz/ply/blob/master/example/classcalc/calc.py

class Parser:
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.variables = {}
        # Build the lexer and parser
        lex.lex(module=self)
        yacc.yacc(module=self)

    def run(self,s):
            yacc.parse(s)

########################################################################
# MAIN CLASS: Econ_model_parser
#

            

class Econ_model_parser(Parser):
    """
    Description
    -----------
    Parser for economic models.

    This class allows to parse strings of variables. Each string parsed should have the following form:
    'Alphanum = f(Alphanum,num)'
    Where Alphanum is an alphanumeric string (starting with a character and may include underscore).

    The class stores two useful attributes when parsing
    * self.variables
    * self.end_of_chain_variables

    self.variables
    --------------
    self.variables is a dictionary with all variables and parameters. The key of the dict is the variable name. The value of the dict is a function tree

    self.end_of_chain_variables
    ---------------------------
    self.end_of_chain_variables contains a set of all variables without successor. In the example below, no variable depends on Y, thus Y is the only end of chain variable.
    

    Example
    -------
    parser = Econ_model_parser()
    
    #We run the parser on two very simple variable definitions
    parser.run('Y = A*x + B')
    parser.run('A = N(mu,sigma)')

    print(parser.variables)
    > {'Y': {'function': [<function Econ_model_parser.p_atom_binop.<locals>.<lambda> at 0x7fccb9542950>, [<function Econ_model_parser.p_atom_binop.<locals>.<lambda> at 0x7fccb95428c8>, [None, 'A'], [None, 'x']], [None, 'B']], 'dependencies': ['A', 'x', 'B']}, 'A': {'function': [<built-in method normal of mtrand.RandomState object at 0x7fccb9b435a0>, [None, 'mu'], [None, 'sigma']], 'dependencies': ['mu', 'sigma']}, 'x': None, 'B': None, 'mu': None, 'sigma': None}

    print(parser.end_of_chain_variables)
    {'Y'}
    """
########################################################################
# VARIABLES STORAGE DECLARATION
#
#

    variables = {}
    end_of_chain_variables = set()

    def get_parameters(self):
        return {p for p,f in self.variables.items() if f is None}

    def get_end_of_chain_variables(self):
        return {v: self.variables[v] for v in self.end_of_chain_variables}

########################################################################
# TOKENS DEFINITION
#
# Tokens for parsing are defined below
#

    tokens = (
        'NAME', 'INTEGER', 'FLOAT',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE', 'EQUALS',
        'LPAREN', 'RPAREN', 'COMMA'
    )

    # Tokens

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_EXP = r'\*\*'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_EQUALS = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    t_COMMA = r','

    def t_FLOAT(self, t):
        '(\d*[.])?\d+'
        #'\d+(\.(\d+)?([eE][-+]?\d+)?|[eE][-+]?\d+)'
        t.value = float(t.value)
        return t
    
    def t_INTEGER(self,t):
        '\d+'
        t.value = int(t.value)
        return t
    
    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

########################################################################
# PARSING RULE LIST
#
# statement: NAME EQUALS atom
# arglist : arglist COMMA NAME | arglist COMMA number | number | NAME
# parameters : LPAREN RPAREN | LPAREN arglist RPAREN
# function : NAME parameters
# number : INTEGER | FLOAT
# number : number PLUS number | number MINUS number | number TIMES number | number DIVIDE number | number EXP number
# atom : atom PLUS atom | atom MINUS atom | atom TIMES atom | atom DIVIDE atom | atom EXP atom
# atom : number PLUS atom | number MINUS atom | number TIMES atom | number DIVIDE atom | number EXP atom
# number : MINUS number %prec UMINUS
# number : LPAREN number RPAREN
# atom : LPAREN atom RPAREN
# variable : NAME
# atom: number
# atom: variable
# atom: function
#

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    def p_statement(self,p):
        """statement : NAME EQUALS atom"""
        # When the line is a statement, get dependencies and
        # store the variable in the appropriate dict
        
        dependencies = get_dependencies(p[3],[])
        
        if p[1] not in self.variables.keys():
            # Check if the variable has been defined and store it
            # If the variable is already stored, this may mean two things:
            # Either p[1] is a parameter for a variable which has already be defined, in which case no further action is needed
            # Or p[1] has already be defined before and is redefined now. In this case, I will implement a reconciliation rule later
            self.end_of_chain_variables.add(p[1])

        #Add variable to the main dict
        self.variables[p[1]] = {
            'function': p[3],
            'dependencies': dependencies.copy()
        }
        for d in dependencies:
            #Add dependencies to main dict if necessary and remove from end_of_chain variable
            if d not in self.variables.keys():
                self.variables[d] = None
            elif d in self.end_of_chain_variables:
                self.end_of_chain_variables.remove(d)
        

    def p_arglist(self,p):
        """
        arglist : arglist COMMA NAME
                   | arglist COMMA number
                   | number
                   | NAME
        """
        if len(p) == 4:
            _ = p[1].copy()
            _.append([None,p[3]])
            p[0] = _
        else:
            p[0] = [[None,p[1]]]

    def p_parameters(self,p):
        """parameters : LPAREN RPAREN 
                      | LPAREN arglist RPAREN"""
        if len(p) == 3:
            p[0] = []
        else:
            p[0] = p[2]

    def p_function(self, p):
        'function : NAME parameters'
        fun = FUNCTIONS[p[1]]
        p[0] = [fun] + p[2]

    def p_number(self, p):
        """number : INTEGER 
                      | FLOAT"""
        p[0] = p[1]

    def p_number_binop(self,p):
        """
        number : number PLUS number
               | number MINUS number
               | number TIMES number
               | number DIVIDE number
               | number EXP number
        """
        if p[2] == '+':
            p[0] = p[1] + p[3]
        elif p[2] == '-':
            p[0] = p[1] - p[3]
        elif p[2] == '*':
            p[0] = p[1] * p[3]
        elif p[2] == '/':
            p[0] = p[1] / p[3]
        elif p[2] == '**':
            p[0] = p[1] ** p[3]

    def p_atom_binop(self,p):
        """
        atom : atom PLUS atom
             | atom MINUS atom
             | atom TIMES atom
             | atom DIVIDE atom
             | atom EXP atom
        """
        binop = LAMBDA_BINOP[p[2]]
        p[0] = [lambda x,y: binop(x,y)] + [p[1],p[3]]

    def p_atom_number_binop_atom(self,p):
        """atom : number PLUS atom
                | number MINUS atom
                | number TIMES atom
                | number DIVIDE atom
                | number EXP atom"""
        binop = LAMBDA_BINOP[p[2]]
        p[0] = [lambda x,y: binop(x,y)] + [[None,p[1]],p[3]]


    def p_number_uminus(self, p):
        'number : MINUS number %prec UMINUS'
        p[0] = -p[2]

    def p_number_group(self,p):
        'number : LPAREN number RPAREN'
        p[0] = p[2]

    def p_atom_group(self,p):
        'atom : LPAREN atom RPAREN'
        p[0] = p[2]

    def p_variable(self,p):
        'variable : NAME'
        p[0] = p[1]

    def p_atom_number(self,p):
        """atom : number"""
        p[0] = [None,p[1]]

    def p_atom_variable(self,p):
        """atom : variable"""
        p[0] = [None, p[1]]

    def p_atom_function(self,p):
        """atom : function"""
        p[0] = p[1]

    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")
