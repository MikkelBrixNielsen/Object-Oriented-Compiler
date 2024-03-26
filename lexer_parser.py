import ply.lex as lex
import ply.yacc as yacc

import interfacing_parser
import AST
from errors import error_message


# LEXICAL UNITS

reserved = {
    'if': 'IF',             # Not implemented
    'then': 'THEN',         # same 
    'else': 'ELSE',         # same
    'while': 'WHILE',       # same
    'do': 'DO',             # same
    'this': 'THIS',
    'function': 'FUNCTION',
    'class': 'CLASS',
    'new' : 'NEW',
    'return': 'RETURN',
    'print': 'PRINT',
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'char': 'CHAR',
    'instanceOf': 'INSTANCEOF',
    #'string': 'STRING'
}


tokens = (
    'IDENT',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN', 'LCURL', 'RCURL',
    'EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE',
    'ASSIGN', 'COMMA', 'SEMICOL', 'DOT',
) + tuple(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='
t_COMMA = r','
t_DOT = r'\.'
t_SEMICOL = r';'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LCURL = r'{'
t_RCURL = r'}'
t_EQ = r'=='
t_NEQ = r'!='
t_LT = r'<'
t_GT = r'>'
t_LTE = r'<='
t_GTE = r'>='



def t_BOOL(t):
    r'True|False'
    try:
        t.value = str(t.value)
    except ValueError:
        error_message("Lexical Analysis", "type not comapatible with Bool.", t.lexer.lineno)
        t.value = ""

    if (t.value == "True"):
        t.value = 1
    else:
        t.value = 0
    return t

def t_CHAR(t):
    r'\'.?\''
    return t

"""
def t_STRING(t):
    r'\".*\"'
    return t
"""

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENT')    # Check for reserved words
    return t

def t_FLOAT(t):
    r'\d*\.\d+'
    try:
        t.value = float(t.value)
    except ValueError:
        error_message("Lexical Analysis", "Float value too large.", t.lexer.lineno)
        t.value = 0
    if t.value > int('0x7FFFFFFFFFFFFFFF', 16):
        error_message("Lexical Analysis", "Float value too large.", t.lexer.lineno)
        t.value = 0
    return t

def t_INT(t): 
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        error_message("Lexical Analysis",
                      "Integer value too large.",
                      t.lexer.lineno)
        t.value = 0
    if t.value > int('0x7FFFFFFFFFFFFFFF', 16):
        error_message("Lexical Analysis",
                      "Integer value too large.",
                      t.lexer.lineno)
        t.value = 0
    return t


# Ignored characters
t_ignore = " \t\r"  # \r included for the sake of windows users


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


def t_COMMENT(t):
    r'\#.*'
    pass

def t_error(t):
    error_message("Lexical Analysis",
                  f"Illegal character '{t.value[0]}'.",
                  t.lexer.lineno)
    t.lexer.skip(1)


# PARSING RULES AND BUILDING THE AST

precedence = (
    ('right', 'EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

# First production identifies the start symbol
def p_program(t):
    'program : global_body'
    interfacing_parser.the_program = AST.function("int", "global", None, t[1], t.lexer.lineno)


def p_empty(t):
    'empty :'
    t[0] = None


def p_global_body(t):
    'global_body : optional_variables_declaration_list optional_assignment_list function optional_functions_declaration_list optional_class_declaration_list'
    t[0] = AST.global_body(t[1], t[2], t[3], t[4], t[5], t.lexer.lineno)

def p_optional_assignment_list(t):
    '''optional_assignment_list : empty
                                | assignment_list'''
    t[0] = t[1]

def p_assignment_list(t):
    '''assignment_list : statement_assignment
                       | statement_assignment assignment_list'''
    if len(t) == 2:
        t[0] = AST.assignment_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.assignment_list(t[1], t[2], t.lexer.lineno)

# DUE TO STM_LIST BEING OPTIONAL FUNCTIONS NO LONGER HAVE REQUIRED RETURN STATEMENT
# MAKE IT SO RETURN IS REQUIRED BY FUNCTIONS WHICH AREN'T GLOLAL FUNCTION
# FIXME - includes instance syntax and this. syntax the latter should only be allowed in classes though
def p_body(t):
    'body : optional_variables_declaration_list optional_functions_declaration_list optional_statement_list'
    t[0] = AST.body(t[1], t[2], t[3], t.lexer.lineno)

def p_optional_variables_declaration_list(t):
    '''optional_variables_declaration_list : empty
                                           | variables_declaration_list'''
    t[0] = t[1]

def p_variables_declaration_list(t):
    '''variables_declaration_list : TYPE variables_list SEMICOL
                                  | TYPE variables_list SEMICOL variables_declaration_list'''
    if len(t) == 4:
        t[0] = AST.variables_declaration_list(t[1], t[2], None, t.lexer.lineno)
    else:
        t[0] = AST.variables_declaration_list(t[1], t[2], t[4], t.lexer.lineno)


def p_TYPE(t):
    '''TYPE : INT
            | FLOAT
            | BOOL
            | CHAR
            | instance_of''' # FIXME - if the type is ident check if it is a class that has been defined!!
    #      | STRING'''
    t[0] = t[1]

def p_instance_of(t):
    '''instance_of : INSTANCEOF IDENT'''
    t[0] = t[2] + "*"






def p_variables_list(t):
    '''variables_list : IDENT
                      | IDENT COMMA variables_list'''
    if len(t) == 2:
        t[0] = AST.variables_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.variables_list(t[1], t[3], t.lexer.lineno)

def p_optional_class_declaration_list(t):
    '''optional_class_declaration_list : empty
                                       | class_declaration_list'''
    t[0] = t[1]
    
def p_class_declaration_list(t):
    '''class_declaration_list : class_declaration
                              | class_declaration class_declaration_list'''
    if len(t) == 2:
        t[0] = AST.class_declaration_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.class_declaration_list(t[1], t[2], t.lexer.lineno)

# FIXME - Currently cannot extend parent class(') 
# FIXME - CONSTRUCTOR?!?!?!?!?!?!!?!??!?!?!!?!?!?
def p_class_declaration(t):
    '''class_declaration : CLASS IDENT optional_extends LCURL class_descriptor RCURL'''
    t[0] = AST.class_declaration(t[2], t[3], t[5], t.lexer.lineno)

# FIXME - Put class descriptors into symbol table
    # put attributes into the symbol table
    # Generate code for class 
    # Create "this." syntax for accessing instance attributes 
    # Figure out how to do the lookup for finding methods when calling methods on instances
    # Create syntax for recognizing instances 
    # put instances into symbol table
def p_class_descriptor(t):
    '''class_descriptor : optional_attributes_declaration_list optional_methods_declaration_list'''
    t[0] = AST.class_descriptor(t[1], t[2], t.lexer.lineno)

def p_optional_attributes_declaration_list(t):
    '''optional_attributes_declaration_list : empty
                                            | attributes_declaration_list'''
    t[0] = t[1]

def p_attributes_declaration_list(t):
    '''attributes_declaration_list : TYPE attributes_list SEMICOL
                                   | TYPE attributes_list SEMICOL attributes_declaration_list'''
    if len(t) == 4:
        t[0] = AST.attributes_declaration_list(t[1], t[2], None, t.lexer.lineno)
    else:
        t[0] = AST.attributes_declaration_list(t[1], t[2], t[4], t.lexer.lineno)

def p_attributes_list(t):
    '''attributes_list : IDENT
                       | IDENT COMMA attributes_list'''
    if len(t) == 2:
        t[0] = AST.attributes_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.attributes_list(t[1], t[3], t.lexer.lineno)





#same as functions but for classes - so is handled differently
def p_optional_methods_declaration_list(t):
    '''optional_methods_declaration_list : empty
                                         | methods_declaration_list'''
    t[0] = t[1]

def p_methods_declaration_list(t):
    '''methods_declaration_list : method
                                | method methods_declaration_list'''
    if len(t) == 2:
        t[0] = AST.methods_declaration_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.methods_declaration_list(t[1], t[2], t.lexer.lineno)

def p_method(t):
    'method : FUNCTION TYPE IDENT LPAREN optional_parameter_list RPAREN LCURL body RCURL'
    t[0] = AST.method(t[2], t[3], AST.parameter_list(None, "this", t[5], t.lexer.lineno), t[8], t.lexer.lineno)

# FIXME - NOT implemented or even a part of the descriptor definiton 
def p_optional_extends(t):
    '''optional_extends : empty'''
                        # | EXTENDS IDENT''' # EXTENDS IDENT, IDENT, IDENT ...
    t[0] = t[1]











def p_optional_functions_declaration_list(t):
    '''optional_functions_declaration_list : empty
                                           | functions_declaration_list'''
    t[0] = t[1]

def p_functions_declaration_list(t):
    '''functions_declaration_list : function
                                  | function functions_declaration_list'''
    if len(t) == 2:
        t[0] = AST.functions_declaration_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.functions_declaration_list(t[1], t[2], t.lexer.lineno)

#FIXME FIGURE OUT WHY TYPE CANNOT COME BEFORE FUCNTION WITHOUT CAUSING SHIFT/REDUCE CONFLICTS
def p_function(t):
    'function : FUNCTION TYPE IDENT LPAREN optional_parameter_list RPAREN LCURL body RCURL'
    t[0] = AST.function(t[2], t[3], t[5], t[8], t.lexer.lineno)

def p_optional_parameter_list(t):
    '''optional_parameter_list : empty
                               | parameter_list'''
    t[0] = t[1]


def p_parameter_list(t):
    '''parameter_list : TYPE IDENT
                      | TYPE IDENT COMMA parameter_list'''
    if len(t) == 3:
        t[0] = AST.parameter_list(t[1], t[2], None, t.lexer.lineno)
    else:
        t[0] = AST.parameter_list(t[1], t[2], t[4], t.lexer.lineno)


def p_statement(t):
    '''statement : statement_return
                 | statement_print
                 | statement_assignment
                 | statement_ifthenelse
                 | statement_while
                 | statement_compound''' # Don't know what this is probably delete
    t[0] = t[1]


def p_statement_return(t):
    'statement_return : RETURN expression SEMICOL'
    t[0] = AST.statement_return(t[2], t.lexer.lineno)


def p_statement_print(t):
    'statement_print : PRINT LPAREN expression RPAREN SEMICOL'
    t[0] = AST.statement_print(t[3], t.lexer.lineno)


def p_statement_assignment(t):
    'statement_assignment : lhs ASSIGN expression SEMICOL'
    t[0] = AST.statement_assignment(t[1], t[3], t.lexer.lineno)

def p_lhs(t): # make this more uniform so that the other phases have a similar interface to interact with attributes, identifers and whatever else might come
    '''lhs : IDENT
           | THIS DOT IDENT'''
    if len(t) == 2:
        t[0] = t[1]
    else: 
        t[0] = AST.attribute(t[3], t.lexer.lineno)



# FIXME NOT IMPLEMENTED
def p_statement_ifthenelse(t):
    'statement_ifthenelse : IF expression THEN statement ELSE statement'
    t[0] = AST.statement_ifthenelse(t[2], t[4], t[6], t.lexer.lineno)

# FIXME NOT IMPLEMENTED
def p_statement_while(t):
    'statement_while :  WHILE expression DO statement'
    t[0] = AST.statement_while(t[2], t[4], t.lexer.lineno)

# FIXME NOT IMPLEMENTED
def p_statement_compound(t):
    'statement_compound :  LCURL statement_list RCURL'
    t[0] = t[2]


def p_optional_statement_list(t):
    '''optional_statement_list : empty
                               | statement_list'''
    t[0] = t[1]


def p_statement_list(t):
    '''statement_list : statement
                      | statement statement_list'''
    if len(t) == 2:
        t[0] = AST.statement_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.statement_list(t[1], t[2], t.lexer.lineno)

# FIXME NOT IMPLEMENTE groupe / string or expression_attribute 
def p_expression(t):
    '''expression : expression_integer
                  | expression_float
                  | expression_bool
                  | expression_char
                  | expression_identifier
                  | expression_call
                  | expression_binop
                  | expression_attribute
                  | expression_this_attribute
                  | expression_new_instance'''
                 #| expression_string
    t[0] = t[1]

def p_expression_new_instance(t):
    'expression_new_instance : NEW IDENT LPAREN optional_instance_expression_list RPAREN'
    t[0] = AST.expression_new_instance(t[2], t[4], t.lexer.lineno)

def p_optional_instance_expression_list(t):
    '''optional_instance_expression_list : empty
                                         | instance_expression_list'''
    t[0] = t[1]


def p_instance_expression_list(t):
    '''instance_expression_list : expression
                                | expression COMMA instance_expression_list'''
    if len(t) == 2:
        t[0] = AST.instance_expression_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.instance_expression_list(t[1], t[3], t.lexer.lineno)





def p_expression_integer(t):
    'expression_integer : INT'
    t[0] = AST.expression_integer(t[1], t.lexer.lineno)


def p_expression_float(t):
    'expression_float : FLOAT'
    t[0] = AST.expression_float(t[1], t.lexer.lineno)


def p_expression_bool(t):
    'expression_bool : BOOL'
    t[0] = AST.expression_boolean(t[1], t.lexer.lineno)


def p_expression_char(t):
    'expression_char : CHAR'
    t[0] = AST.expression_char(t[1], t.lexer.lineno)

"""
def p_expression_string(t):
    'expression_string : STRING'
    t[0] = AST.expression_string(t[1], t.lexer.lineno)
"""

def p_expression_identifier(t):
    'expression_identifier : IDENT'
    t[0] = AST.expression_identifier(t[1], t.lexer.lineno)


def p_expression_call(t):
    'expression_call : IDENT LPAREN optional_expression_list RPAREN'
    t[0] = AST.expression_call(t[1], t[3], t.lexer.lineno)


# For accessing an attribute on a class 
def p_expression_attribute(t):
    'expression_attribute : IDENT DOT IDENT'
    t[0] = AST.expression_attribute(t[1], t[2])

# For recognizing "this." syntax
def p_expression_this_attribute(t):
    'expression_this_attribute : THIS DOT IDENT'
    t[0] = AST.attribute(t[3], t.lexer.lineno)


def p_expression_binop(t):
    '''expression_binop : expression PLUS expression
                        | expression MINUS expression
                        | expression TIMES expression
                        | expression DIVIDE expression
                        | expression EQ expression
                        | expression NEQ expression
                        | expression LT expression
                        | expression GT expression
                        | expression LTE expression
                        | expression GTE expression'''
    t[0] = AST.expression_binop(t[2], t[1], t[3], t.lexer.lineno)



def p_optional_expression_list(t):
    '''optional_expression_list : empty
                                | expression_list'''
    t[0] = t[1]


def p_expression_list(t):
    '''expression_list : expression
                       | expression COMMA expression_list'''
    if len(t) == 2:
        t[0] = AST.expression_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.expression_list(t[1], t[3], t.lexer.lineno)


def p_error(t):
    try:
        cause = f" at '{t.value}'"
        location = t.lexer.lineno
    except AttributeError:
        cause = " - check for missing closing braces"
        location = "unknown"
    error_message("Syntax Analysis",
                  f"Problem detected{cause}.",
                  location)


# Build the lexer
lexer = lex.lex()

# Build the parser
parser = yacc.yacc()
