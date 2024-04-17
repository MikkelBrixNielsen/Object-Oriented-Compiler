from visitors_base import VisitorsBase
from errors import error_message
from symbols import NameCategory

class ASTTypeCheckingVisitor(VisitorsBase):
    def __init__(self):
        self._current_scope = None
        self.number_of_actual_parameters = []

    def preVisit_function(self, t):
        self._current_scope = t.symbol_table

    def postVisit_function(self, t):
        self._current_scope = self._current_scope.parent
        if not t.name == "global": 
           self._function_type_match_return_type(t)

    def preVisit_class_declaration(self, t):
        self._current_scope = t.symbol_table
        # checks if the extensions is actually a class 
        # FIXME If multi-inheritance is implemented expand this to check all the extensions 
        super = t.extends
        if super:
            if super == t.name:
                error_message("Type Checking",
                              f"{t.name} cannot have itself as an extension.",
                              t.lineno)
            super_cd = self._current_scope.lookup(super)
            if not super_cd:
                error_message("Type Checking",
                              f"Class {super} not found - maybe used before declaration.",
                              t.lineno)
                
            if not NameCategory.CLASS == super_cd.cat:
                cat = str(super_cd.cat).split(".")[-1].lower()
                error_message("Type Checking",
                            f"{t.name} can only extend other classes {super} is a {cat}.",
                            t.lineno)
    
    def postVisit_class_declaration(self, t):
        self._current_scope = self._current_scope.parent

    def preVisit_method(self, t):
        self._current_scope = t.symbol_table
        
    def postVisit_method(self, t):
        self._current_scope = self._current_scope.parent

    def postVisit_statement_assignment(self, t):
        lhs = None
        # FIXME - This is really specific make it more general
        if t.lhs.__class__.__name__ == "expression_attribute":
            lhs = self._exist_membership(t.lhs, "attribute")         
        else: 
            lhs = self._current_scope.lookup(t.lhs)
            lhs = (t.lhs, lhs.type, lhs.cat)
        if not lhs:
            error_message("Type Checking",
                          f"Variable '{lhs[0]}' not found.",
                          t.lineno)
        if lhs[2] == NameCategory.PARAMETER:
            error_message("Type Checking",
                          f"Assignment to parameter '{lhs[0]}' not allowed.",
                          t.lineno)
        elif lhs[2] == NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Assignment to function '{lhs[0]}' not allowed.",
                          t.lineno)
        # check whether what is being assigned has the same type as what is being assigned to
        t_lhs = lhs[1]
        t_rhs = self._get_type(t.rhs)
        
        if not t_lhs == t_rhs:
            # FIXME - I REALLY DON'T LIKE THAT A FUCNTIONS RETURN TYPE IS CHECKED HERE BUT MAYBE 
            # THAT IS OKAY IDK THIS SEEMS REALLY BAD SINCE IT IS THEN CHECKED AGIAN WHEN THE 
            # FUCNTION IS ACTUALLY VISITED FOR TYPE CHECKING AND THAT JUST SEEMS A LITTLE "NEDEREN"
            # BUT IDK MAYBE ASK STEFFEN HE MIGHT KNOW SOMETHING COOL
            self._function_type_match_return_type(self._current_scope.lookup(t.rhs.name).info)
            error_message("Type Checking",
                          f"Incorrect assignment: Assigning type {t_rhs} to type {t_lhs}",
                          t.rhs.lineno)

    def postVisit_expression_identifier(self, t):
        value = self._current_scope.lookup(t.identifier)
        if not value:
            error_message("Type Checking",
                          f"Identifier '{t.identifier}' not found.",
                          t.lineno)
        if value.cat == NameCategory.FUNCTION:
            error_message(
                "Type Checking",
                f"Function name '{t.identifier}' cannot be an identifier.",
                t.lineno)
        t.type = value.type

    def preVisit_expression_call(self, t):
        self.number_of_actual_parameters.append(0)

    def postVisit_expression_call(self, t):
        value = self._current_scope.lookup(t.name)
        if not value:
            error_message("Type Checking",
                          f"Function '{t.name}' not found.",
                          t.lineno)
        elif value.cat != NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Identifier '{t.name}' is not a function.",
                          t.lineno)
        node = value.info
        if self.number_of_actual_parameters[-1] < node.number_of_parameters:
            error_message("Type Checking",
                          f"'{t.name}' was called with too few parameters.",
                          t.lineno)
        elif self.number_of_actual_parameters[-1] > node.number_of_parameters:
            error_message("Type Checking",
                          f"'{t.name}' was called with too many parameters.",
                          t.lineno)
        self.number_of_actual_parameters.pop()
        # FIXME - Check parameter types actually match was is needed compared to what was given :))

    def midVisit_expression_list(self, t):
        self.number_of_actual_parameters[-1] += 1

    def postVisit_expression_binop(self, t):
        t.type = self._get_effective_type(self._get_type(t.lhs), self._get_type(t.rhs), t)
                
    def postVisit_expression_new_instance(self, t):
        value = self._current_scope.lookup(t.struct)
        if not value:
            error_message("Type Checking",
                          f"Class {t.struct} not found.",
                          t.lineno)
        elif not value.cat == NameCategory.CLASS:
            error_message("Type Checking",
                          f"Identifier {t.struct} is not a class.",
                          t.lineno)
        num_given_params = self._getLen(t.params)
        num_actual_params = len(value.info[0])
        if num_actual_params < num_given_params:
            error_message("Type Checking",
                          f"Constructor was called with too many argumnets.",
                          t.lineno)
        elif num_actual_params > num_given_params:
            error_message("Type Checking",
                          f"Constructor was called with too few arguments.",
                          t.lineno)
        elif not self._param_type_match(value.info[0], t.params):
            error_message("Type Checking",
                          f"Type of parameters given does not match parameters needed.",
                          t.lineno)
        
        # if everything checks out maybe do something cool???

    def postVisit_expression_attribute(self, t):
        self._exist_membership(t, "attribute")

    def preVisit_expression_method(self, t):
        self.number_of_actual_parameters.append(0)
        self._exist_membership(t, "method")

    def postVisit_expression_method(self, t):
        self.number_of_actual_parameters.pop()


    # The auxiliaries
    def _getLen(self, params):
        num_params = 0
        current = params
        while current:
            num_params += 1
            current = current.next
        return num_params
    
    def _param_type_match(self, a, b):
        matches = 0
        i = 0
        while i < len(a) and b and a[i][1] == b.exp.type:
            b.param = a[i][0] # assigns given param to actual param
            matches += 1
            b = b.next
            i += 1
        return len(a) == matches
    
    def _function_type_match_return_type(self, t):
        current = t.body.stm_list
        while current.next:
            current = current.next
        if not current.stm.exp.type == t.type:
            error_message("Type Checking",
                          f"Type of function and return statement does not match.",
                          t.lineno)
    
    # If expression_attribute and expression_method are deleted from _get_type delete this code as well
    #def _get_type_of_class(self, t, cat):
    #    idx = None
    #    if cat == "attribute":
    #        idx = 0
    #    elif cat == "method":
    #        idx = 1
    #    if idx == None:
    #        error_message("Type Checking",
    #                      f"Category '{cat}' given to find type of class resulted in None index.",
    #                      t.lineno)
    #    val = self._current_scope.lookup(t.inst).type[:-1]
    #    cd = self._current_scope.lookup(val).info[idx]
    #    for elem in cd:
    #        if t.field == elem[0]:
    #            return elem[1]



    def _get_type(self, t):
          match t.__class__.__name__:
            case "expression_new_instance":
                return t.struct + "*"
            case "expression_attribute":
                return t.type
            case "expression_method":
                return t.type
            case "expression_binop":
                return self._get_effective_type(self._get_type(t.lhs), self._get_type(t.rhs), t)
            case "expression_call":
                return self._current_scope.lookup(t.name).type
            case "attribute":
                return self._current_scope.parent.lookup_this_scope(t.attr).type
            case "expression_integer" | "expression_float" | "expression_boolean" | "expression_char":
                return t.type
            case "expression_identifier":
                return self._current_scope.lookup(t.identifier).type
            case "expression_group":
                # FIXME - evaluate expression group somehow or remove it from program in its entirity
                return None
            case _:
                  error_message("Type Checking", f"_get_type does not implement {t.__class__.__name__}", t.lineno)



    # FIXME - figure out if it is needed to check which operation is performed
    def _get_effective_type(self, type1, type2, t):
        match t.op:
            # These operators return a truth value which is represented as an integer
            case "==" | "!=" | "<" | ">" | "<=" | ">=":
                if type1 and type2:
                    return "int"
                else:
                    error_message("Type Checking",
                                  f"None type detected.",
                                  t.lineno)
                    
            # FIXME Maybe check for None type here as well or just do it in general before the match IDK ask Steffen
            case "/" | "*" | "+" | "-":
                if type1 == "int" and type2 == "int":
                    return "int"
                else: 
                    return "float"
                
    # Checks if instance trying to be accessed exits and has field as member
    def _exist_membership(self, t, cat):
        inst = self._current_scope.lookup(t.inst)
        if not inst:
            error_message("Type Checking", 
                          f"Instance {t.inst} not found.",
                          t.lineno)
        field = None
        if t.inst == "this": # Looking only through class attributes / methods
            field = self._current_scope.parent.lookup_this_scope(t.field)
            # FIXME - Should there be lookup into extensions when referencing "this"' attributes???? IDK ASK STEFFEN

        else: # Finding class the attribute / method should be part of and checking for membership
            desc = self._current_scope.lookup(inst.type[:-1])
            idx = 0 if cat == "attribute" else 1 # if not attribute then method
            name = t.field if cat == "attribute" else t.name
            while field == None:
                for elem in desc.info[idx]:
                    if elem[0] == name:
                        field = (elem[0], elem[1], NameCategory.ATTRIBUTE)
                        t.type = elem[1]
                        break # stops searching when first match found
                if field or len(desc.info[2]) == 0:
                    break # if member found stop looking or no more extension to look through 
                desc = self._current_scope.lookup(desc.info[2][0])
        if not field:
            error_message("Type Checking",
                          f"Identifier '{t.field}' not found.",
                          t.lineno)
        return field