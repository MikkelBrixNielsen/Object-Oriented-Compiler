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
        self._function_type_match_return_type(t)

    def postVisit_statement_assignment(self, t):
        lhs = None
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
            cn = t.__class__.__name__
            if cn == "expression_call" or cn == "expression_method":
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
        val = self._current_scope.lookup(t.name)
        if not val:
            error_message("Type Checking", 
                          f"Function '{t.name}' not found.",
                          t.lineno)

        t.type = val.info.type
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
        # FIXME - Check parameter types actually match what is needed compared to what was given :))
        # This is implemented for class constructors so maybe that can be used here as well 

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
        self._parameter_check("constructor for " + t.struct, t.params, value, t.lineno)

    def postVisit_expression_attribute(self, t):
        self._exist_membership(t, "attribute")

    def preVisit_expression_method(self, t):
        self.number_of_actual_parameters.append(0)
        member = self._exist_membership(t, "method")
        if not member:
            error_message("Type Checking",
                          f"Function '{t.name}' not found.",
                          t.lineno)
        elif member[2] != NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Identifier '{t.name}' is not a function.",
                          t.lineno)
        cd = self._current_scope.lookup(self._current_scope.lookup(t.inst).type[:-1])
        meth = self._find_member_in_tuple_list((t.name, t.type), cd.info[1])
        if not meth:
            meth = self._find_member_in_tuple_list((t.name, t.type), cd.info[3])
        self._exp_check(t.name, t.exp_list, meth, t.lineno)   

    def postVisit_expression_method(self, t):
        self.number_of_actual_parameters.pop()

    # after expression has been evaluated check if it can be evaluated to boolean 
    def preMidVisit_statement_ifthenelse(self, t):
        self._is_boolean_convertable(t)

    def midVisit_statement_while(self, t):
        self._is_boolean_convertable(t)








    # TODO - ARRAY OUT OF BOUNDS TYPE CHECKING TO THE DEGREE IT IS POSSIBLE
        #val = self._current_scope.lookup(t.identifier)
        #if not val.cat == NameCategory.PARAMETER:
        #    size_of_self = 0
        #    current = val.info[-3]
        #    while current:
        #        current = current.next
        #        size_of_self += 1
        #if not val.cat == NameCategory.PARAMETER and isinstance(t.idx, int) and val.info[-2] <= t.idx:
        #    error_message("Symbol Collection",
        #                  f"Index out of bounds s[{t.idx}]: '{t.identifier}' has {val.info[-2]} elements",
        #                  t.lineno)
                
                # THE THIGNS I THINK IT MIGHT BE POSSIBLE FOR
                # expression integer 
                # identifier
                # expression_array_indexing
                # expression_attribute
                # binop when lhs and rhs is one of the above


    def preVisit_array_list(self, t):
        if not str(t.type[:-2]) == t.exp.type:
            error_message("Type Checking",
                          f"Type mismatch assigning array of type {t.exp.type} to array of type {t.type}.",
                          t.lineno)

    def preVisit_expression_new_array(self, t):
        self.number_of_actual_parameters.append(0)

    def postVisit_expression_new_array(self, t):
        if not self.is_integer(t.size):
            error_message("Type Checking",
                          f"Array size has to be an integer.",
                          t.lineno)
        mismatched = False
        current = t.data
        while current:
            if not current.exp.type == t.type:
                mismatched = True
                break
            current = current.next
        
        if mismatched:
            error_message("Type Checking",
                          f"{current.exp.type} does not match the type of the array being {t.type}.",
                          t.lineno)
        num_params = self.number_of_actual_parameters.pop()
        needed =  self._get_value_if_any(t, t.lineno)
        # if there is an actual size to get this will be true and it will be compared
        # with num_params otherwise the size might be variable and first known at runtime 
        # which we cannot do much about
        if needed[0]: 
            if num_params > needed[1]:
                error_message("Type Checking",
                              f"Too many elements given to array, recieved {num_params} expected at most {needed[1]}.",
                              t.lineno)
        t.type = t.type + "[]"

    def postVisit_expression_array_indexing(self, t):
        if not self.is_integer(t.idx):
            error_message("Type Checking",
                          f"Array index has to be an integer.",
                          t.lineno)
        t.type = t.type[:-2]

    def postVisit_attributes_declaration_list(self, t):
        #type = None
        #if  hasattr(t.decl, "exp") and t.decl.exp.size.__class__.__name__ == "expression_binop" and not t.decl.exp.size.type == "int":
        #    type = self._get_type(t.decl.exp.size)
        
        # FIXME - if there is a variabl-sized paramter in the binop thrown an error 
                # all expression involved in the binop should have a static value (known at compile time)
        # FIXME - Get the type of the binop 

        if hasattr(t.decl, "exp") and t.decl.exp.size.__class__.__name__ == "expression_binop":
            type = self._get_type(t.decl.exp.size)
            if not type == "int":
                error_message("Type Checking",
                              "Cannot initialize array with non-integer value",
                              t.decl.lineno)
















    # The auxiliaries
    def _get_value_if_any(self, t, lineno):
        tree = t.size
        cn = tree.__class__.__name__
        match cn:
            case "expression_integer" | "expression_boolean":
                return (True, tree.integer)
            case "expression_binop":

                # FIXME - Traverse the binop and determine its effective type and the type of any functions etc.
           
           
                if t.type == "int":
                    return (False, None)
                else:
                    error_message("Type Checking",
                              f"Cannot initialize array with non-integer value.",
                              lineno)
           

            
            case "expression_char" | "expression_float":
                error_message("Type Checking",
                              f"Cannot initialize array with non-integer value.",
                              lineno)
            case "expression_new_array":
                error_message("Type Checking",
                              f"Cannot initialize array with another array.",
                              lineno)
            case "expression_new_instance":
                error_message("Type Checking",
                              f"Cannot initialize array with an instance of a class.",
                              lineno)
            case "expression_call" | "expression_method" | "expression_identifier" | "expression_array_indexing" | "expression_attribute":
                if t.data:
                    error_message("Type Checking",
                                  f"Variable-sized object may not be initialized.",
                                  lineno)
                else:
                    return (False, None)
            case _:
                error_message("Type Checking",
                              f"_get_value does not support {cn}",
                              lineno)

    def is_integer(self, t):
        return self._get_type(t) == "int"

    def _is_boolean_convertable(self, t):
        immediate_conversion = ["int", "float", "char", "expression_integer", "expression_float", 
                                "expression_bool", "expression_char"]
        is_convertable = False
        type = None
        if t.exp.__class__.__name__ in immediate_conversion:
            is_convertable = True
        else:
            match t.exp.__class__.__name__:
                case "expression_identifier" | "expression_attribute" | "expression_method":
                    is_convertable = t.exp.type in immediate_conversion
                    if not is_convertable:
                        is_convertable = not t.exp.type == None
                case "expression_call":
                    value = self._current_scope.lookup(t.exp.name)
                    if value:
                        is_convertable = value.type
                    else:
                        is_convertable = False
                case "expression_binop":
                    type = self._get_effective_type(t.exp.lhs.type, t.exp.rhs.type, t.exp)
                    is_convertable = type in immediate_conversion
                case "expression_new_instance":
                    # Design choice "new" instantiations should not evaluate to anything boolean
                    is_convertable = False
                case _:
                    error_message("Type Checking",
                            f"'{t.exp.__class__.__name__}' is not implemented for boolean conversion check in if statements.",
                            t.lineno)
        if not is_convertable:
            error_message("Type Checking",
                          f"'{type}' is not convertable to Bool.",
                          t.lineno)
            
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
            
    def _get_type(self, t):
          match t.__class__.__name__:
            case "expression_new_instance":
                return t.struct + "*"
            case "expression_attribute":
                return t.type if t.type != None else self._exist_membership(t, "attribute")
            case "expression_method":
                return t.type if t.type != None else self._exist_membership(t, "method")
            case "expression_binop":
                return self._get_effective_type(self._get_type(t.lhs), self._get_type(t.rhs), t)
            case "expression_call":
                return self._current_scope.lookup(t.name).type
            case "expression_integer" | "expression_float" | "expression_boolean" | "expression_char" | "expression_new_array" | "expression_array_indexing":
                return t.type
            case "expression_identifier":
                return self._current_scope.lookup(t.identifier).type
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
        desc = None
        # Finding class the attribute / method should be part of and
        if t.inst == "this": 
            class_name = self._current_scope.lookup(NameCategory.THIS).cat
            desc = self._current_scope.lookup(class_name)
        else: 
            desc = self._current_scope.lookup(inst.type[:-1])
        # checking for membership
        idx = 0 if cat == "attribute" else 1 # if not attribute then method
        name = t.field if cat == "attribute" else t.name
        while field == None:
            for elem in desc.info[idx]:
                if elem[0] == name:
                    field = (elem[0], elem[1], NameCategory.ATTRIBUTE if idx == 0 else NameCategory.FUNCTION)
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
    
    # PREVIOUS VERSION OF THE ABOVE METHOD
    #def _exist_membership(self, t, cat):
    #    inst = self._current_scope.lookup(t.inst)
    #    if not inst:
    #        error_message("Type Checking", 
    #                      f"Instance {t.inst} not found.",
    #                      t.lineno)
    #    field = None
    #    desc = None
    #    if t.inst == "this": # Looking only through class attributes / methods
    #        elem = (t.field if cat == "attribute" else t.name, None, NameCategory.ATTRIBUTE if cat == "attribute" else NameCategory.FUNCTION)
    #        field = self._current_scope.parent.lookup_this_scope(elem[0])
    #        if field:
    #            t.type = field.type
    #            field = (elem[0], field.type, elem[2])
    #    else: # Finding class the attribute / method should be part of and checking for membership
    #        desc = self._current_scope.lookup(inst.type[:-1])
    #    
    #        idx = 0 if cat == "attribute" else 1 # if not attribute then method
    #        name = t.field if cat == "attribute" else t.name
    #        while field == None:
    #            for elem in desc.info[idx]:
    #                if elem[0] == name:
    #                    field = (elem[0], elem[1], NameCategory.ATTRIBUTE if idx == 0 else NameCategory.FUNCTION)
    #                    t.type = elem[1]
    #                    break # stops searching when first match found
    #            if field or len(desc.info[2]) == 0:
    #                break # if member found stop looking or no more extension to look through 
    #            desc = self._current_scope.lookup(desc.info[2][0])
    #    
    #    if not field:
    #        error_message("Type Checking",
    #                      f"Identifier '{t.field}' not found.",
    #                      t.lineno)
    #    return field
    
    def _find_member_in_tuple_list(self, m, tl):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return member[2]
        return None

    def _parameter_check(self, name, params, value, lineno):
        num_given_params = self._getLen(params)
        num_actual_params = len(value.info[0])
        if num_actual_params < num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too many argumnets.",
                          lineno)
        elif num_actual_params > num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too few arguments.",
                          lineno)
        elif not self._param_type_match(value.info[0], params):
            error_message("Type Checking",
                          f"Type of parameters given does not match parameters needed.",
                          lineno) 
            
    def _exp_check(self, name, exp_list, meth, lineno):
        num_given_params = self._getLen(exp_list)
        num_actual_params = self._getLen(meth.par_list) - 1 # minus 1 is to disregard the implicit reference to "this"
        if num_actual_params < num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too many argumnets.",
                          lineno)
        elif num_actual_params > num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too few arguments.",
                          lineno)
        elif not self._exp_type_match(meth.par_list, exp_list):
            error_message("Type Checking",
                          f"Type of parameters given does not match parameters needed.",
                          lineno) 

    def _exp_type_match(self, a, b):
        a = a.next # disregards the imlicit reference to "this"
        while a and b and (a.type == b.exp.type):
            a = a.next
            b = b.next
        return a == None and b == None