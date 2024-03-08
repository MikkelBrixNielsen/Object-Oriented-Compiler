from enum import Enum, auto
from errors import error_message
from visitors_base import VisitorsBase


class NameCategory(Enum):
    """Categories for the names (symbols) collected and inserted into
       the symbol table.
    """
    VARIABLE = auto()   
    PARAMETER = auto()
    FUNCTION = auto()
    CLASS = auto()
    INSTANCE = auto()


class SymVal():
    """The information for a name (symbol) is its category together with
       supplementary information.
    """
    def __init__(self, cat, type, level, info):
        self.cat = cat
        self.type = type
        self.level = level
        self.info = info


class SymbolTable:
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

    def insert(self, name, value):
        self._tab[name] = value

    def lookup(self, name):
        if name in self._tab:
            return self._tab[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return None

    def lookup_this_scope(self, name):
        if name in self._tab:
            return self._tab[name]
        else:
            return None


# Symbol Collection

class ASTSymbolVisitor(VisitorsBase):
    """The visitor implementing the symbol phase."""
    def __init__(self):
        # The main scope does not have a surrounding scope
        self._current_scope = None
        # Have not entered the main scope (level 0) yet:
        self._current_level = -1

    def preVisit_body(self, t):
        # Preparing for processing local variables:
        self.variable_offset = 0

    def preMidVisit_body(self, t):
        # Recording the number of local variables:
        t.number_of_variables = self.variable_offset

    def preVisit_global_body(self, t):
        func = t.main_function
        if func.name != "main":
            error_message("Symbol Collection", 
                          f"missing function {'main'} - please define.",
                          t.lineno)
        elif func.type != "int":
            error_message("Symbol Collection",
                          f"main function is not of type 'int' but is of type 'float'",
                          t.lineno)
        elif func.par_list != None:
            error_message("Symbol Collection",
                          f"parameter list not empty",
                          t.lineno)
        # Preparing for processing local variables:
        self.variable_offset = 0

    def preMidVisit_global_body(self, t):
        # Recording the number of local variables:
        t.number_of_variables = self.variable_offset

    def preVisit_function(self, t):
        # The name of the function belongs to the surrounding scope:
        if t.name != "global":
            if self._current_scope.lookup_this_scope(t.name):
                error_message(
                    "Symbol Collection",
                    f"Redeclaration of function '{t.name}' in the same scope.",
                    t.lineno)
            self._current_scope.insert(
                t.name, SymVal(NameCategory.FUNCTION, t.type, self._current_level, t))
        # Parameters and the body of the function belongs to the inner scope:
        self._current_level += 1
        self._current_scope = SymbolTable(self._current_scope)
        # Saving the current symbol table in the AST for future use:
        t.symbol_table = self._current_scope
        t.scope_level = self._current_level
        # Preparing for the processing of formal parameters:
        self.parameter_offset = 0

    def midVisit_function(self, t):
        # Saving the number of formal parameters after the parameter
        # processing is completed:
        t.number_of_parameters = self.parameter_offset

    def postVisit_function(self, t):
        # Returning to the outer scope after function processing is completed:
        self._current_scope = self._current_scope.parent
        self._current_level -= 1

    def preVisit_parameter_list(self, t):
        # Recording formal parameter names in the symbol table:
        if self._current_scope.lookup_this_scope(t.parameter):
            error_message(
                "Symbol Collection",
                f"Redeclaration of '{t.parameter}' in the same scope.",
                t.lineno)

        self._current_scope.insert(
            t.parameter, SymVal(NameCategory.PARAMETER,
                                t.type,
                                self._current_level,
                                self.parameter_offset))
        self.parameter_offset += 1

    def preVisit_variables_declaration_list(self, t):
        # Pass along its type to the variable declaration lists
        t.decl.type = t.type

    def preVisit_variables_list(self, t):
        # if variables_list has a next pass along its type
        if t.next: 
            t.next.type = t.type

        # Recording local variable names in the symbol table:
        if self._current_scope.lookup_this_scope(t.variable):
            error_message(
                "Symbol Collection",
                f"Redeclaration of '{t.variable}' in the same scope.",
                t.lineno)
 
        self._current_scope.insert(
            t.variable, SymVal(NameCategory.VARIABLE,
                               t.type,
                               self._current_level,
                               self.variable_offset))
        self.variable_offset += 1

    def postVisit_expression_identifier(self, t):
        value = self._current_scope.lookup(t.identifier)
        if not value:
            error_message("Symbol Collection",
                          f"Identifier '{t.identifier}' not found.",
                          t.lineno)
        t.type = value.type

    def preVisit_class_declaration(self, t):
        value = self._current_scope.lookup_this_scope(t.name)
        if value:
            error_message("Symbol Collection",
                          f"Redeclaration of class '{t.name}'.",
                          t.lineno)
        self._current_scope.insert(
            t.name, SymVal(NameCategory.CLASS,
                           None,
                           self._current_level,
                           t))
    
    # Make function part of the structs in C code 
    # Make this.<attr> syntax to differentiat between global variable, parameters, and class attributes
    # Make new syntax work to create class instances 
    # make identifier.<attr>/<func> syntax work for calling attributes / functions for a specific instace
    """
    Expression_attribute
    Figure out how the extends part of a class declaration is going to work
    Class_declaration
    Classes in symbol table
    """


