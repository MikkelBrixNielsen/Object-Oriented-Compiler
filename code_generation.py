from enum import Enum, auto
from singleton_decorator import singleton
from visitors_base import VisitorsBase
from symbols import NameCategory
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
    ALLOCSTART = auto()
    ALLOCEND = auto()
    MEMCHECK = auto()

class Ins:
    """Representation of an instruction with an opcode, a number of
       arguments, and an optional comment.
    """
    def __init__(self, *args, c=""):
        self.opcode = args[0]
        self.args = args[1:]
        self.comment = c

# Code Generation
class ASTCodeGenerationVisitor(VisitorsBase):
    """Implements the intermediate code generation from the AST."""
    def __init__(self):
        self._counter = "0000"
        self._current_scope = None
        self._code = []
        self._lables = {}

    def _numgen(self):
        temp = int(self._counter) + 1
        counter = 0
        while temp > 0:
            temp = temp // 10
            counter = counter + 1
        self._counter = "0"*(4-counter) + str(int(self._counter) + 1)
        return "_" + self._counter

    def get_code(self):
        return self._code

    def _app(self, instruction):
        self._code.append(instruction)

    def preVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.TYPE, t.decl.type))        

    def midVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def preVisit_variables_list(self, t):
        self._lables[t.variable] = self._numgen()
        self._app(Ins(Op.VARLIST, t.variable + self._lables[t.variable], t.next, t.type))

    def preVisit_statement_assignment(self, t):
        self._lables["TEMP"] = self._numgen()
        self._app(Ins(Op.TYPE, t.rhs.type))
        self._app(Ins(Op.VARLIST, "TEMP" + self._lables["TEMP"], None, t.rhs.type))
        self._app(Ins(Op.ASSIGN, ""))
        
    def midVisit_statement_assignment(self, t):
        cn = t.rhs.__class__.__name__
        if not cn == "expression_new_instance":
            self._app(Ins(Op.RAW, ";"))
        if  cn == "expression_new_array":
            self._app(Ins(Op.MEMCHECK, "TEMP" + self._lables["TEMP"]))
        if isinstance(t.lhs , str) and not cn == "expression_new_instance": # If statement assignemnt gets identifier, which is just a string it is responsible for printing it
            self._app(Ins(Op.INDENT))
            self._app(Ins(Op.ASSIGN, t.lhs + self._lables[t.lhs]))
        if t.lhs.__class__.__name__  == "expression_array_indexing":
            self._app(Ins(Op.INDENT))
        
    def postVisit_statement_assignment(self, t):
        cn = t.rhs.__class__.__name__ 
        # else the expression will do so automatically when visisted by the visitor
        if not isinstance(t.lhs , str):
            self._app(Ins(Op.ASSIGN, ''))
        if not cn == "expression_new_instance":
            self._app(Ins(Op.RAW, "TEMP" + self._lables["TEMP"]))
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
        self._current_scope = t.symbol_table
        if not t.name == "global":
            self._app(Ins(Op.TYPE, t.type))
            temp = name
            if not name == "main":
                self._lables[t.name] = self._numgen()
                temp = name + self._lables[t.name]
            self._app(Ins(Op.START, " " + temp, t.type))
            self._app(Ins(Op.IDTL_P))
            self._app(Ins(Op.SIGNATURE, t.type, temp, t.par_list))
        t.name = name
    
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
        self._app(Ins(Op.RAW, t.identifier + self._lables[t.identifier]))

    def preVisit_function(self, t):
        self._current_scope = t.symbol_table
        if not t.name == "global":
            name = t.name
            self._app(Ins(Op.TYPE, t.type))
            if not t.name == "main":
                self._lables[t.name] = self._numgen()
                name = name + self._lables[t.name]
            self._app(Ins(Op.START, " " + name, t.type))
            self._app(Ins(Op.IDTL_P))
            self._app(Ins(Op.SIGNATURE, t.type, name, t.par_list))
    
    def midVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.PREMID))

    def postVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.IDTL_M))
            self._app(Ins(Op.END))
        self._current_scope = self._current_scope.parent

    def preVisit_parameter_list(self, t):
        self._app(Ins(Op.PARAMS, t.type, t.parameter, t.next))

    def preVisit_expression_call(self, t):
        self._app(Ins(Op.RAW, t.name + self._lables[t.name]))
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
        self._current_scope = t.symbol_table
        self._app(Ins(Op.ALLOC, t.struct+"*", t.struct))
        self._app(Ins(Op.MEMCHECK, "TEMP" + self._lables["TEMP"]))
        self._app(Ins(Op.INDENT))
        self._app(Ins(Op.ASSIGN, t.identifier + self._lables[t.identifier]))
        self._app(Ins(Op.RAW, "TEMP" + self._lables["TEMP"]))
        self._app(Ins(Op.RAW, ";"))
        self._extension_instance(t)

    def preVisit_instance_expression_list(self, t):
        self._app(Ins(Op.ATTRASSIGN, t.struct + self._lables[t.struct], t.next, t.param))

    def midVisit_instance_expression_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def postVisit_expression_attribute(self, t):
        cd = None
        var = t.inst
        if t.inst == "this":
            cd = self._current_scope.lookup(self._current_scope.lookup(NameCategory.THIS).cat)
        else:
            cd = self._current_scope.lookup(self._current_scope.lookup(t.inst).type[:-1])
            var = var + self._lables[t.inst]

        if self._is_member_in_tuple_list((t.field, t.type), cd.info[0]): # is attr member of cd
            self._app(Ins(Op.RAW, var + "->" + t.field))
        else:
            self._app(Ins(Op.RAW, var + "->" + cd.info[2][0].lower() + "->" + t.field))

    def preVisit_expression_method(self, t):
        prefix = ""
        inst_lable = ""
        name_lable = self._lables[t.name]
        if not t.inst == "this":
            prefix = self._current_scope.lookup(t.inst).info[-1][:-1]
            inst_lable = self._lables[t.inst]
        else:
            prefix = self._current_scope.lookup(NameCategory.THIS).type[:-1]

        self._app(Ins(Op.RAW, prefix + "_"))
        self._app(Ins(Op.RAW, t.name + name_lable))
        self._app(Ins(Op.RAW, "("))

        # constructs list of parameters
        args = t.inst + inst_lable
        if t.exp_list:
            args += ", "
        self._app(Ins(Op.RAW, args))

    def postVisit_expression_method(self, t):
        self.postVisit_expression_call(t)

    def preVisit_array_list(self, t):
        s = " " + t.variable + self._lables[t.variable]
        self._app(Ins(Op.ASSIGN, s))
    
    def preVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCSTART, t.type))

    def midVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCEND, t.type[:-2]))

    def preVisit_expression_array_indexing(self, t):
        self._app(Ins(Op.RAW, f"{t.identifier + self._lables[t.identifier]}["))

    def postVisit_expression_array_indexing(self, t):
        self._app(Ins(Op.RAW, "]"))

# auxies
    # FIXME - Ensure that there is a check in regard to if the type of the expression trying to be assigned to the extensions attributes match
    def _extension_instance(self, t):
        current = self._current_scope.lookup(t.struct)
        prev = t.identifier + self._lables[t.identifier]
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
            self._app(Ins(Op.RAW, prev + "->" + name + " = " + var))
            self._app(Ins(Op.RAW, ";"))
            
            # Instanciate all attributeds for the new instance 
            super = self._current_scope.lookup(current.info[2][0])
            for attr in super.info[0]:
                self._app(Ins(Op.INDENT))
                self._app(Ins(Op.ASSIGN, var + "->" + attr[0]))
                if attr[1] == "int" or attr[1][-2:] == "[]" or attr[0] == "bool":
                    self._app(Ins(Op.RAW, "0"))
                elif attr[1] == "float":
                    self._app(Ins(Op.RAW, "0.0"))
                elif attr[1] == "char":
                    self._app(Ins(Op.RAW, "''"))
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
                self._app(Ins(Op.TYPE, ext))
                self._app(Ins(Op.VARLIST, "*" + ext.lower(), None, None))
                self._app(Ins(Op.RAW, ";"))
                pass
        self._app(Ins(Op.CLASSMID, t.name))
        if len(cd.info[3]) > 0: # len > 0 => there are additons to generate code for
            for member in cd.info[3]: # where the additions are located
                if len(member) >= 3: # method
                    self._app(Ins(Op.TYPE, member[1]))
                    self._app(Ins(Op.START, " " + t.name + "_" + member[0] + self._lables[member[0]], member[1]))
                    self._app(Ins(Op.PARAMS, t.name, "*this", None))
                    self._app(Ins(Op.PREMID))
                    self._app(Ins(Op.IDTL_P))
                    self._app(Ins(Op.RET))
                    self._app(Ins(Op.RAW, cd.info[2][0] + "_" + member[0] + self._lables[member[0]] + "(this->" + cd.info[2][0].lower() + ")"))
                    self._app(Ins(Op.RAW, ";"))
                    self._app(Ins(Op.IDTL_M))
                    self._app(Ins(Op.END))
                    self._app(Ins(Op.SIGNATURE, member[1], t.name + "_" + member[0] + self._lables[member[0]], AST.parameter_list(t.name, "*this", None, t.lineno)))

    def _is_member_in_tuple_list(self, m, tl):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return True
        return False