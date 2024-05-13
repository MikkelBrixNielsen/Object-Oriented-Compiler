from enum import Enum, auto
from visitors_base import VisitorsBase
from symbols import NameCategory, PRIM_TYPES, _get_identifier
import AST

class Op(Enum):
    """Defines various operations."""
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()

    TYPE = auto()
    RET = auto()

    INDENT = auto()
    IDTL_M = auto()
    IDTL_P = auto()
    
    CALLSTART = auto()
    CALLEND = auto()
    
    CLASS = auto()
    CLASSMID = auto()
    THIS = auto()
    ATTRASSIGN = auto()

    VARLIST = auto()
    PARAMS = auto()
    ASSIGN = auto()
    SIGNATURE = auto()

    START = auto()
    PREMID = auto()
    MID = auto()
    POSTMID = auto()
    END = auto()
    PRINT = auto()
    COMMA = auto()
    RAW = auto()

    ALLOC = auto()
    FREE = auto()
    ALLOCSTART = auto()
    ALLOCEND = auto()
    MEMCHECK = auto()
    DEFAULTVAL = auto()

class LableTable:
    _counter = "0000"
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

    # Inserts lables into table for the give name
    # and returns name with lable
    def insert(self, name):
        lable = self._numgen()
        self._tab[name] = lable
        return name + lable

    # Finds the lable corresponding to name if any exist
    # it returns name with lable otherwise returns name
    def lookup(self, name):
        if name in self._tab:
            return name + self._tab[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return name
        
    # Generates the numbers for the lables 
    def _numgen(self):
        temp = int(LableTable._counter) + 1
        counter = 0
        while temp > 0:
            temp = temp // 10
            counter = counter + 1
        LableTable._counter = "0"*(4-counter) + str(int(LableTable._counter) + 1)
        return "_" + LableTable._counter

class Ins:
    def __init__(self, *args, c=""):
        self.opcode = args[0]
        self.args = args[1:]
        self.comment = c

# Code Generation
class ASTCodeGenerationVisitor(VisitorsBase):
    def __init__(self):
        self._current_scope = None
        self._code = []
        self._lables = LableTable(None)
        self._temp_lables = LableTable(None)
        self._comp_lables = LableTable(None)

    def get_code(self):
        return self._code

    # creates and enters a new scope
    def _enter_new_scope(self, t):
        self._current_scope = t.symbol_table
        self._lables = LableTable(self._lables)
        self._temp_lables = LableTable(self._temp_lables)
        self._comp_lables = LableTable(self._comp_lables)
    
    # exits the current scope and goes to parent scope
    def _exit_current_scope(self, t):
        self._current_scope = self._current_scope.parent
        self._lables = self._lables.parent
        self._temp_lables = self._temp_lables.parent
        self._comp_lables = self._comp_lables.parent

    def _app(self, instruction):
        self._code.append(instruction)

    def preVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.TYPE, t.decl.type))        

    def midVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def preVisit_variables_list(self, t):
        self._app(Ins(Op.VARLIST, self._lables.insert(t.variable), t.next, t.type))

    def preVisit_statement_assignment(self, t):
        self._app(Ins(Op.TYPE, t.rhs.type))
        self._app(Ins(Op.VARLIST, self._temp_lables.insert("TEMP"), None, t.rhs.type))
        self._app(Ins(Op.ASSIGN, ""))
        
    def midVisit_statement_assignment(self, t):
        cnr = t.rhs.__class__.__name__
        if not cnr == "expression_new_instance":
            self._app(Ins(Op.RAW, ";"))
        if  cnr == "expression_new_array":
            self._app(Ins(Op.MEMCHECK, self._temp_lables.lookup("TEMP")))
        if isinstance(t.lhs , str) and not cnr == "expression_new_instance": # If statement assignemnt gets identifier, which is just a string it is responsible for printing it
            self._app(Ins(Op.INDENT))
            self._app(Ins(Op.ASSIGN, self._lables.lookup(t.lhs)))
        cnl = t.lhs.__class__.__name__
        if cnl  == "expression_array_indexing" or cnl == "expression_attribute":
            self._app(Ins(Op.INDENT))
        
    def postVisit_statement_assignment(self, t):
        cn = t.rhs.__class__.__name__ 
        # else the expression will do so automatically when visisted by the visitor
        if not isinstance(t.lhs , str):
            self._app(Ins(Op.ASSIGN, ''))
        if not cn == "expression_new_instance":
            self._app(Ins(Op.RAW, self._temp_lables.lookup("TEMP")))
            self._app(Ins(Op.RAW, ";"))

    def preVisit_statement_return(self, t):
        self._app(Ins(Op.RET))

    def postVisit_statement_return(self, t):
        self._app(Ins(Op.RAW, ";"))

    def preVisit_statement_print(self, t):
        self._app(Ins(Op.START, "printf", None))
        if t.exp:
            self._app(Ins(Op.PRINT, t.exp.type))
        else:
            self._app(Ins(Op.PRINT, "char"))

    def postVisit_statement_print(self, t):
        if not t.exp:
            self._app(Ins(Op.RAW, "' '"))
        self._app(Ins(Op.RAW, ")"))
        self._app(Ins(Op.RAW, ";"))

    def preVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.START, "if ", None))
        self._app(Ins(Op.IDTL_P))

    def preMidVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.PREMID))

    def postMidVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.IDTL_M))
        self._app(Ins(Op.MID, "else"))
        self._app(Ins(Op.IDTL_P))

    def postVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.IDTL_M))
        self._app(Ins(Op.END))

    def preVisit_statement_while(self, t):
        self._app(Ins(Op.START, "while ", None))
        self._app(Ins(Op.IDTL_P))

    def midVisit_statement_while(self, t):
        self._app(Ins(Op.PREMID))

    def postVisit_statement_while(self, t):
        self._app(Ins(Op.IDTL_M))
        self._app(Ins(Op.END))

    def postVisit_expression_integer(self, t):
        self._app(Ins(Op.RAW, t.integer))
        
    def postVisit_expression_float(self, t):
        self._app(Ins(Op.RAW, t.double))

    def postVisit_expression_boolean(self, t):
        self._app(Ins(Op.RAW, t.integer))
    
    def postVisit_expression_char(self, t):
        self._app(Ins(Op.RAW, t.char))
    
    def preVisit_class_declaration(self, t):
        self._current_scope = t.symbol_table
        self._app(Ins(Op.CLASS, t.name))

    def postVisit_class_declaration(self, t):
        self._current_scope = self._current_scope.parent
    
    def midVisit_class_descriptor(self, t):
        self._extend_class(t)

    def preVisit_method(self, t):
        name = t.parent + "_" + t.name
        self._app(Ins(Op.TYPE, t.type))
        labelled_name = t.parent + "_" + self._comp_lables.insert(t.name)
        self._app(Ins(Op.START, " " + labelled_name, t.type))
        self._app(Ins(Op.IDTL_P))
        self._app(Ins(Op.SIGNATURE, t.type, labelled_name, t.par_list))
        t.name = name
        self._enter_new_scope(t)
    
    def midVisit_method(self, t):
        self.midVisit_function(t)

    def postVisit_method(self, t):
        self.postVisit_function(t)

    def preVisit_attributes_declaration_list(self, t):
        self._app(Ins(Op.TYPE, t.decl.type))

    def midVisit_attributes_declaration_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def preVisit_attributes_list(self, t):
        self._app(Ins(Op.VARLIST, t.variable, t.next, t.type))

    def postVisit_expression_identifier(self, t):
        self._app(Ins(Op.RAW, self._lables.lookup(t.identifier)))

    def preVisit_function(self, t):
        if t.scope_level > 0: # functions defined instide the global scope (so all functions excluding the implicit function for global scope)
            name = t.name
            self._app(Ins(Op.TYPE, t.type))
            if not t.name == "main" or t.scope_level > 1:
                name = self._lables.insert(t.name)
            self._app(Ins(Op.START, " " + name, t.type))
            self._app(Ins(Op.IDTL_P))
            self._app(Ins(Op.SIGNATURE, t.type, name, t.par_list))
        self._enter_new_scope(t)
    
    def midVisit_function(self, t):
        if t.name != "global" or t.scope_level > 0:
            self._app(Ins(Op.PREMID))

    def postVisit_function(self, t):
        self._cleanup(t)
        self._exit_current_scope(t)
        if t.name != "global" or t.scope_level > 0:
            self._app(Ins(Op.IDTL_M))
            self._app(Ins(Op.END))

    def preVisit_parameter_list(self, t):
        self._app(Ins(Op.PARAMS, t.type, t.parameter, t.next))

    def preVisit_expression_call(self, t):
        self._app(Ins(Op.RAW, self._lables.lookup(t.name)))
        self._app(Ins(Op.RAW, "("))

    def postVisit_expression_call(self, t):
        self._app(Ins(Op.RAW, ")"))

    def preVisit_statement_call(self, t):
        self._app(Ins(Op.INDENT))
        self.preVisit_expression_call(t)
    
    def postVisit_statement_call(self, t):
        self.postVisit_expression_call(t)
        self._app(Ins(Op.RAW , ";"))

    def preVisit_statement_method(self, t):
        self._app(Ins(Op.INDENT))
        self.preVisit_expression_method(t)

    def postVisit_statement_method(self, t):
        self.postVisit_expression_method(t)
        self._app(Ins(Op.RAW , ";"))
        
    def midVisit_expression_list(self, t):
        self._app(Ins(Op.COMMA, t.next))

    def preVisit_expression_group(self, t):
        self._app(Ins(Op.RAW, "("))

    def postVisit_expression_group(self, t):
        self._app(Ins(Op.RAW, ")"))

    def midVisit_expression_binop(self, t):
        match t.op:
            case "/":
                self._app(Ins(Op.DIV))
            case "*":
                self._app(Ins(Op.MUL))
            case "+":
                self._app(Ins(Op.ADD))
            case "-":
                self._app(Ins(Op.SUB))
            case "==":
                self._app(Ins(Op.EQ))
            case "!=":
                self._app(Ins(Op.NEQ))
            case "<":
                self._app(Ins(Op.LT))
            case ">":
                self._app(Ins(Op.GT))
            case "<=":
                self._app(Ins(Op.LTE))
            case ">=":
                self._app(Ins(Op.GTE))

    def preVisit_expression_new_instance(self, t):
        self._app(Ins(Op.ALLOC, t.struct+"*", t.struct))
        self._app(Ins(Op.MEMCHECK, self._temp_lables.lookup("TEMP")))
        self._app(Ins(Op.INDENT))
        identifier = self._lables.lookup(t.identifier) if t.identifier else ""
        self._app(Ins(Op.ASSIGN, identifier))
        self._app(Ins(Op.RAW, self._temp_lables.lookup("TEMP")))
        self._app(Ins(Op.RAW, ";"))
        self._extension_instance(t)
        self._enter_new_scope(t)

    def preVisit_instance_expression_list(self, t):
        struct = self._lables.lookup(t.struct) 
        self._app(Ins(Op.ATTRASSIGN, struct, t.next, t.param))

    def midVisit_instance_expression_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def postVisit_expression_attribute(self, t):
        cd = None
        var = t.inst
        if t.inst == "this":
            cd = self._current_scope.lookup(self._current_scope.lookup(NameCategory.THIS).cat)
        else:
            cd = self._current_scope.lookup(self._current_scope.lookup(t.inst).type[:-1])
            var = self._lables.lookup(t.inst)

        if self._is_member_in_tuple_list((t.field, t.type), cd.info[0]): # is attr member of cd
            self._app(Ins(Op.RAW, var + "->" + t.field))
        else:
            s = ""
            while not self._is_member_in_tuple_list((t.field, t.type), cd.info[0]) and cd.info[2]:
                ext = cd.info[2][0]
                s = s + self._comp_lables.lookup(ext.lower()) + "->"
                cd = self._current_scope.lookup(ext)
            self._app(Ins(Op.RAW, var + "->" + s + t.field))

    def preVisit_expression_method(self, t):
        prefix = ""
        lablled_inst = ""
        lablled_name = self._comp_lables.lookup(t.name)
        if not t.inst == "this":
            prefix = self._current_scope.lookup(t.inst).info[-1][:-1]
            lablled_inst = self._lables.lookup(t.inst)
        else:
            prefix = self._current_scope.lookup(NameCategory.THIS).type[:-1]

        self._app(Ins(Op.RAW, prefix + "_"))
        self._app(Ins(Op.RAW, lablled_name))
        self._app(Ins(Op.RAW, "("))

        # constructs list of parameters
        args = lablled_inst
        if t.exp_list:
            args += ", "
        self._app(Ins(Op.RAW, args))

    def postVisit_expression_method(self, t):
        self.postVisit_expression_call(t)

    #def preVisit_array_list(self, t):
    #    s = " " + self._lables.lookup(t.variable)
    #    self._app(Ins(Op.ASSIGN, s))
    
    def preVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCSTART, t.type))

    def midVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCEND, t.type[:-2]))

    def preVisit_expression_array_indexing(self, t):
        self._app(Ins(Op.RAW, f"{self._lables.lookup(t.identifier)}["))

    def postVisit_expression_array_indexing(self, t):
        self._app(Ins(Op.RAW, "]"))

    def postVisit_expression_null(self, t):
        self._app(Ins(Op.DEFAULTVAL, t.type))

# auxies
    # FIXME - Ensure that there is a check in regard to if the type of the expression trying to be assigned to the extensions attributes match
    def _extension_instance(self, t):
        current = self._current_scope.lookup(t.struct)
        prev = self._lables.lookup(t.identifier) if t.identifier else ""
        while len(current.info[2]) > 0: # There are more extensions to generate code for 
            name = current.info[2][0].lower()
            var = name + self._numgen()
            type = current.info[2][0] + "*"
            self._app(Ins(Op.TYPE, type))
            self._app(Ins(Op.VARLIST, var, None, type))
            self._app(Ins(Op.RAW, " = "))  
            self._app(Ins(Op.ALLOC, type, type[:-1]))
            self._app(Ins(Op.MEMCHECK, var))

            # Assigns created struct to its parent class
            self._app(Ins(Op.INDENT))
            self._app(Ins(Op.RAW, prev + "->" +self._comp_lables.lookup(name) + " = " + var))
            self._app(Ins(Op.RAW, ";"))
            
            # Instanciate all attributeds for the new instance 
            super = self._current_scope.lookup(current.info[2][0])
            for attr in super.info[0]:
                self._app(Ins(Op.INDENT))
                self._app(Ins(Op.ASSIGN, var + "->" + attr[0]))
                if attr[1] == "int" or attr[1][-2:] == "[]" or attr[1] == "bool":
                    self._app(Ins(Op.RAW, "0"))
                elif attr[1] == "float":
                    self._app(Ins(Op.RAW, "0.0"))
                elif attr[1] == "char":
                    self._app(Ins(Op.RAW, "'\\0'"))
                elif attr[1][-1] == "*":
                    ins1 = self._code.pop()
                    ins2 = self._code.pop()
                    var1 = attr[1][:-1].lower() + self._numgen()
                    self._app(Ins(Op.TYPE, attr[1]))
                    self._app(Ins(Op.VARLIST, var1, None, attr[1]))
                    self._app(Ins(Op.RAW, " = "))  
                    self._app(Ins(Op.ALLOC, attr[1], attr[1][:-1]))
                    self._app(Ins(Op.MEMCHECK, var1))
                    self._app(ins2)
                    self._app(ins1)
                    self._app(Ins(Op.RAW, var1))
                else:
                    print(f"{attr[1]} not implemented in _extension_instance in code generation - please fix")
                self._app(Ins(Op.RAW, ";"))
            prev = var
            current = self._current_scope.lookup(current.info[2][0])

    # FIXME Make it so code is generated for the extensions 
    # FIXME - NOT VERY MAINTAINABLE... I MEAN I PROBABLY DON'T EVEN KNOW WHAT IT IS SUPPOSED TO DO ANYMORE
    # FIXME - Variables inherited should become a special version associated with a "virtual" instance of the extension e.g. Second has attr a, so in Third there will be a Second_a attr and for Seconds get_a Third will return Second_a
    # or it might be possible to include an actual instance of Second in third and just use the methods already defined for second which are in the global scope already
    def _extend_class(self, t):
        cd = self._current_scope.lookup(t.name)
        if len(cd.info[2]) > 0: # len > 0 => extension exists
            for ext in cd.info[2]:
                name = ext.lower()
                self._app(Ins(Op.TYPE, ext))
                self._app(Ins(Op.VARLIST, "*" + self._comp_lables.insert(name), None, None))
                self._app(Ins(Op.RAW, ";"))
        self._app(Ins(Op.CLASSMID, t.name))
        if len(cd.info[3]) > 0: # len > 0 => there are additons to generate code for
            for member in cd.info[3]: # where the additions are located
                if len(member) >= 3: # method
                    self._app(Ins(Op.TYPE, member[1]))
                    self._app(Ins(Op.START, " " + t.name + "_" + self._comp_lables.lookup(member[0]), member[1]))
                    self._app(Ins(Op.PARAMS, t.name, "*this", None))
                    self._app(Ins(Op.PREMID))
                    self._app(Ins(Op.IDTL_P))
                    self._app(Ins(Op.RET))
                    name = cd.info[2][0].lower()
                    self._app(Ins(Op.RAW, cd.info[2][0] + "_" + self._comp_lables.lookup(member[0]) + "(this->" + self._comp_lables.lookup(name) + ")"))
                    self._app(Ins(Op.RAW, ";"))
                    self._app(Ins(Op.IDTL_M))
                    self._app(Ins(Op.END))
                    self._app(Ins(Op.SIGNATURE, member[1], t.name + "_" + self._comp_lables.lookup(member[0]), AST.parameter_list(t.name, "*this", None, t.lineno)))

    def _is_member_in_tuple_list(self, m, tl):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return True
        return False
    
    def _cleanup(self, t):
        if not t.name == "global" or t.scope_level > 0: # clean up for all other user defined functions
            # finds and frees variables in the scope for the current function
            self._find_and_free_in(t.body.stm_list)
        else: # clean up for the global scope encapsulating everything
            self._find_and_free_in(t.body.assignment_list)

    def _find_and_free_in(self, list):
        # Delete the comment bellow if the code to find all variables is deleted 
        # Collects all variables defined in the function
        collected_vars = {}
        # useless code we don't need to collect all variables
        # just collect the once which are assigne something that
        # is not a primitive type
        #decl = t.body.variables_decl
        #while decl:
        #    var = decl.decl
        #    while var:    
        #        # FIXME - CHECK: do all the things have type???
        #        if not (var.type in PRIM_TYPES):
        #                collected_vars[var.variable] = False
        #        var = var.next                         
        #    decl = decl.next
        # looks through statements to see what collected variables are assigned 
        stm = list
        #print(collected_vars, t.name, "START")
        while stm:
            if stm.stm.__class__.__name__ == "statement_assignment":
                val = self._current_scope.lookup_this_scope(stm.stm.lhs) # only looks for variables in the current function scope  
                if val and val.type not in PRIM_TYPES and val.cat != NameCategory.PARAMETER: # primitive types and parameters should not be freed
                    collected_vars[_get_identifier(stm.stm)[0]] = True # _get_identifier(stm.stm)[0] is lhs for statement_assignment 
            stm = stm.next
        #print(collected_vars, t.name, "END")
        # looks through all statemnts and finds all returns statements
        # and places free statements before it
        stm = list
        while stm:
            # FIXME - does not look into sub trees of any given statement
            # only look at whether the current statment is a return statement
            # it should also look if e.g. a if_then_else statement has a return
            # or a while_statement etc.
            if stm.stm.__class__.__name__ == "statement_return":
                ins = self._remove_return_instructions()
                self._free_list(collected_vars)
                self._add_return_instreuctions(ins)
            stm = stm.next

    def _free_list(self, collected_vars):
        # if the flag for a given key is set meaning it has been assigned something 
        # that has been allocated then it should be freed
        for key, flag in collected_vars.items():
            if flag:
                self._app(Ins(Op.FREE, key))
        
    # removes instructions associated with return statement
    def _remove_return_instructions(self):
        ins = []
        current = self._code.pop()
        while current:
            ins.append(current)
            if current.opcode == Op.RET:
                break
            current = self._code.pop()
        return ins[::-1] # reverse the instruction to get them in the order which they should be put back

    # Puts the instructions for return statement back into the code after the free statements
    # ins must be the result from callign _remove_return_instructions
    def _add_return_instreuctions(self, ins):
        [self._app(x) for x in ins]