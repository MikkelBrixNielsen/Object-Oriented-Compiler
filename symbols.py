from enum import Enum, auto
from errors import error_message
from visitors_base import VisitorsBase

PRIM_TYPES = ["int", "float", "bool", "char"]

class NameCategory(Enum):
    """Categories for the names (symbols) collected and inserted into
       the symbol table.
    """
    VARIABLE = auto()   
    PARAMETER = auto()
    FUNCTION = auto()
    CLASS = auto()
    INSTANCE = auto()
    ATTRIBUTE = auto()
    ARRAY = auto()
    THIS = auto()

class Scope(Enum):
    FUNCTION = auto()
    CLASS = auto()


class SymVal():
    """The information for a name (symbol) is its category together ith
       supplementary information.
    """
    def __init__(self, cat, type, level, info, assigned_value = None):
        self.cat = cat
        self.type = type
        self.level = level
        self.info = info
        self.assigned_value = assigned_value

class SymbolTable:
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

    def insert(self, name, value):
        self._tab[name] = value

    # lookup for when not using "this." syntax
    # skips the scope for the class descriptor but not the function defined in cd
    def lookup(self, name):
        # for if we implement classes in classes
        #if (self.parent and (NameCategory.THIS in self._tab and NameCategory.THIS not in self.parent._tab or 
        #    NameCategory.THIS in self._tab and NameCategory.THIS in self.parent._tab and self.parent._tab[NameCategory.THIS].type !=  self._tab[NameCategory.THIS].type)):
        if self.parent and NameCategory.THIS in self._tab and NameCategory.THIS not in self.parent._tab:
           return self.parent.lookup(name)
        elif name in self._tab:
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
    
    def lookup_class(self, name):
        # for if we implement classes in classes
            #if self.parent and (NameCategory.THIS in self._tab and NameCategory.THIS not in self.parent._tab and name in self._tab or 
        #NameCategory.THIS in self._tab and NameCategory.THIS in self.parent._tab and self._tab[NameCategory.THIS].type != self.parent._tab[NameCategory.THIS].type):
        if self.parent and NameCategory.THIS in self._tab and NameCategory.THIS not in self.parent._tab and name in self._tab:
            return self._tab[name]
        elif self.parent:
            return self.parent.lookup_class(name)
        else:
            return None
        
    def lookup_all(self, name):
        if name in self._tab:
            return self._tab[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return None

# Symbol Collection
class ASTSymbolVisitor(VisitorsBase):
    """The visitor implementing the symbol phase."""
    def __init__(self):
        # The main scope does not have a surrounding scope
        self._current_scope = None
        # Have not entered the global scope (level 0) yet:
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
                          f"Missing function {'main'} - please define as first function.",
                          t.lineno)
        elif func.type != "int":
            error_message("Symbol Collection",
                          f"Function 'main' is not of type 'int' but is of type '{t.type}'",
                          t.lineno)
        elif func.par_list != None:
            error_message("Symbol Collection",
                          f"Function 'main' has non-empty parameter list.",
                          t.lineno)
        # Preparing for processing local variables:
        self.variable_offset = 0

    def preMidVisit_global_body(self, t):
        # Recording the number of local variables:
        t.number_of_variables = self.variable_offset

    def preVisit_function(self, t):
        _check_if_user_type_exists(self, t.type, t.lineno)
        if t.name != "global" or self._current_level > -1: # in global scope or deeper
            if self._current_scope.lookup_this_scope(t.name):
                error_message(
                    "Symbol Collection",
                    f"Redeclaration of function '{t.name}' in the same scope.",
                    t.lineno)
            if not t.body.stm_list:
                if not t.body.variables_decl and not t.body.functions_decl: 
                    error_message("Symbol Collection", 
                                  f"The body of the function '{t.name}' is empty.",
                                  t.lineno)
                error_message("Symbol Collection", 
                              f"Missing return statement in function '{t.name}'.",
                              t.lineno)

            current = t.body.stm_list
            while current.next:
                current = current.next
            if not current.stm.__class__.__name__ == "statement_return":
                error_message("Symbol Collection", 
                              f"Missing return statement in function '{t.name}'.",
                              t.lineno)
            exp = current.stm.exp.__class__.__name__
            if exp == "expression_new_array" or "expression_new_instance" == exp:
                error_message("Symnol Collection",
                              f"Object instantiation not allowed as return value in function '{t.name}'.",
                              t.lineno)
                
            self._current_scope.insert(
                t.name, SymVal(NameCategory.FUNCTION, t.type, self._current_level, t))
            
        # Parameters and the body of the function belongs to the inner scope:
        self._current_level += 1
        self._current_scope = SymbolTable(self._current_scope)
        # Saving the current symbol table in the AST for future use:
        t.symbol_table = self._current_scope
        # if function belongs to a class add reference its scope
        if t.__class__.__name__ == "method":
            self._current_scope.insert(
                NameCategory.THIS, SymVal(t.parent, t.parent+"*", self._current_level, []))
        t.scope_level = self._current_level
        # Preparing for the processing of formal parameters:
        self.parameter_offset = 0

    def midVisit_function(self, t):
        # Saving the number of formal parameters after the parameter processing is completed:
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
        _check_if_user_type_exists(self, t.type, t.lineno)
        # if variables_list has a next pass along its type
        if t.next: 
            t.next.type = t.type
        _record_variables(self, t, NameCategory.VARIABLE, t.type)

    # FIXME make class declaration the descriptor and give class 
    # FIXME declaration in lexer a class body instead of descriptor???
    def preVisit_class_declaration(self, t):
        if self._current_scope.lookup_this_scope(t.name):
            error_message("Symbol Collection",
                          f"Redeclaration of class '{t.name}'.",
                          t.lineno)
        if t.name[0].upper() != t.name[0]:
            error_message("Symbol Collection",
                          f"Class names must be capitalized.",
                          t.lineno)
        # FIXME - Eliminate recursive extensions by only allowing a 
        # FIXME - class to extend an already defined class
        extensions = []
        if t.extends:
            extensions.append(t.extends)
            
        # [attributes, methods, extended, methods inherited from extended class]
        info = [[],[], extensions, []]
        self._current_scope.insert(
            t.name, SymVal(NameCategory.CLASS,
                           None,
                           self._current_level,
                           info))
        t.descriptor.name = t.name
        # descriptor of the class belongs to the inner scope:
        self._current_level += 1
        self._current_scope = SymbolTable(self._current_scope)
        # add reference to self
        self._current_scope.insert(
                NameCategory.THIS, SymVal(t.name, t.name+"*", self._current_level, []))
        # Saving the current symbol table in the AST for future use:
        t.symbol_table = self._current_scope
        t.scope_level = self._current_level

        # if class has an extension add the extensions methods and attributes to this class
        if t.extends:
            super = self._current_scope.lookup_all(t.extends)
            if not super:
                error_message("Symbol Collection",
                              f"Class '{t.extends}' not found - maybe used before declaration.",
                              t.lineno)
            if not super.cat == NameCategory.CLASS:
                error_message("Symbol Collection",
                              f"Extension '{t.extends}' is not a class.",
                              t.lineno)
            _extend(self, t, super)

    def postVisit_class_declaration(self, t):
        self._current_scope = self._current_scope.parent
        self._current_level -= 1

    def preVisit_class_descriptor(self, t):
        if t.attributes:
            t.attributes.name = t.name
        if t.methods:
            t.methods.parent = t.name

    def preVisit_attributes_declaration_list(self, t):
        _check_if_user_type_exists(self, t.type, t.lineno)
        t.decl.name = t.name
        t.decl.type = t.type
        if t.next:
            t.next.name = t.name

    # FIXME - (MIGHT BE) useless code that can just be deleted since arrays in classes are just pointers now 
    # so no size is needed and therefore no point in checking whether its is static since the array will be 
    # dynamically allocated later anyway if it is ever initialized.
    #def postVisit_attributes_declaration_list(self, t):
    #    if hasattr(t.decl, "exp"):
    #        if hasattr(t.decl.exp, "size"):
    #            self._check_size_is_static(t.decl.exp.size, t.decl.lineno)

    def preVisit_attributes_list(self, t):
        if t.next:
            t.next.name = t.name 
            t.next.type = t.type
        value = self._current_scope.parent.lookup_this_scope(t.name)
        value.info[0].append((t.variable, t.type))
        _record_variables(self, t, NameCategory.ATTRIBUTE, t.name)

    def preVisit_methods_declaration_list(self, t):
        t.decl.parent = t.parent
        if t.next:
            t.next.parent = t.parent

    def preVisit_method(self, t):
        _check_if_user_type_exists(self, t.type, t.lineno)
        this = self._current_scope.lookup_class(NameCategory.THIS)
        t.parent = this.cat
        t.par_list.type = this.type
        self.preVisit_function(t)
        value = self._current_scope.lookup_all(t.parent)
        value.info[1].append((t.name, t.type, t))

    def midVisit_method(self, t):
        self.midVisit_function(t)
    
    def postVisit_method(self, t):
        self.postVisit_function(t)

    def preVisit_statement_assignment(self, t):
        cn = t.lhs.__class__.__name__
        name = t.lhs
        lhs = t.lhs
        if cn == "expression_attribute":
            if t.lhs.inst == "this":
                name = t.lhs.field
            else:    
                name = t.lhs.inst
            lhs = self._current_scope.lookup_class(name)
        elif cn == "expression_array_indexing":
           # FIXME - if array indexing is possible on array attributes then something link "expression_attribute" should happen
           name = t.lhs.identifier
           lhs = self._current_scope.lookup(name)
        else:
            lhs = self._current_scope.lookup(name)

        if not lhs:
            error_message("Symbol Collection",
                          f"Assignment before declaration of '{name}",
                          t.lineno)
        
        if t.rhs.__class__.__name__ == "expression_new_instance":
            t.rhs.identifier = t.lhs
        if t.rhs.__class__.__name__ == "expression_new_array":
           if lhs.cat == NameCategory.ARRAY:
                error_message("Symbol Collection",
                              f"Cannot assign new array to already initialized array - perhaps use indexing to change each element.",
                              t.rhs.lineno)
           lhs.size = t.rhs.size
  
    def postVisit_statement_return(self, t):
        cn = t.exp.__class__.__name__
        _check_if_initialized(self, cn, t.exp)

    def preVisit_statement_print(self, t):
        cn = t.exp.__class__.__name__
        #_check_if_initialized(cn, t.exp)
        if cn == "expression_new_instance":
            error_message("Symbol Collection",
                          f"Object initialization not allowed in print statement",
                          t.lineno)

    def preVisit_expression_new_instance(self, t):
        t.symbol_table = self._current_scope # adds sym_table to instances
        if t.params:
            t.params.struct = t.identifier

    # FIXME - Assigning type to parameters might need more complex logic to correctly identify the differet type of parameters there exit and giving them the correct type
    def preVisit_instance_expression_list(self, t):
        cn = t.exp.__class__.__name__
        if cn == "expression_new_instance":
            error_message("Symbol Collection",
                          f"Anonymous instantiation of class '{t.exp.struct}' not allowed.",
                          t.exp.lineno)
        elif cn == "expression_new_array":
            error_message("Symbol Collection",
                          f"Anonymous instantiation of '{t.exp.type}' array not allowed.",
                          t.exp.lineno)
        # Assigns the struct each expression relates to
        if t.next:
            t.next.struct = t.struct
        if cn == "expression_null":
            return
        # Assigns types to the parameters
        if cn not in ["expression_integer", "expression_char", "expression_bool", "expression_float"]:
            val = None
            if cn == "expression_method" or cn == "expression_attribute":
                val = self._current_scope.lookup_class(_get_identifier(t.exp))
            else:    
                val = self._current_scope.lookup(_get_identifier(t.exp))
            if val:
                t.exp.type = val.type

    # Probably just delete this since it is taken care of through variables_declaration_list now but mention it existed in the report
    #def preVisit_array_list(self, t):
    #    if t.name: # the array is an attribute on a class if it has a name
    #        value = self._current_scope.lookup(t.name)
    #        value.info[0].append((t.variable, t.type))
    #    _record_variables(t, NameCategory.ARRAY, t.exp.size, t.name) #t.exp.data, t.exp.size, t.name)

    def postVisit_expression_array_indexing(self, t):
        val = self._current_scope.lookup(t.identifier)
        if not val:
            error_message("Symobl Collection",
                          f"Array access before declaration of '{t.identifier}'.",
                          t.lineno)
        t.type = val.type

    def preVisit_expression_new_array(self, t):
        cn = t.size.__class__.__name__
        if cn == "expression_binop" and t.size.op in ["<", ">", "<=", ">=", "==", "!="]:
            error_message("Symobl Collection",
                          f"Array access using result of comparison not allowed.",
                          t.lineno)
        elif cn == "expression_char":
             error_message("Symobl Collection",
                          f"Array access using a character not allowed.",
                          t.lineno)
        elif cn == "expression_new_instance":
             error_message("Symobl Collection",
                          f"Array access using result of creating new instance not allowed.",
                          t.lineno)
        elif cn == "expression_new_array":
             error_message("Symobl Collection",
                          f"Array access using result of creating new array not allowed.",
                          t.lineno)
        #elif t.type[-1:] == "*":
        #     error_message("Symobl Collection",
        #                  f"Array does not support user defiend type '{t.type[:-1]}'.",
        #                  t.lineno)    
    # TODO - Make this.<attr> syntax to differentiate between global variable, parameters, and class attributes
    # TODO - Make new syntax work to create class instances 
    # TODO - make identifier.<attr>/<func> syntax work for calling attributes / functions for a specific instace

# Auxiliaries
def _record_variables(self, t, *args): # maybe don't need to be *args
    # AUX: Recording local variable names in the symbol table:
    if self._current_scope.lookup_this_scope(t.variable):
        error_message(
            "Symbol Collection",
            f"Redeclaration of '{t.variable}' in the same scope.",
            t.lineno)
 
    self._current_scope.insert(
        t.variable, SymVal(args[0],
                           t.type,
                           self._current_level,
                           [self.variable_offset] + [x for x in args]))
    self.variable_offset += 1

# Extends class with appropriate methods and attributes 
def _extend(self, t, ext):
    this = self._current_scope.lookup(t.name)
    if not this:
        error_message("Symbol Collection",
                    f"class '{t.name}' not found.",
                    t.lineno)
    new_additions = []
    for i in range(len(ext.info)):
        for new_elem in ext.info[i]:
            found = False
            if i != 2: # Tuple comparison for attributes, methods, and extensions
                for elem in this.info[i]:
                    if new_elem[0] == elem[0]:
                        found = True
                        break # new_elem was found, so stop looking for it
            if not found and i != 2:
                new_additions.append(new_elem)
    this.info[3] += new_additions
    
def _check_if_initialized(self, cn, t):
    if (not cn == "expression_integer" and not cn == "expression_float" and 
        not cn == "expression_boolean" and not cn == "expression_char"):
        ident = _get_identifier(t)
        val = None
        if cn == "expression_binop" or cn == "statement_assignment":
            _check_if_initialized(self, t.lhs.__class__.__name__, t.lhs)
            _check_if_initialized(self, t.rhs.__class__.__name__, t.rhs)
            # if neither of lhs or rhs fails the initialization check then
            # there exists a value
            val = True
        elif cn == "expression_method" or cn == "expression_attribute":
            val = self._current_scope.lookup(t.inst)
            if t.inst == "this":
                val = self._current_scope.lookup_class(t.field)
            if not val:
                val = _lookup_in_extensions(self, t, t.__class__.__name__)
        elif cn == "expression_new_instance" or cn == "expression_new_array":
            val = True
        elif cn in ["str", "int", "float", "char", "bool"]:
            val = True
        else:
            val = self._current_scope.lookup(ident)
        if not val:
            if ident == "this":
                ident = ident + "." + t.field
            error_message("Symbol Collection",
                            f"Accessing variable / function '{ident}' before initialization.",
                            t.lineno)
            
def _lookup_in_extensions(self, t, cat):
    idx = 0 if cat == "expression_attribute" else 1
    val = self._current_scope.lookup_all(t.inst)
    cd = self._current_scope.lookup_all(val.type[:-1])
    while True:
        for member in cd.info[idx]:
            if member[0] == t.field:
                return member
        if not len(cd.info[2]) > 0:
            break
        cd = self._current_scope.lookup_all(cd.info[2][0])
    return None

def _get_identifier(t):
    match t.__class__.__name__:
        case "expression_integer" | "expression_boolean":
            return t.integer
        case "expression_float":
            return t.double
        case "expression_char":
            return t.char
        case "expression_identifier" | "expression_array_indexing":
            return t.identifier
        case "expression_call" | "expression_method":
            return t.name
        case "expression_binop":
            return (_get_identifier(t.lhs), _get_identifier(t.rhs))
        case "statement_assignment":
            return(t.lhs if isinstance(t.lhs, str) else _get_identifier(t.lhs), _get_identifier(t.rhs))
        case "statement_print" | "statement_return" | "expression_group":
            return _get_identifier(t.exp)
        case "expression_attribute":
            return t.inst#, t.field
        case "expression_new_instance" | "expression_new_array":
            return None
        case _:
            error_message("Symbol Collection",
                          f"_get_identifier does not implement {t.__class__.__name__}",
                          t.lineno)
            
# if code for array list is deleted then delete this as well but mention in report that this was something that existed                
#def _check_size_is_static(self, t, lineno):
#    match t.__class__.__name__:
#        case "expression_integer" | "expression_bool" | "expression_binop": # only allow non-variable parameters as the size on class attribute arrays when initialzing them
#            pass
#        case "expression_float" | "expression_char":
#            error_message("Symbol Collection",
#                          "Non-integer types cannot be used to initialize the size of an array.",
#                          lineno)
#        case _:
#            error_message("Symbol Collection",
#                          "variable-sized parameters cannot be used to initialize arrays in classes.",
#                          lineno)
                
# check whether a type given is defined            
def _check_if_user_type_exists(self, type, lineno):
    base_type = type.replace("[]", "").replace("*", "")
    if base_type not in PRIM_TYPES and not self._current_scope.lookup_all(base_type):
        error_message("Symbol Collection",
                        f"Type or class '{base_type}' not defined.",
                        lineno)