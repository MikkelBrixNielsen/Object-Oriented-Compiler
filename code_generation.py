from enum import Enum, auto
from singleton_decorator import singleton
from visitors_base import VisitorsBase
from symbols import NameCategory


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
    FUNCSTART = auto()
    FUNCMID = auto()
    FUNCEND = auto()
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



    PRINTSTART = auto()
    PRINTEND = auto()


    COMMA = auto()
    RAW = auto()        # direct print


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
        self._app(Ins(Op.TYPE, t.type))

    def midVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_variables_list(self, t):
        self._app(Ins(Op.VARLIST, t.variable, t.next))

    def preVisit_statement_assignment(self, t):
        self._app(Ins(Op.INDENT))
        
    def midVisit_statement_assignment(self, t):
        lhs = ""
        if isinstance(t.lhs , str): # If statement assignemnt gets identifier, which is just a string it is responsible for printing it
            lhs = t.lhs
        self._app(Ins(Op.ASSIGN, lhs))

    def postVisit_statement_assignment(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_statement_return(self, t):
        self._app(Ins(Op.RET))

    def postVisit_statement_return(self, t):
        self._app(Ins(Op.EOL))

    def preVisit_statement_print(self, t):
        self._app(Ins(Op.PRINTSTART, t.exp.type))

    def postVisit_statement_print(self, t):
        self._app(Ins(Op.PRINTEND))

    def postVisit_expression_integer(self, t):
        self._app(Ins(Op.RAW, t.integer))
        
    def postVisit_expression_float(self, t):
        self._app(Ins(Op.RAW, t.double))

    def postVisit_expression_boolean(self, t):
        self._app(Ins(Op.RAW, t.integer))
    
    def postVisit_expression_char(self, t):
        self._app(Ins(Op.RAW, t.char))
    
    """
    def postVisit_expression_string(self, t):
        self._app(Ins(Op.STR, t.string))
    """

    def postVisit_attribute(self, t):
        self._app(Ins(Op.THIS))
        self._app(Ins(Op.RAW, t.attr))

    def preVisit_class_declaration(self, t):
        self._app(Ins(Op.CLASS, t.name))
        self._current_scope = t.symbol_table
    
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
        self._app(Ins(Op.TYPE2, t.type))

    def midVisit_attributes_declaration_list(self, t):
        self._app(Ins(Op.EOL2))

    def preVisit_attributes_list(self, t):
        self._app(Ins(Op.VARLIST2, t.variable, t.next))

    def postVisit_expression_identifier(self, t):
        self._app(Ins(Op.RAW, t.identifier))

    def preVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.TYPE, t.type))
            self._app(Ins(Op.FUNCSTART, t.name))
            self._app(Ins(Op.SIGNATURE, t.type, t.name, t.par_list))
    
    def midVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.FUNCMID))

    def postVisit_function(self, t):
        if not t.name == "global":
            self._app(Ins(Op.FUNCEND))

    def preVisit_parameter_list(self, t):
        self._app(Ins(Op.PARAMS, t.type, t.parameter, t.next))

    def preVisit_expression_call(self, t):
        self._app(Ins(Op.CALLSTART, t.name))
    
    def postVisit_expression_call(self, t):
        self._app(Ins(Op.CALLEND))

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

    # FIXME - HEEEEEEEEEEEEEEEEEEEEEEEEELP!?!?
    def postVisit_instance_expression_list(self, t):
        # find the value of the parameter if given or assign default value
        # might be more ideal to do this else where but idk ask steffen
        pass
    
    def postVisit_expression_attribute(self, t):
        self._app(Ins(Op.RAW, t.inst + "->" + t.field))

    def preVisit_expression_method(self, t):
        self._app(Ins(Op.RAW, self._current_scope.lookup(t.inst).type[:-1] + "_"))
        self.preVisit_expression_call(t)
        self._app(Ins(Op.RAW, t.inst + ", "))

    def postVisit_expression_method(self, t):
        self.postVisit_expression_call(t)

# auxies
    # FIXME - RUNNING NUMBER
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
                    if current_param:
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
                                self._app(Ins(Op.RAW, ""))
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
                if len(member) < 3: # Attribute
                    self._app(Ins(Op.TYPE2, member[1]))
                    self._app(Ins(Op.VARLIST2, member[0], None))
                    self._app(Ins(Op.EOL2))
                else: # method
                    self._app(Ins(Op.IDT_M)) # remove indentation level 
                    self._app(Ins(Op.TYPE, member[1]))
                    self._app(Ins(Op.FUNCSTART, t.name + "_" + member[0]))
                    self._app(Ins(Op.PARAMS, t.name + "*", "this", None))
                    self._app(Ins(Op.FUNCMID))
                    self._app(Ins(Op.RET))
                    self._app(Ins(Op.RAW, cd.info[2][0] + "_" + member[0] + "(this->" + cd.info[2][0].lower() + ")"))
                    self._app(Ins(Op.EOL))
                    self._app(Ins(Op.FUNCEND))
                    self._app(Ins(Op.IDT_P)) # add indentation level