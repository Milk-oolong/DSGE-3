import ply.lex as lex
import ply.yacc as yacc

from numpy.random import normal

FUNCTIONS = {
    'N': normal
    }


LAMBDA_BINOP = {
    '+': lambda x, y : x + y,
    '-': lambda x, y : x - y,
    '/': lambda x, y : x - y,
    '*': lambda x, y : x * y,
    '**': lambda x, y : x ** y
    }

def get_dependencies(tree,acc = []):
    if tree[0] is None:
        if type(tree[1]) == str:
            acc.append(tree[1])
    else:
        for t in tree[1:]:
            get_dependencies(t,acc)
    return acc

class Parser:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.variables = {}
        # Build the lexer and parser
        lex.lex(module=self)
        yacc.yacc(module=self)

    def run(self,s):
            yacc.parse(s)



class Calc(Parser):

    tokens = (
        'NAME', 'INTEGER', 'FLOAT',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE', 'EQUALS',
        'LPAREN', 'RPAREN', 'COMMA'
    )

    variables = {}
    end_of_chain_variables = set()

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

    def get_parameters(self):
        return {p for p,f in self.variables.items() if f is None}

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

    # Parsing rules

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    def p_statement(self,p):
        """statement : NAME EQUALS atom"""
        #Get dependencies
        dependencies = get_dependencies(p[3])
        
        self.variables[p[1]] = {
            'function': p[3],
            'dependencies': dependencies
        }
        self.end_of_chain_variables.add(p[1])
        for d in dependencies:
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


class Equation:

    def __init__(self,fun,deps):
        self.fun = fun
        self.deps = deps
        self.value = None

    def __call__(self):
        for dep in self.deps:
            dep()
        args = [dep.value for dep in self.deps]
        self.value = self.fun(*args)
        return self.value


class Parameter:

    def __init__(self,val):
        self.value = val

    def __call__(self):
        pass
    
