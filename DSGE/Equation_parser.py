import ply.lex as lex
import ply.yacc as yacc

from numpy.random import normal

FUNCTIONS = {
    'N': normal
    }


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

    # Parsing rules

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    def p_statement_assign(self, p):
        'statement : NAME EQUALS expression'
        print(p[1])
        self.variables[p[1]] = p[3]

    def p_statement_expr(self, p):
        'statement : expression'
        print(p[1])

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EXP expression
        """
        # print [repr(p[i]) for i in range(0,4)]
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

    def p_expression_function(self,p):
        'statement : function'
        fun = FUNCTIONS[p[1][0]]
        params = p[1][1:]
        print(fun,params)

    def p_arglist(self,p):
        """arglist : arglist COMMA NAME
                   | arglist COMMA FLOAT
                   | FLOAT
                   | NAME"""
        if len(p) == 4:
            _ = p[1].copy()
            _.append(p[3])
            p[0] = _
        else:
            p[0] = [p[1]]

    def p_parameters(self,p):
        """parameters : LPAREN RPAREN 
                      | LPAREN arglist RPAREN"""
        if len(p) == 3:
            p[0] = []
        else:
            p[0] = p[2]

    def p_function(self, p):
        'function : NAME parameters'
        p[0] = [p[1]] + p[2]


    def p_expression_uminus(self, p):
        'expression : MINUS expression %prec UMINUS'
        p[0] = -p[2]
        
    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = p[2]

    def p_expression_INTEGER(self, p):
        'expression : INTEGER'
        p[0] = p[1]


    def p_expression_FLOAT(self, p):
        'expression : FLOAT'
        p[0] = p[1]
        
    def p_expression_name(self, p):
        'expression : NAME'
        try:
            p[0] = self.names[p[1]]
        except LookupError:
            print("Undefined name '%s'" % p[1])
            p[0] = 0


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
    
