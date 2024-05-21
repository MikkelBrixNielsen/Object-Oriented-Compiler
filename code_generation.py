from enum import Enum, auto
from visitors_base import VisitorsBase
from symbols import NameCategory, PRIM_TYPES, _get_identifier
#from label_generation import LabelTable
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

    NULLINITIALIZATION = auto()
    ALLOC = auto()
    FREE = auto()
    ALLOCSTART = auto()
    ALLOCEND = auto()
    MEMCHECK = auto()
    DEFAULTVAL = auto()



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
        #self._labels = LabelTable(None)
        #self._temp_labels = LabelTable(None)
        #self._comp_labels = LabelTable(None)

    def get_code(self):
        return self._code

    # creates and enters a new scope
    def _enter_new_scope(self, t):
        self._current_scope = t.symbol_table
        # FIXME REMOVE RETURN WHEN ACTIVATING LABLE GENERATION PHASE 
        #self._labels = t._labels
        #self._temp_labels = t._temp_labels 
        #self._comp_labels = t._comp_labels
    
    # exits the current scope and goes to parent scope
    def _exit_current_scope(self, t):
        self._current_scope = self._current_scope.parent
        # FIXME REMOVE RETURN WHEN ACTIVATING LABLE GENERATION PHASE 
        #self._labels = self._labels.parent
        #self._temp_labels = self._temp_labels.parent
        #self._comp_labels = self._comp_labels.parent

    def _app(self, instruction):
        self._code.append(instruction)

    def preVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.TYPE, t.decl.type))        

    def midVisit_variables_declaration_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def preVisit_variables_list(self, t):
        self._app(Ins(Op.VARLIST, t.variable + t.label, t.next, t.type))

    # FIXME - GARBAGE COLLECTION free when assigning values to lhs if rhs has no references
    def preVisit_statement_assignment(self, t):
        self._assign_cleanup(t)
        self._app(Ins(Op.TYPE, t.rhs.type))
        self._app(Ins(Op.VARLIST, "TEMP" + t.temp_label, None, t.rhs.type))
        self._app(Ins(Op.ASSIGN, ""))
        # self._cleanup # or something similar
        
    def midVisit_statement_assignment(self, t):
        cnr = t.rhs.__class__.__name__
        cnl = t.lhs.__class__.__name__
        if not cnr == "expression_new_instance":
            self._app(Ins(Op.RAW, ";"))
        if  cnr == "expression_new_array":
            self._app(Ins(Op.MEMCHECK, "TEMP" + t.temp_label))
        if isinstance(t.lhs , str) and not cnr == "expression_new_instance": # If statement assignemnt gets identifier, which is just a string it is responsible for printing it
            self._app(Ins(Op.INDENT))
            self._app(Ins(Op.ASSIGN, t.lhs + self._current_scope.lookup(t.lhs).label))
        if cnl  == "expression_array_indexing" and (cnl == "expression_attribute" and not cnl == "expression_new_instance"):
            self._app(Ins(Op.INDENT))

    def postVisit_statement_assignment(self, t):
        cnr = t.rhs.__class__.__name__
        cnl = t.lhs.__class__.__name__
        # else the expression will do so automatically when visisted by the visitor
        if not isinstance(t.lhs , str) and not (cnl == "expression_attribute" and not cnl == "expression_new_instance"):
            self._app(Ins(Op.ASSIGN, ''))
        if not cnr == "expression_new_instance":
            self._app(Ins(Op.RAW, "TEMP" + t.temp_label))
            self._app(Ins(Op.RAW, ";"))
       
    def preVisit_statement_return(self, t):
        self._app(Ins(Op.TYPE, t.exp.type))
        self._app(Ins(Op.VARLIST, "TEMP" + t.temp_label, None, t.exp.type))
        self._app(Ins(Op.ASSIGN, ''))


    def postVisit_statement_return(self, t):
        self._app(Ins(Op.RAW, ";"))
        self._cleanup(t)
        self._app(Ins(Op.RET))
        self._app(Ins(Op.RAW, "TEMP" + t.temp_label + ";"))

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
        labelled_name = t.parent + "_" + t.name + t.label
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
        self._app(Ins(Op.VARLIST, t.variable + t.label, t.next, t.type))

    def postVisit_expression_identifier(self, t):
        self._app(Ins(Op.RAW, t.identifier + t.label))

    def preVisit_function(self, t):
        # functions defined instide the global scope 
        # (so all functions excluding the implicit function for global scope)
        if t.scope_level > 0: 
            name = t.name
            self._app(Ins(Op.TYPE, t.type))
            if not t.name == "main" or t.scope_level > 1:
                name = t.name + t.label
            self._app(Ins(Op.START, " " + name, t.type))
            self._app(Ins(Op.IDTL_P))
            self._app(Ins(Op.SIGNATURE, t.type, name, t.par_list))
        self._enter_new_scope(t)
    
    def midVisit_function(self, t):
        if t.name != "global" or t.scope_level > 0:
            self._app(Ins(Op.PREMID))

    def postVisit_function(self, t):
        self._exit_current_scope(t)
        if t.name != "global" or t.scope_level > 0:
            self._app(Ins(Op.IDTL_M))
            self._app(Ins(Op.END))

    def preVisit_parameter_list(self, t):
        self._app(Ins(Op.PARAMS, t.type, t.parameter, t.next))

    def preVisit_expression_call(self, t):
        val = self._current_scope.lookup(t.name)
        self._app(Ins(Op.RAW, t.name + val.label))
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
        self._app(Ins(Op.MEMCHECK, "TEMP" + t.temp_label))
        self._app(Ins(Op.INDENT))

        identifier = ""
        if t.identifier.__class__.__name__ == "expression_attribute":
            identifier = self._generate_attribute_labeled_identifier(t.identifier)
            identifier = f"{identifier[0]}->{identifier[1]}"
        else:
            identifier = t.identifier + self._current_scope.lookup(t.identifier).label
            pass
        self._app(Ins(Op.ASSIGN, identifier))
        self._app(Ins(Op.RAW, "TEMP" + t.temp_label))
        self._app(Ins(Op.RAW, ";"))
        self._extension_instance(t)
        self._enter_new_scope(t)

    def preVisit_instance_expression_list(self, t):
        inst = ""
        field = ""
        if t.struct.__class__.__name__ == "expression_attribute":
            inst, field = self._generate_attribute_labeled_identifier(t.struct)
        else:
            val = self._current_scope.lookup_this_scope(t.struct)
            inst = t.struct + val.label if val else ""
            cd = self._current_scope.lookup_all(self._current_scope.lookup(t.struct).type[:-1]).info
            member = self._find_member_in_tuple_list((t.param, t.exp.type), cd[0])
            field = member[0] + member[2]
        self._app(Ins(Op.ATTRASSIGN, inst, t.next, field))

    def midVisit_instance_expression_list(self, t):
        self._app(Ins(Op.RAW, ";"))

    def postVisit_expression_attribute(self, t):
        cd = None
        var = t.inst
        if t.inst == "this":
            inst = self._current_scope.lookup(NameCategory.THIS).cat
            cd = self._current_scope.lookup_all(inst)
        else:
            cd = self._current_scope.lookup_all(self._current_scope.lookup_all(t.inst).type[:-1])
            var = t.inst + self._current_scope.lookup(t.inst).label

        member = self._find_member_in_tuple_list((t.field, t.type), cd.info[0])
        if member: # is attr member of cd
            self._app(Ins(Op.RAW, var + "->" + member[0] + member[2]))
        else:
            s = ""
            while (not member) and len(cd.info[2]) != 0:
                ext = cd.info[2][0]
                s = s + ext.lower() + cd.info[2][1] + "->"
                cd = self._current_scope.lookup_all(ext)
                member = self._find_member_in_tuple_list((t.field, t.type), cd.info[0])
            self._app(Ins(Op.RAW, var + "->" + s + member[0] + member[2]))

    def preVisit_expression_method(self, t):
        prefix = ""
        lablled_inst = ""
        lablled_name = t.name + t.label
        if t.inst != "this":
            prefix = self._current_scope.lookup(t.inst).info[-1][:-1]
            lablled_inst = t.inst + self._current_scope.lookup(t.inst).label
        else:
            prefix = self._current_scope.lookup(NameCategory.THIS).cat
            lablled_inst = t.inst

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
    #    s = " " + (t.variable)
    #    self._app(Ins(Op.ASSIGN, s))
    
    def preVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCSTART, t.type))

    def midVisit_expression_new_array(self, t):
        self._app(Ins(Op.ALLOCEND, t.type[:-2]))

    def preVisit_expression_array_indexing(self, t):
        if isinstance(t.identifier, str):
            self._app(Ins(Op.RAW, f"{_get_identifier(t.identifier) + t.label}["))
        else:
            self._app(Ins(Op.RAW, "["))

    def postVisit_expression_array_indexing(self, t):
        self._app(Ins(Op.RAW, "]"))

    def postVisit_expression_null(self, t):
        self._app(Ins(Op.DEFAULTVAL, t.type))

# auxies
    # FIXME - Ensure that there is a check in regard to if the type of the expression trying to be assigned to the extensions attributes match
    def _extension_instance(self, t):
        current = self._current_scope.lookup_all(t.struct)
        if t.identifier.__class__.__name__ == "expression_attribute":
            inst, field = self._generate_attribute_labeled_identifier(t.identifier)
            prev = f"{inst}->{field}"
        else:
            prev = t.identifier + self._current_scope.lookup(t.identifier).label

        while len(current.info[2]) > 0: # There are more extensions to generate code for
            name = current.info[2][0].lower()
            var = name + t.inst_label
            name = name + current.info[2][1]
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
            super = self._current_scope.lookup_all(current.info[2][0])
            for attr in super.info[0]:
                self._app(Ins(Op.INDENT))
                self._app(Ins(Op.ASSIGN, var + "->" + attr[0] + attr[2]))
                if attr[1] == "int" or attr[1][-2:] == "[]" or attr[1] == "bool":
                    self._app(Ins(Op.RAW, "0"))
                elif attr[1] == "float":
                    self._app(Ins(Op.RAW, "0.0"))
                elif attr[1] == "char":
                    self._app(Ins(Op.RAW, "'\\0'"))
                elif attr[1][-1] == "*":
                    ins1 = self._code.pop()
                    ins2 = self._code.pop()
                    var1 = attr[1][:-1].lower() + t.temp_label
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
            current = self._current_scope.lookup_all(current.info[2][0])

    # FIXME Make it so code is generated for the extensions 
    # FIXME - NOT VERY MAINTAINABLE... I MEAN I PROBABLY DON'T EVEN KNOW WHAT IT IS SUPPOSED TO DO ANYMORE
    # FIXME - Variables inherited should become a special version associated with a "virtual" instance of the extension e.g. Second has attr a, so in Third there will be a Second_a attr and for Seconds get_a Third will return Second_a
    # or it might be possible to include an actual instance of Second in third and just use the methods already defined for second which are in the global scope already
    def _extend_class(self, t):
        cd = self._current_scope.lookup_all(t.name)
        if len(cd.info[2]) > 0: # len > 0 => extension exists
            for ext in cd.info[2][0]:
                name = ext.lower()
                self._app(Ins(Op.TYPE, ext))
                self._app(Ins(Op.VARLIST, "*" + name + cd.info[2][1], None, None))
                self._app(Ins(Op.RAW, ";"))
        self._app(Ins(Op.CLASSMID, t.name))
        if len(cd.info[3]) > 0: # len > 0 => there are additons to generate code for
            for member in cd.info[3]: # where the additions are located
                if len(member) >= 3: # method
                    method_name = member[0] + member[2].label
                    self._app(Ins(Op.TYPE, member[1]))
                    self._app(Ins(Op.START, " " + t.name + "_" + method_name, member[1]))
                    self._app(Ins(Op.PARAMS, t.name, "*this", None))
                    self._app(Ins(Op.PREMID))
                    self._app(Ins(Op.IDTL_P))
                    self._app(Ins(Op.RET))
                    name = cd.info[2][0].lower()
                    self._app(Ins(Op.RAW, cd.info[2][0] + "_" + method_name + "(this->" + name + t.label + ")"))
                    self._app(Ins(Op.RAW, ";"))
                    self._app(Ins(Op.IDTL_M))
                    self._app(Ins(Op.END))
                    self._app(Ins(Op.SIGNATURE, member[1], t.name + "_" + method_name, AST.parameter_list(t.name, "*this", None, t.lineno)))

    def _find_member_in_tuple_list(self, m, tl):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return member
        return None
    
    def _is_member_in_tuple_list(self, m, tl):
        return not self._find_member_in_tuple_list(m, tl) == None

    def _generate_attribute_labeled_identifier(self, t):
        idt = [t.inst, t.field]
        if idt[0] == "this":
            # this has not label so it remains unchanged
            # find field label
            val = self._current_scope.lookup_class(NameCategory.THIS)
            cd = self._current_scope.lookup_all(val.cat)
            member = self._find_member_in_tuple_list((idt[1],t.type), cd.info[0]) 
            idt[1] = member[0] + member[2]
        else:
            # find inst label
            val = self._current_scope.lookup(idt[0])
            idt[0] = idt[0] + val.label
            # find attribute label
            cd = self._current_scope.lookup_all(val.type[:-1])
            member = self._find_member_in_tuple_list((idt[1], t.type), cd.info[0])
            idt[1] = member[0] + member[2]
        return idt
    
    #def _cleanup(self, t):
    #    if not t.name == "global" or t.scope_level > 0: # clean up for all other user defined functions
    #        # finds and frees variables in the scope for the current function
    #        self._find_and_free_in(t.body.variables_decl)
    #    else: # clean up for the global scope encapsulating everything
    #        self._find_and_free_in(t.body.variables_decl)

    #def _find_and_free_in(self, list):
        # Delete the comment bellow if the code to find all variables is deleted 
        # Collects all variables defined in the function
    #    collected_vars = {}
    #    decl = list
    #    while decl:
    #        var = decl.decl
    #        while var:
    #            if not (var.type in PRIM_TYPES):
    #                    collected_vars[var.variable] = False
    #            var = var.next                         
    #        decl = decl.next 
    #    print(collected_vars)
    
    # TODO
    # Do free for global scope encapsulating main and stuff

    #def _assignment(self, t):
    #    cn = t.lhs.__class__.__name__
    #    name = t.lhs
    #    lhs = t.lhs
    #    if cn == "expression_attribute":
    #        name = t.lhs.field if t.lhs.inst == "this" else t.lhs.inst
    #        lhs = self._current_scope.lookup_class(name)
    #    elif cn == "expression_array_indexing":
    #       # FIXME - if array indexing is possible on array attributes then something link "expression_attribute" should happen
    #       name = _get_identifier(t.lhs.identifier)
    #       name = name if not isinstance(name, tuple) else name[0]
    #       lhs = self._current_scope.lookup(name)
    #    else:
    #        lhs = self._current_scope.lookup(name)
    #
    #    # finds identifiers in rhs expression and saves them in symbol table for lhs identifier
    #    lhs._assigned_value = []
    #    lhs._assigned_value.append(_get_identifier(t.rhs))
    #    if hasattr(t.rhs, "_assigned_value"):
    #        lhs._assigned_value = lhs._assigned_value + t.rhs._assigned_value
    #    
    #    # for all variables in rhs if they have variables assigned to them and are not primitive 
    #    # types save those variables as well
    #    for var in lhs._assigned_value:
    #        val = self._current_scope.lookup(var)
    #        if not val:
    #            val = self._current_scope.lookup_class(var)
    #        if val and val.type not in PRIM_TYPES:
    #            lhs._assigned_value = lhs._assigned_value + val._assigned_value


    def _assign_cleanup(self, t):
        # primitive type should not be freed so no point in keeping count of their references 
        if t.rhs.type in PRIM_TYPES:
            return
        
        cnl = t.lhs.__class__.__name__
        cnr = t.rhs.__class__.__name__
        lhs = _get_identifier(t.lhs)
        rhs = _get_identifier(t.rhs)

        if cnl == "expression_attribute":
            lhs, field = lhs
            lhs_val = self._current_scope.lookup(lhs)
            # store information regarding what an attribute has been assigned 
            # on the identifier for the instance they are a part of
            if hasattr(lhs_val, f"_attr_assigned_value"):
                lhs_val._attr_assigned_value[field]._references[field].remove((lhs, field))
                if (lhs_val._attr_assigned_value[field].type not in PRIM_TYPES and
                    len(lhs_val._attr_assigned_value[field]._references[field]) < 1):
                    self._app(Ins(Op.FREE, lhs))
            else:
                lhs_val._attr_assigned_value = {}
            
            rv = t.rhs 
            if cnr == "expression_attribute":
                rv = self._rhs_exprresion_attribute_assign_aux(rv)
            else:            
                if cnr != "expression_call" and cnr != "expression_method":
                    rhs_val = self._current_scope.lookup(rhs)
                    if rhs_val and rhs_val.cat != NameCategory.PARAMETER: 
                        rv = rhs_val._attr_assigned_value[field]
            if not hasattr(rv, "_references"):
                rv._references = {}
            if field not in rv._references:
                rv._references[field] = []  
            rv._references[field].append((lhs, field))
            lhs_val._attr_assigned_value[field] = rv
        else: # lhs = Identifier or expression_array_indexing
            lhs_val = self._current_scope.lookup(lhs)        
            # removes lsh from lhs' assigned value's reference list
            if hasattr(lhs_val, "_assigned_value"):
                # remove lhs as reference
                lhs_val._assigned_value._references.remove(lhs)
                if (lhs_val._assigned_value.type not in PRIM_TYPES and
                    len(lhs_val._assigned_value._references) < 1):
                    # free identifier
                    self._app(Ins(Op.FREE, lhs))

            # the value that should be assigned 
            # should be AST node for a new instance 
            # / allocation / func. call / meth. call
            rv = t.rhs 
            if cnr == "expression_attribute":
                rv = self._rhs_exprresion_attribute_assign_aux(rv)
                # retrieve AST node from where attributes save their assigned value
                # This will probably need to be saved on the identifier for the instance the attribute belongs to
                # Maybe even put a dict there so its more like lookup(t.inst)[_t.field] -> assigned_value
                # rv = lookup(t.inst)._t.field_assigned_value (or something)
            else:            
                # if rhs is an entry in symbol table then it is not an 
                # AST node so get its assigned value which should be an AST node 
                # But treat method and function calls as if they were an allocated object
                if cnr != "expression_call" and cnr != "expression_method":
                    rhs_val = self._current_scope.lookup(rhs)
                    if rhs_val and rhs_val.cat != NameCategory.PARAMETER: 
                        rv = rhs_val._assigned_value
            # if it's rhs' first time being rhs, assign it a reference list
            if not hasattr(rv, "_references"):
                rv._references = []

            # append lhs to rhs' reference list
            rv._references.append(lhs)
            # make rhs (The AST node) lhs' assigned value
            lhs_val._assigned_value = rv

    def _rhs_exprresion_attribute_assign_aux(self, rv):
        print("GARBAGE COLLECTION FOR ATTRIBUTES NOT IMPLEMENTED")
        pass

    def _cleanup(self, t):
        self._free_list(self._collect_variables(t))

    def _free_list(self, collected_vars):
        for key, info in collected_vars.items():
            self._free_object(key, info.type, info.label)

    def _collect_variables(self, t):
        # should be all variables with a reference count > 0
        variables_to_not_free = []
        
        if t.exp.type not in PRIM_TYPES:
            variables_to_not_free.append(t.exp.identifier)

        variables_to_free = {}
        for elem, info in self._current_scope._tab.items():
            if (info.cat != NameCategory.PARAMETER and info.type not in PRIM_TYPES and 
                elem != NameCategory.THIS and elem not in variables_to_not_free and 
                self._only_one_or_local_refs(elem, info)):
                variables_to_free[elem] = info
                # puts all references to the object elem has been assigned into the 
                # variables_to_not_free list such that double frees don't occur
                if hasattr(info, "_assigned_value"):
                    variables_to_not_free.append(x for x in info._assigned_value._references)
                if hasattr(info, "_attr_assigned_value"):
                    # FIXME - add attributes to variables not to free
                    pass
        return variables_to_free
    
    def _only_one_or_local_refs(self, elem, info):
        # check whether _attr_assigned_value prevents freeing the memory
        # or if _assigned_value prevents freeing the memory
        #(not len(info._assigned_value._references) > 1) and self._all_refs_in_scope(elem, info)
        return True

    def _all_refs_in_scope(self, elem, info):
        references = info._assigned_value._references
        for ref in references:
            if ref not in self._current_scope._tab:
                return False
        return True

    def _free_object(self, key, type, label, prev=""):
        if type[-1:] == "*": # if type is a pointer to an instance
            cd = self._current_scope.lookup_all(type[:-1])
            self._free_instance_variables(key, cd, label, prev)
        else: # type is pointer to some array
            self._free_array(key, type, label, prev)

    def _free_instance_variables(self, key, cd, label, prev=""):
        prev = prev + key + label
        # free attributes for given instance
        for attr in cd.info[0]:
            if attr[1] not in PRIM_TYPES:
                self._free_object(*attr)
        # free extension and its attributes if there is one 
        if len(cd.info[2]) > 0:
            current = cd.info[2][0].lower()
            self._free_object(current, cd.info[2][0] + "*", cd.info[2][1], prev + "->")
        # free instance itself
        self._app(Ins(Op.FREE, prev))

    def _free_array(self, key, type, label, prev=""):
        self._app(Ins(Op.INDENT))
        self._app(Ins(Op.RAW, f"// Free({key + label})\n"))
        pass

    #def _collect_variables_in_return(self, t):
    #    vars_in_return = []
    #    current = t
    #    while current:
    #        if current.__class__.__name__ == "expression_binop":
    #            vars_in_return = vars_in_return + self._collect_variables_in_return(t.exp.lhs)
    #            vars_in_return = vars_in_return + self._collect_variables_in_return(t.exp.rhs)
    #        else:
    #            identifier = self._flatten_tuple(_get_identifier(current.exp))
    #            for idt in identifier:
    #                elem = self._current_scope.lookup(idt)
    #                if elem and elem.type not in PRIM_TYPES:
    #                    vars_in_return.append(idt)
    #        if hasattr(current, "next"):
    #            current = current.next
    #        else: 
    #            current = None
    #    return vars_in_return
    
    #def _flatten_tuple(self, t):
    #    if not isinstance(t, tuple):
    #        return []
    #    flattened_list = []
    #    for item in t:
    #        if isinstance(item, tuple):
    #            flattened_list.extend(self._flatten_tuple(item))
    #        else:
    #            flattened_list.append(item)
    #    return flattened_list
        
        # looks through statements to see what collected variables are assigned 
        #stm = list
        #print(collected_vars, t.name, "START")
        #while stm:
        #    if stm.stm.__class__.__name__ == "statement_assignment":
        #        val = self._current_scope.lookup_this_scope(stm.stm.lhs) # only looks for variables in the current function scope  
        #        if val and val.type not in PRIM_TYPES and val.cat != NameCategory.PARAMETER: # primitive types and parameters should not be freed
        #            collected_vars[_get_identifier(stm.stm)[0]] = True # _get_identifier(stm.stm)[0] is lhs for statement_assignment 
        #    stm = stm.next
        #print(collected_vars, t.name, "END")
        # looks through all statemnts and finds all returns statements
        # and places free statements before it
        #stm = list
        #while stm:
            # only look at whether the current statment is a return statement
            # it should also look if e.g. a if_then_else statement has a return
            # or a while_statement etc.
         #   if stm.stm.__class__.__name__ == "statement_return":
         #       ins = self._remove_return_instructions()
         #       self._free_list(collected_vars)
         #       self._add_return_instructions(ins)
         #   stm = stm.next
        
    # removes instructions associated with return statement
    #def _remove_return_instructions(self):
    #    ins = []
    #    current = self._code.pop()
    #    while current:
    #        ins.append(current)
    #        if current.opcode == Op.RET:
    #            break
    #        current = self._code.pop()
    #    return ins[::-1] # reverse the instruction to get them in the order which they should be put back

    # Puts the instructions for return statement back into the code after the free statements
    # ins must be the result from callign _remove_return_instructions
    #def _add_return_instructions(self, ins):
    #    [self._app(x) for x in ins]

    # frees should happen in returns
    # when assigning something to something new the old thing should be freed 
       # Flag saying something has been assigned something???
    # variables should be collected in previsit function
    # if the variable you are trying to free is a class and 
    # it has instances of other classes it also has to be freed
    # when initializing an instance or array set them to Null / 0 at the beginnig
    # relevant attributes should be freed, 
    # except for those included in a return statement of the scope in which the class containing them is initialized
