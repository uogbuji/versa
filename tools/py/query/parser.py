'''
versa.query.parser
'''

import ply.lex as lex
import ply.yacc as yacc

#------------------
# Parser
#------------------

# Lexer tokens.
tokens = (
   'WILD',
   'VAR',
   'IDENT',
   'AND',
   'OR',
   'NOT',
   'STRING',
   'LPAREN',
   'RPAREN',
   'COMMA',
   'QUESTION',
)

# Regular expression rules for simple tokens
t_WILD    = r'\*'
t_IDENT   = r'\w+'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_AND     = r'and'
t_OR      = r'or'
t_NOT     = r'not'
t_COMMA   = r','
t_QUESTION = r'\?'

def t_STRING(t):
    r'("[^"]*")|(\'[^\']*\')'
    t.value = t.value[1:-1]
    return t

def t_VAR(t):
    r'\$\w+'
    t.value = t.value[1:]
    return t

#Ignored characters (spaces & tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

#------------------
# Parser
#------------------

'''
from versa.query import parse, context
from versa.driver import memory
parsed = parse("?($a, DC 'title', *)")
#parsed = parse("?($a, V 'type', BL 'Instance') and ?($a, V 'type', MARC 'ElectronicResource') and ?($b, V 'type', BL 'Work') and ?($b, V 'type', MARC 'Books')")
DC = 'http://purl.org/dc/elements/1.1/'
HTML5 = 'http://www.w3.org/TR/html5/'
U = 'http://uche.ogbuji.net#'
m = memory.connection()
LINKS = [
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/title", "Ndewo, Colorado", {"@lang": "en"}],
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/author", "http://uche.ogbuji.net/", {"link/description": "Uche Ogbuji"}],
["http://uche.ogbuji.net/ndewo/", "http://www.w3.org/TR/html5/link-type/see-also", "", {"@label": "Goodreads"}],
["http://uche.ogbuji.net/", "http://www.w3.org/TR/html5/link-type/see-also", "http://uche.ogbuji.net/ndewo/", {}]
]
[ m.add(*l) for l in LINKS ]
ctx = context(U + 'uo', tuple(LINKS[0]), m, base=None, extras=None, variables={'DC', DC})
parsed.evaluate(ctx)
'''

from .ast import *
#from versa.query.ast import *

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'NOT'),
)

def p_query(p):
    'query : expression'
    p[0] = p[1]

def p_conjunction(p):
    'expression : expression OR expression'
    p[0] = conjunction(p[1], p[3])

def p_expression_disj(p):
    'expression : expression AND expression'
    p[0] = disjunction(p[1], p[3])

def p_expression_not(p):
    'expression : NOT expression'
    p[0] = negation(p[1])

def p_expression_stringseq(p):
    '''
    expression : stringseq
    '''
    p[0] = p[1]

def p_expression_constant(p):
    '''
    expression : IDENT
    '''
    p[0] = constant(p[1])

def p_expression_funccall(p):
    '''
    expression : funccall
               | match
    '''
    p[0] = p[1]

def p_expression_var(p):
    '''
    expression : VAR
    '''
    p[0] = variable(p[1])

def p_funccall(p):
    '''
    funccall : IDENT LPAREN arglist RPAREN
    '''
    p[0] = funccall(p[1], p[3])

def p_match(p):
    '''
    match : QUESTION LPAREN matcharglist RPAREN
    '''
    p[0] = funccall(p[1], p[3])

def p_arglist(p):
    '''
    arglist : arg
            | arglist COMMA arg
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])

def p_matcharglist(p):
    '''
    matcharglist : matcharg
                 | matcharglist COMMA matcharg
    '''
    if len(p) == 2:
        p[0] = [p[1]]

    else:
        p[0] = p[1]
        p[0].append(p[3])

def p_arg(p):
    'arg : expression'
    p[0] = p[1]

def p_matcharg(p):
    '''
    matcharg : expression
             | WILD
    '''
    p[0] = p[1]

def p_stringseq(p):
    '''
    stringseq : STRING
              | expression STRING
    '''
    p[0] = stringseq(p[1:])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()
