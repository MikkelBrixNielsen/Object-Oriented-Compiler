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
    TYPE = auto()       # specifies that type for function and type infront of variable declaration lists should be printed
    EOL = auto()        # End of line (appends ";")
    RET = auto()
    INDENT = auto()
    IDT_M = auto()
    IDT_P = auto()
    VARLIST = auto()
    PARAMS = auto()
    ASSIGN = auto()
    SIGNATURE = auto()
    CALLSTART = auto()
    CALLEND = auto()
    CLASS = auto()
    CLASSMID = auto()
    THIS = auto()
    INSTANCE = auto()
    ATTRASSIGN = auto()

    TYPE2 = auto()
    EOL2 = auto()  
    VARLIST2 = auto()

    START = auto()
    PREMID = auto()
    MID = auto()
    POSTMID = auto()
    END = auto()
    RPAREN = auto()
    LPAREN = auto()
    LCURL = auto()
    RCURL = auto()
    PRINT = auto()
    COMMA = auto()
    RAW = auto()


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
        self._current_scope = None
        self._code = []

    def get_code(self):
        return self._code

    def _app(self, instruction):
        self._code.append(instruction)

    def preVisit_variables_declaration_list(self, t):
        if t.decl.__class__.__name__ == "array_list":
            t.type = t.type[:-2]
        self._app(Ins(Op.TYPE, t.type))

    def midVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_variables_list(self, t):
        self._app(Ins(Op.VARLIST, t.variable, t.next, t.type))

    def preVisit_statement_assignment(self, t):
            self._app(Ins(Op.INDENT))
        
    def midVisit_statement_assignment(self, t):
        lhs = ""
        if isinstance(t.lhs , str): # If statement assignemnt gets identifier, which is just a string it is responsible for printing it
            lhs = t.lhs
        # else the expression will do so automatically when visisted by the visitor
        self._app(Ins(Op.ASSIGN, lhs))

    def postVisit_statement_assignment(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_statement_return(self, t):
        self._app(Ins(Op.RET))

    def postVisit_statement_return(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_statement_print(self, t):
        self._app(Ins(Op.START, "printf"))
        self._app(Ins(Op.PRINT, t.exp.type))

    def postVisit_statement_print(self, t):
        self._app(Ins(Op.RPAREN))
        self._app(Ins(Op.EOL))

    def preVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.START, "if"))
        self._app(Ins(Op.IDT_P))

    def preMidVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.PREMID))

    def postMidVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.IDT_M))
        self._app(Ins(Op.MID, "else"))
        self._app(Ins(Op.IDT_P))

    def postVisit_statement_ifthenelse(self, t):
        self._app(Ins(Op.IDT_M))
        self._app(Ins(Op.END))

    def preVisit_statement_while(self, t):
        self._app(Ins(Op.START, "while"))
        self._app(Ins(Op.IDT_P))

    def midVisit_statement_while(self, t):
        self._app(Ins(Op.PREMID))

    def postVisit_statement_while(self, t):
        self._app(Ins(Op.IDT_M))
        self._app(Ins(Op.END))

    def postVisit_expression_integer(self, t):
        self._app(Ins(Op.RAW, t.integer))
        
    def postVisit_expression_float(self, t):
        self._app(Ins(Op.RAW, t.double))

    def postVisit_expression_boolean(self, t):
        self._app(Ins(Op.RAW, t.integer))
    
    def postVisit_expression_char(self, t):
        self._app(Ins(Op.RAW, t.char))
    
    def postVisit_attribute(self, t):
        self._app(Ins(Op.THIS))
        self._app(Ins(Op.RAW, t.attr))

    def preVisit_class_declaration(self, t):
        self._app(Ins(Op.CLASS, t.name))
        self._current_scope = t.symbol_table

    def postVisit_class_declaration(self, t):
        self._current_scope = self._current_scope.parent
    
    def midVisit_class_descriptor(self, t):
        self._extend_class(t)
        self._app(Ins(Op.CLASSMID, t.name))

    def preVisit_method(self, t):
        t.name = t.parent + "_" + t.name
        self.preVisit_function(t)
    
    def midVisit_method(self, t):
        self.midVisit_function(t)

    def postVisit_method(self, t):
        self.postVisit_function(t)

    def preVisit_attributes_declaration_list(self, t):
        if t.decl.__class__.__name__ == "array_list":
            t.type = t.type[:-2]
        self._app(Ins(Op.TYPE2, t.type))

    def midVisit_attributes_declaration_list(self, t):
        self._app(Ins(Op.EOL2))

    def preVisit_attributes_list(self, t):
        self._app(Ins(Op.VARLIST2, " " + t.variable, t.next))

    def postVisit_expression_identifier(self, t):
        self._app(Ins(Op.RAW, t.identifier))

    def preVisit_function(self, t):
        self._current_scope = t.symbol_table
        if not t.name == "global":
            if str(t.type)[-2:] == "[]":
                t.type = t.type[:-2] + "*"
            self._app(Ins(Op.TYPE, t.type))
            self._app(Ins(Op.START, " " + t.name))
            self._app(Ins(Op.IDT_P))
            self._app(Ins(Op.SIGNATURE, t.type, t.name, t.par_list))
    
    def midVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.PREMID))

    def postVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.IDT_M))
            self._app(Ins(Op.END))
        self._current_scope = self._current_scope.parent

    def preVisit_parameter_list(self, t):
        if t.type[-2:] == "[]":
            t.type = t.type[:-2]
            t.parameter = "*" + t.parameter
        self._app(Ins(Op.PARAMS, t.type, t.parameter, t.next))

    def preVisit_expression_call(self, t):
        self._app(Ins(Op.RAW, t.name))
        self._app(Ins(Op.LPAREN))
    
    def postVisit_expression_call(self, t):
        self._app(Ins(Op.RPAREN))

    def midVisit_expression_list(self, t):
        self._app(Ins(Op.COMMA, t.next))

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
        self._app(Ins(Op.INSTANCE, t.struct))
        self._extension_instance(t)


    def preVisit_instance_expression_list(self, t):
        self._app(Ins(Op.ATTRASSIGN, t.struct, t.next, t.param))
        # do something cool about assigning attributes to the newly created struct or smth idk ask steffen he might know

    def midVisit_instance_expression_list(self, t):
        if t.next:
            self._app(Ins(Op.EOL))
    
    def postVisit_expression_attribute(self, t):
        cd = None
        if t.inst == "this":
            cd = self._current_scope.lookup(self._current_scope.parent.lookup_this_scope(t.field).info[-1])
        else:
            cd = self._current_scope.lookup(self._current_scope.lookup(t.inst).type[:-1])
        
        if self._is_member_in_tuple_list((t.field, t.type), cd.info[0]): # is attr member of cd
            self._app(Ins(Op.RAW, t.inst + "->" + t.field))
        else:
            self._app(Ins(Op.RAW, t.inst + "->" + cd.info[2][0].lower() + "->" + t.field))

    def preVisit_expression_method(self, t):
        name = t.inst
        if not name == "this":
            name = self._current_scope.lookup(t.inst).type[:-1]
        else:
            name = self._current_scope.lookup(t.name).info.parent
        self._app(Ins(Op.RAW, name + "_"))
        self.preVisit_expression_call(t)
        args = t.inst
        if t.exp_list:
            args += ", "
        self._app(Ins(Op.RAW, args))

    def postVisit_expression_method(self, t):
        self.postVisit_expression_call(t)

    def preVisit_array_list(self, t):
        s = " " + t.variable + "[" + str(t.exp.size) + "]"
        flag = 0 if not t.name else 1
        if t.exp.data:
              self._app(Ins(Op.ASSIGN, s, flag))
        else:
            self._app(Ins(Op.RAW, s, flag))

    def preVisit_expression_new_array(self, t):
        if t.data:
            self._app(Ins(Op.LCURL))

    def postVisit_expression_new_array(self, t):
        if t.data:
            self._app(Ins(Op.RCURL))

    def postVisit_expression_array_indexing(self, t):
        val = self._current_scope.lookup(t.identifier)
        if not val.cat == NameCategory.PARAMETER:
            current_idx = 0
            current = val.info[-3]
            while current:
                current = current.next
                current_idx += 1

        self._app(Ins(Op.RAW, f"{t.identifier}[{t.idx}]"))

    # Design choice just return 0 if array index is not initialized or throw error?


# auxies
    # FIXME - RUNNING NUMBER
    # FIXME - Ensure that there is a check in regard to if the type of the expression trying to be assigned to the extensions attributes match
    def _extension_instance(self, t):
        cd = self._current_scope.lookup(t.struct)
        if len(cd.info[2]) > 0: # len > 0 => there are extensions 
            temp = cd.info[2][0].lower()
            self._app(Ins(Op.TYPE, cd.info[2][0] + "*"))
            self._app(Ins(Op.VARLIST, temp, None))
            self._app(Ins(Op.RAW, " = "))            
            self._app(Ins(Op.INSTANCE, cd.info[2][0]))
               
        # Instanciate all attributeds for the new instance 
            super = self._current_scope.lookup(cd.info[2][0])
            # FIXME - MAYBE WORKS IDK ASK STEFFEN
            # FIXME - NEEDS running number 
            if t.params:
                current_param = t.params
                for attr in super.info[0]:
                    self._app(Ins(Op.INDENT))
                    self._app(Ins(Op.ASSIGN, temp + "->" + attr[0]))
                    # FIXME - DON'T LIKETHIS 
                    if current_param and current_param.exp.type == attr[1]: # Latter part of this if should consider if the type of the expression being assigned to the attr matches its type but IDK ask Steffen
                        match current_param.exp.type:
                            case "int":
                                self._app(Ins(Op.RAW, current_param.exp.integer))
                            case "float":
                                self._app(Ins(Op.RAW, current_param.exp.double))
                            case "char":
                                self._app(Ins(Op.RAW, current_param.exp.char))
                            case _:
                                print(f"{current_param.exp.type} not implemented in _extension_instance in code generation - please fix")
                    else:
                        match attr[1]: # attr's type 
                            case "int":
                                self._app(Ins(Op.RAW, "0"))
                            case "float":
                                self._app(Ins(Op.RAW, "0.0"))
                            case "char":
                                self._app(Ins(Op.RAW, "''"))
                            case _:
                                print(f"{current_param.exp.type} not implemented in _extension_instance in code generation - please fix")
                    self._app(Ins(Op.EOL))
                    current_param = current_param.next

        # Assigns created struct to its parent class
            self._app(Ins(Op.INDENT))
            self._app(Ins(Op.RAW, t.identifier + "->" + temp + " = " + temp))
            self._app(Ins(Op.EOL))

    # FIXME Make it so code is generated for the extensions 
    # FIXME - NOT VERY MAINTAINABLE... I MEAN I PROBABLY DON'T EVEN KNOW WHAT IT IS SUPPOSED TO DO ANYMORE
    # FIXME - Variables inherited should become a special version associated with a "virtual" instance of the extension e.g. Second has attr a, so in Third there will be a Second_a attr and for Seconds get_a Third will return Second_a
    # or it might be possible to include na actual instance of Second in third and just use the methods already defined for second which are in the global scope already
    def _extend_class(self, t):
        cd = self._current_scope.lookup(t.name)
        if len(cd.info[2]) > 0: # len > 0 => extension exists
                self._app(Ins(Op.TYPE2, cd.info[2][0] + "*"))
                self._app(Ins(Op.VARLIST2, cd.info[2][0].lower(), None))
                self._app(Ins(Op.EOL2)) 
        if len(cd.info[3]) > 0: # len > 0 => there are additons to generate code for
            for member in cd.info[3]: # where the additions are located
                # FIXME - We probably should not add the attributes from the extended class to the actual class 
                if len(member) < 3: # Attribute
                    # TODO - DELETE maybe
                    #self._app(Ins(Op.TYPE2, member[1]))
                    #self._app(Ins(Op.VARLIST2, member[0], None))
                    #self._app(Ins(Op.EOL2))
                    pass
                else: # method
                    self._app(Ins(Op.IDT_M)) # remove indentation level 
                    self._app(Ins(Op.TYPE, member[1]))
                    self._app(Ins(Op.START, " " + t.name + "_" + member[0]))
                    self._app(Ins(Op.IDT_P))
                    self._app(Ins(Op.PARAMS, t.name + "*", "this", None))
                    self._app(Ins(Op.PREMID))
                    self._app(Ins(Op.RET))
                    self._app(Ins(Op.RAW, cd.info[2][0] + "_" + member[0] + "(this->" + cd.info[2][0].lower() + ")"))
                    self._app(Ins(Op.EOL))
                    self._app(Ins(Op.IDT_M)) # remove indentation level 
                    self._app(Ins(Op.END))
                    self._app(Ins(Op.IDT_P)) # add indentation level
                    self._app(Ins(Op.SIGNATURE, member[1], t.name + "_" + member[0], AST.parameter_list(t.name + "*", "this", None, -1)))

    def _is_member_in_tuple_list(self, m, tl):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return True
        return False