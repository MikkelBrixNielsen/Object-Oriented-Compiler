import ply.lex as lex
import ply.yacc as yacc

import interfacing_parser
import AST
from errors import error_message

# Reserved keywords in C
reserved_in_c = (
    "auto",  "double", "int", "struct", "break", "else", "long", 
    "switch", "case", "enum", "register", "typedef", "char",
    "extern", "return", "union", "const", "float", "short", 
    "unsigned", "continue", "for", "signed", "void", "default",
    "goto", "sizeof", "volatile", "do", "if", "static", "while", 
    "_Bool", "_Complex", "_Imaginary",
)

# LEXICAL UNITS
reserved = {
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
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
    'array': 'ARRAY',
    'instanceOf': 'INSTANCEOF',
    'extends': 'EXTENDS',
    'Null': 'NULL',
}

tokens = (
    'IDENT', 
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN', 'LCURL', 'RCURL',
    'RBRAC', 'LBRAC',
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
t_LBRAC = r'\['
t_RBRAC = r'\]'
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

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    if t.value in reserved_in_c and t.value not in reserved:
          error_message("Lexical Analysis", f"Identifier '{t.value}' is a reserved keyword.", t.lexer.lineno)
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
    'global_body : optional_variables_declaration_list optional_assignment_list optional_class_declaration_list function optional_functions_declaration_list'
    t[0] = AST.global_body(t[1], t[2], t[3], t[4], t[5], t.lexer.lineno)

def p_optional_assignment_list(t):
    '''optional_assignment_list : empty
                                | assignment_list'''
    t[0] = t[1]

def p_assignment_list(t):
    '''assignment_list : statement_assignment SEMICOL
                       | statement_assignment SEMICOL assignment_list'''
    if len(t) == 3:
        t[0] = AST.assignment_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.assignment_list(t[1], t[3], t.lexer.lineno)

def p_body(t):
    'body : optional_variables_declaration_list optional_functions_declaration_list optional_statement_list'
    t[0] = AST.body(t[1], t[2], t[3], t.lexer.lineno)

def p_method_body(t):
    'method_body : optional_variables_declaration_list optional_methods_declaration_list optional_statement_list'
    t[0] = AST.body(t[1], t[2], t[3], t.lexer.lineno)

def p_optional_variables_declaration_list(t):
    '''optional_variables_declaration_list : empty
                                           | variables_declaration_list'''
    t[0] = t[1]

def p_variables_declaration_list(t):
    '''variables_declaration_list : FT variables_list SEMICOL
                                  | FT variables_list SEMICOL variables_declaration_list'''
    if len(t) == 4:
        t[0] = AST.variables_declaration_list(t[1], t[2], None, t.lexer.lineno)
    else:
        t[0] = AST.variables_declaration_list(t[1], t[2], t[4], t.lexer.lineno)

def p_TYPE(t):
    '''TYPE : INT
            | FLOAT
            | BOOL
            | CHAR
            | instance_of'''
    t[0] = t[1]

def p_instance_of(t):
    '''instance_of : INSTANCEOF LPAREN IDENT RPAREN'''
    t[0] = t[3] + "*"

def p_array(t):
    '''array : TYPE ARR'''
    t[0] = t[1] + t[2]

def p_ARR(t):
    '''ARR : LBRAC RBRAC
           | LBRAC RBRAC ARR'''
    if len(t) == 3:
        t[0] = "[]"
    else:
        t[0] = "[]" + t[3]

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

def p_class_declaration(t):
    '''class_declaration : CLASS IDENT optional_extends LCURL class_descriptor RCURL'''
    t[0] = AST.class_declaration(t[2], t[3], t[5], t.lexer.lineno)

def p_class_descriptor(t):
    '''class_descriptor : optional_attributes_declaration_list optional_methods_declaration_list'''
    t[0] = AST.class_descriptor(t[1], t[2], t.lexer.lineno)

def p_optional_attributes_declaration_list(t):
    '''optional_attributes_declaration_list : empty
                                            | attributes_declaration_list '''
    t[0] = t[1]

def p_attributes_declaration_list(t):
    '''attributes_declaration_list : FT attributes_list SEMICOL
                                   | FT attributes_list SEMICOL attributes_declaration_list'''
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
    'method : FUNCTION FT IDENT LPAREN optional_parameter_list RPAREN LCURL method_body RCURL'
    t[0] = AST.method(t[2], t[3], AST.parameter_list(None, "this", t[5], t.lexer.lineno), t[8], t.lexer.lineno)

def p_optional_extends(t):
    '''optional_extends : empty
                        | EXTENDS IDENT'''
    if len(t) == 2:
        t[0] = t[1]
    else:
        t[0] = t[2] 

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

def p_function(t):
    'function : FUNCTION FT IDENT LPAREN optional_parameter_list RPAREN LCURL body RCURL'
    t[0] = AST.function(t[2], t[3], t[5], t[8], t.lexer.lineno)

def p_FT(t):
    '''FT : TYPE 
          | array'''
    t[0] = t[1]

def p_optional_parameter_list(t):
    '''optional_parameter_list : empty
                               | parameter_list'''
    t[0] = t[1]

def p_parameter_list(t):
    '''parameter_list : FT IDENT
                      | FT IDENT COMMA parameter_list'''
    if len(t) == 3:
        t[0] = AST.parameter_list(t[1], t[2], None, t.lexer.lineno)
    else:
        t[0] = AST.parameter_list(t[1], t[2], t[4], t.lexer.lineno)

def p_statement(t):
    '''statement : statement_return SEMICOL
                 | statement_print SEMICOL
                 | statement_assignment SEMICOL
                 | statement_ifthenelse
                 | statement_while
                 | statement_call SEMICOL
                 | statement_this_method SEMICOL
                 | statement_method SEMICOL
                 | statement_compound'''
    t[0] = t[1]

def p_statement_return(t):
    'statement_return : RETURN expression'
    t[0] = AST.statement_return(t[2], t.lexer.lineno)

def p_statement_print(t):
    '''statement_print : PRINT LPAREN expression RPAREN
                       | PRINT LPAREN RPAREN'''
    if len(t) == 5:
        t[0] = AST.statement_print(t[3], t.lexer.lineno)
    else:
        t[0] = AST.statement_print(None, t.lexer.lineno)
def p_statement_assignment(t):
    'statement_assignment : lhs ASSIGN expression'
    t[0] = AST.statement_assignment(t[1], t[3], t.lexer.lineno)

def p_lhs(t):
    '''lhs : IDENT
           | THIS DOT IDENT
           | IDENT DOT IDENT
           | expression_array_indexing''' 
    if len(t) == 2:
        t[0] = t[1]
    else: 
        t[0] = AST.expression_attribute(t[1], t[3], t.lexer.lineno)

def p_statement_ifthenelse(t):
    'statement_ifthenelse : IF expression THEN statement ELSE statement'
    t[0] = AST.statement_ifthenelse(t[2], t[4], t[6], t.lexer.lineno)

def p_statement_while(t):
    'statement_while :  WHILE expression DO statement'
    t[0] = AST.statement_while(t[2], t[4], t.lexer.lineno)

def p_statement_compound(t):
    'statement_compound :  LCURL statement_list RCURL'
    t[0] = t[2]

def p_statement_call(t):
    'statement_call : IDENT LPAREN optional_expression_list RPAREN'
    t[0] = AST.statement_call(t[1], t[3], t.lexer.lineno)

def p_statement_method(t):
    '''statement_method : IDENT DOT IDENT LPAREN optional_expression_list RPAREN'''
    # FIXME             | IDENT DOT statement_method'''
    t[0] = AST.statement_method(t[1], t[3], t[5], t.lexer.lineno)

def p_statement_this_method(t):
    '''statement_this_method : THIS DOT IDENT LPAREN optional_expression_list RPAREN'''
    # FIXME                  | THIS DOT statement_method'''
    t[0] = AST.statement_method(t[1], t[3], t[5], t.lexer.lineno)

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
                  | expression_method
                  | expression_this_method
                  | expression_new_instance
                  | expression_new_array
                  | expression_array_indexing
                  | expression_group'''
                  #| unary_minus_integer
                  #| unary_minus_float'''
    t[0] = t[1]

#def p_unary_minus_integer(t):
#    '''unary_minus_integer : MINUS expression_integer'''
#    t[0] = AST.expression_binop(AST.expression_integer(0, t.lexer.lineno), t[1], t[2], t.lexer.lineno)

#def p_unary_minus_float(t):
#    '''unary_minus_float : MINUS expression_float'''
#    t[0] = AST.expression_binop(AST.expression_integer(0, t.lexer.lineno), t[1], t[2], t.lexer.lineno)

def p_expression_array_indexing(t):
    '''expression_array_indexing : IDENT LBRAC expression RBRAC 
                                 | expression_array_indexing LBRAC expression RBRAC
                                 | expression_this_attribute LBRAC expression RBRAC
                                 | expression_attribute LBRAC expression RBRAC'''
    t[0] = AST.expression_array_indexing(t[1], t[3], t.lexer.lineno)

def p_expression_new_array(t):
    'expression_new_array : NEW ARRAY LPAREN FT COMMA expression RPAREN' 
    t[0] = AST.expression_new_array(t[4], t[6], t.lexer.lineno)

def p_expression_new_instance(t):
    'expression_new_instance : NEW IDENT LPAREN optional_instance_expression_list RPAREN'
    t[0] = AST.expression_new_instance(t[2], t[4], t.lexer.lineno)

def p_optional_instance_expression_list(t):
    '''optional_instance_expression_list : empty
                                         | instance_expression_list'''
    t[0] = t[1]

def p_instance_expression_list(t):
    '''instance_expression_list : expression
                                | expression COMMA instance_expression_list
                                | expression_null
                                | expression_null COMMA instance_expression_list'''
    if len(t) == 2:
        t[0] = AST.instance_expression_list(t[1], None, t.lexer.lineno)
    else:
        t[0] = AST.instance_expression_list(t[1], t[3], t.lexer.lineno)

def p_expression_null(t):
    'expression_null : NULL'
    t[0] = AST.expression_null(t[1], t.lexer.lineno)

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

def p_expression_identifier(t):
    'expression_identifier : IDENT'
    t[0] = AST.expression_identifier(t[1], t.lexer.lineno)

def p_expression_call(t):
    'expression_call : IDENT LPAREN optional_expression_list RPAREN'
    t[0] = AST.expression_call(t[1], t[3], t.lexer.lineno)

def p_expression_this_attribute(t):
    'expression_this_attribute : THIS DOT IDENT'
    # FIXME                    | THIS DOT expression_attribute # to be able to do instance access on an already accessed instance variable aka attribute

    t[0] = AST.expression_attribute(t[1], t[3], t.lexer.lineno)

def p_expression_attribute(t):
    'expression_attribute : IDENT DOT IDENT'
    # FIXME               | IDENT DOT expression_attribute # to be able to do instance access on an already accessed instance variable aka attribute
    t[0] = AST.expression_attribute(t[1], t[3], t.lexer.lineno)

def p_expression_this_method(t):
    'expression_this_method : THIS DOT IDENT LPAREN optional_expression_list RPAREN'
    t[0] = AST.expression_method(t[1], t[3], t[5], t.lexer.lineno)

def p_expression_method(t):
    'expression_method : IDENT DOT IDENT LPAREN optional_expression_list RPAREN'
    t[0] = AST.expression_method(t[1], t[3], t[5], t.lexer.lineno)

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

def p_expression_group(t):
    'expression_group : LPAREN expression RPAREN'
    t[0] = AST.expression_group(t[2], t.lexer.lineno)

def p_error(t):
    try:
        cause = f" at '{t.value}'"
        location = t.lexer.lineno
    except AttributeError:
        cause = " - check for missing closing braces or main function"
        location = "unknown"
    error_message("Syntax Analysis",
                  f"Problem detected{cause}.",
                  location)

# Build the lexer
lexer = lex.lex()

# Build the parser
parser = yacc.yacc()