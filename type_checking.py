from visitors_base import VisitorsBase
from errors import error_message
from symbols import NameCategory, _lookup_in_extensions, _get_identifier

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
            #if t.lhs.type[-2:] == "[]":
            #    error_message("Type Checking",
            #                  f"Assignment to expression with array type", 
            #                  t.lineno)
            lhs = self._exist_membership(t.lhs, "attribute")
        elif t.lhs.__class__.__name__ == "expression_array_indexing":
            ident = _get_identifier(t.lhs.identifier)
            ident = ident if not isinstance(ident, tuple) else ident[0]
            lhs = self._current_scope.lookup(ident)
            if lhs:
                lhs = [ident, t.lhs.type, lhs.cat]
        else: 
            lhs = self._current_scope.lookup(t.lhs)
            if lhs:
                lhs = [t.lhs, lhs.type, lhs.cat]

        if not lhs:
            error_message("Type Checking",
                          f"Variable '{t}' not found.",
                          t.lineno)
        #if lhs[2] == NameCategory.PARAMETER:
        #    error_message("Type Checking",
        #                  f"Assignment to parameter '{lhs[0]}' not allowed.",
        #                  t.lineno)
        if lhs[2] == NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Assignment to function '{lhs[0]}' not allowed.",
                          t.lineno)
        # check whether what is being assigned has the same type as what is being assigned to
        t_lhs = lhs[1]
        t_rhs = self._get_type(t.rhs)
        cnr = t.rhs.__class__.__name__

        if not t_lhs == t_rhs and not (t_lhs == "int" and t_rhs == "float" or t_lhs == "float" and t_rhs == "int"):
            if cnr == "expression_call" or cnr == "expression_method":
                self._function_type_match_return_type(self._current_scope.lookup(t.rhs.name).info)
            error_message("Type Checking",
                          f"Incorrect assignment: Assigning type {t_rhs} to type {t_lhs}",
                          t.rhs.lineno)
        #self._value_has_been_assigned(t)
    
    # after expression has been evaluated check if it can be evaluated to boolean 
    def preMidVisit_statement_ifthenelse(self, t):
        self._is_boolean_convertable(t)

    def midVisit_statement_while(self, t):
        self._is_boolean_convertable(t)

    def preVisit_statement_call(self, t):
        self.preVisit_expression_call(t)

    def postVisit_statement_call(self, t):
        self.postVisit_expression_call(t)

    def preVisit_statement_method(self, t):
        self.preVisit_expression_method(t)

    def postVisit_statement_method(self, t):
        self.postVisit_expression_method(t)

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
        if val.cat != NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Identifier '{t.name}' is not a function.",
                          t.lineno)
        t.type = val.info.type
        self.number_of_actual_parameters.append(0)

    def postVisit_expression_call(self, t):
        value = self._current_scope.lookup(t.name)
        node = value.info
        nnop = node.number_of_parameters - 1 if hasattr(node, "parent") else node.number_of_parameters
        snoap = self.number_of_actual_parameters[-1]
        if snoap < nnop:
            error_message("Type Checking",
                          f"Function '{t.name}' was called with too few parameters.",
                          t.lineno)
        elif snoap > nnop:
            error_message("Type Checking",
                          f"Function '{t.name}' was called with too many parameters.",
                          t.lineno)
        self.number_of_actual_parameters.pop()
        res = self._check_params_match_function(t)
        if res[0]:
            error_message("Type Checking",
                          f"Type of given parameter '{res[2]}' does not match type needed '{res[1]}'",
                          t.lineno)

    def midVisit_expression_list(self, t):
        self.number_of_actual_parameters[-1] += 1

    def postVisit_expression_binop(self, t):
        t_lhs = self._get_type(t.lhs)
        t_rhs = self._get_type(t.rhs)
        if (t_lhs != "int" and t_lhs != "float"):
            error_message("Type Checking",
                          f"Expression of type '{t_lhs}' not allowed in binop.",
                          t.lineno)
        if (t_rhs != "int" and t_rhs != "float"):
            error_message("Type Checking",
                          f"Expression of type '{t_rhs}' not allowed in binop.",
                          t.lineno)
        t.type = self._get_effective_type(t_lhs, t_rhs, t)
                        
    def postVisit_expression_new_instance(self, t):
        value = self._current_scope.lookup_all(t.struct)
        if not value:
            error_message("Type Checking",
                          f"Class {t.struct} not found.",
                          t.lineno)
        elif not value.cat == NameCategory.CLASS:
            error_message("Type Checking",
                          f"Identifier {t.struct} is not a class.",
                          t.lineno)
        self._parameter_check(t.struct, t.params, value, t.lineno)

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
        cd = self._current_scope.lookup(self._current_scope.lookup_all(t.inst).type[:-1])
        meth = self._find_member_in_tuple_list((t.name, t.type), cd.info[1] + cd.info[3], "method")
        self._exp_check(t.name, t.exp_list, meth, t.lineno)   

    def postVisit_expression_method(self, t):
        self.number_of_actual_parameters.pop()
        self._check_params_match_function(t)

    def postVisit_expression_group(self, t):
        t.type = t.exp.type

    #def preVisit_array_list(self, t):
    #    if not str(t.type[:-2]) == t.exp.type:
    #        error_message("Type Checking",
    #                      f"Type mismatch assigning array of type {t.exp.type} to array of type {t.type}.",
    #                      t.lineno)
            
    #def postVisit_array_list(self, t):
    #    val = self._current_scope.lookup(t.variable)
    #    val.info[-2] = AST.expression_integer(self._get_value_of_binop(val.info[-2]), t.lineno)

    def preVisit_expression_new_array(self, t):
        self.number_of_actual_parameters.append(0)

    def postVisit_expression_new_array(self, t):
        if not self.is_integer(t.size):
            error_message("Type Checking",
                          f"Array size has to be an integer.",
                          t.lineno)
        # relics from when expression new arrays had data    
        #self._check_array_elements_match_type(t)
        #num_params = self.number_of_actual_parameters.pop()
        #needed =  self._get_value_if_any(t, t.lineno)
        # if there is an actual size to get this will be true and it will be compared
        # with num_params otherwise the size might be variable and first known at runtime 
        # which we cannot do much about
        #if needed[0]: 
        #    if num_params > needed[1]:
        #        error_message("Type Checking",
        #                      f"Too many elements given to array, recieved {num_params} expected at most {needed[1]}.",
        #                      t.lineno)
        t.type = t.type + "[]"

    # FIXME - if attribute array indexing is implemented add logic to use different 
    # lookup when array indexing is on an attribute array
    def postVisit_expression_array_indexing(self, t):
        ident = _get_identifier(t.identifier)
        ident = ident if not isinstance(ident, tuple) else ident[1]
        type = t.identifier.type if not isinstance(t.identifier, str) else t.type
        if not type[-2:] == "[]":
            error_message("Type Checking", 
                          f"cannot index into identifier '{ident}' - It is not an array.",
                          t.lineno)
        if not self.is_integer(t.idx):
            error_message("Type Checking",
                          f"Array index has to be an integer.",
                          t.lineno)
        if t.type[-2:] == "[]":
            t.type = t.type[:-2]
        #val = self._current_scope.lookup(t.identifier)
        #if val.cat != NameCategory.PARAMETER:
        #    self._is_idx_oob(t.idx, val)

    # TODO - 
        # Evaluate binary expression and determine if its result is dependent on a function or other variable-sized expression
        # if it is disallow it as size to array initialization
        # FIXME - when initialzing an array ensure that the given size is greater or equal to the number of elements given


    # The auxiliaries
    #def _check_array_elements_match_type(self, t):
    #    # checks the type of the expressions given as elements to the array match the array
    #    mismatched = False
    #    unsupported_type = False
    #    current = t.data
    #    while current:
    #        if not current.exp.type == t.type:
    #            mismatched = True
    #            break
    #        if current.exp.__class__.__name__ in ["expression_call", "expression_method",
    #                                                   "expression_new_instance", "expression_new_array"]:
    #            unsupported_type = True
    #            break
    #        current = current.next
    #    if mismatched:
    #        error_message("Type Checking",
    #                      f"'{current.exp.type}' does not match the type of the array being '{t.type}'.",
    #                      t.lineno)
    #    elif unsupported_type:
    #        s = str(current.exp.__class__.__name__).replace("_", " ")
    #        error_message("Type Checking",
    #                      f"'{s}' cannot be put into arrays.",
    #                      t.lineno)

    # FIXME- MIGHT BE USELESS SINCE NOTHING IS KNOWN IN REGARDS TO AN ARRAYS ELEMENTS 
    # WHEN GIVEN THE IDENTIFIER FOR THE ARRAY
    #def _is_idx_oob(self, t, val):
    #    cn = t.__class__.__name__
    #    match cn:
    #        case "expression_integer":
    #            if t.integer >= self._get_value_of_binop(val.info[-2]) or t.integer < 0:
    #                error_message("Type Checking",
    #                              "Array index out of bounds.",
    #                              t.lineno)
    #            return t.integer
    #        case "expression_binop":
    #            lhs = self._is_idx_oob(t.lhs, val)
    #            rhs = self._is_idx_oob(t.rhs, val)
    #            sum = rhs + lhs
    #            if sum >= self._get_value_of_binop(val.info[-2]) or sum < 0:
    #                error_message("Type Checking",
    #                              "Array index out of bounds.",
    #                              t.idx.lineno)
    #            return lhs + rhs
    #        case "expression_array_indexing":
    #            idx = self._is_idx_oob(t.idx, self._current_scope.lookup(t.identifier))
    #            if idx >= self._get_value_of_binop(val.info[-2]) or idx < 0:
    #                error_message("Type Checking",
    #                              "Array index out of bounds.",
    #                              t.idx.lineno)
    #            # find the integer value at idx in the array
    #            i = 0
    #            current = val.info[2]
    #            while current and i < idx:
    #                current = current.next
    #                i = i + 1
    #            if not current:
    #                error_message("Type Checking",
    #                              f"Accessing undeclared index '{i}' in {t.identifier}.",
    #                              t.lineno)
    #            return current.exp.integer
    #        case "expression_identifier":
    #            # Value of identifier might not be known before runtime so just return 0
    #            value = self._current_scope.lookup(t.identifier)
    #            if not value:
    #                error_message("Type Checking",
    #                              f"Identifier '{t.identifier}' not found.",
    #                              t.lineno)
    #            elif not value.assigned_value:
    #                error_message("Type Checking",
    #                              f"Undeclared '{t.identifier}' first use in function.",
    #                              t.lineno)
    #            return 0
    #        case "expression_attribute" | "expression_method":
    #            # check if attribute exists
    #            self._exist_membership(t, "method" if cn == "expression_method" else "attribute")
    #            # Value of attribute might not be known before runtime so just return 0
    #            return 0
    #        case "expression_call":
    #            # value returned by expression call may not be known before runtime so just return 0
    #            value = self._current_scope.lookup(t.name)
    #            if not value:
    #                 error_message("Type Checking",
    #                              f"Identifier '{t.name}' not found.",
    #                              t.lineno)
    #            return 0
    #        case _:
    #            error_message("Type Checking", 
    #                          f"Index out of bounds check is not implemented for {t.__class__.__name__}",
    #                          t.lineno)
      
    #def _value_has_been_assigned(self, t):
    #    lhs = t.lhs
    #    if t.lhs.__class__.__name__ == "expression_attribute":
    #        lhs = t.lhs.inst
    #    elif t.lhs.__class__.__name__ == "expression_array_indexing":
    #       lhs = t.lhs.identifier
    #    lhs = self._current_scope.lookup(lhs)
    #    lhs.assigned_value = t.rhs


    #def _get_value_if_any(self, t, lineno):
    #    tree = t.size
    #    cn = tree.__class__.__name__
    #    match cn:
    #        case "expression_integer" | "expression_boolean":
    #            return (True, tree.integer)
    #        case "expression_binop":
    #            if t.type == "int":
    #                value = self._get_value_of_binop(t.size)
    #                t.size = AST.expression_integer(value, t.lineno)
    #                return (True, value)
    #            else:
    #                error_message("Type Checking",
    #                          f"Cannot initialize array with non-integer value.",
    #                          lineno)
    #        case "expression_char" | "expression_float":
    #            error_message("Type Checking",
    #                          f"Cannot initialize array with non-integer value.",
    #                          lineno)
    #        case "expression_new_array":
    #            error_message("Type Checking",
    #                          f"Cannot initialize array with another array.",
    #                          lineno)
    #        case "expression_new_instance":
    #            error_message("Type Checking",
    #                          f"Cannot initialize array with an instance of a class.",
    #                          lineno)
    #        case "expression_call" | "expression_method" | "expression_identifier" | "expression_array_indexing" | "expression_attribute":
    #            #if t.data:
    #            #    error_message("Type Checking",
    #            #                  f"Variable-sized object may not be used to initialize array.",
    #            #                  lineno)
    #            #else:
    #            return (False, None)
    #        case _:
    #            error_message("Type Checking",
    #                          f"_get_value does not support {cn}",
    #                          lineno)

    #def _get_value_of_binop(self, t):
    #    cn = t.__class__.__name__
    #    match cn:
    #        case "expression_integer":
    #            return t.integer
    #        case "expression_binop":
    #            return self._get_value_of_binop(t.lhs) + self._get_value_of_binop(t.rhs)
    #        case "expression_array_indexing":
    #            idx = self._get_value_of_binop(t.idx)
    #            #info = self._current_scope.lookup(t.identifier)
    #            # find the integer value at idx in the array 
    #            #i = 0                   # Commented out due to data being commented out
    #            #current = info[2]
    #            #while i < idx:
    #            #    current = current.next
    #            #    i = i + 1
    #            #return current.exp.integer + idx
    #            return idx
    #        case "expression_identifier" | "expression_call" | "expression_attribute" | "expression_method":
    #            error_message("Type Checking",
    #                          f"Variable-sized object may not be used to initialize array",
    #                          t.lineno)
    #        case _:
    #            error_message("Type Checking", 
    #                          f"_approx_value_of_binop does not implemented {cn}",
    #                          t.lineno)

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
                case "expression_group":
                    is_convertable = t.exp.exp.type in immediate_conversion
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
    
    def _param_type_match(self, a, b, name):
        matches = 0
        i = 0
        while i < len(a) and b:
            exp_type = self._get_type(b.exp)
            if a[i][1] != exp_type:
                if "null" != exp_type:
                     break
                b.exp.type = a[i][1] # if exp_type == null -> null expression set type of null expression to type of parameter
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
                          f"Type of function and return does not match. Was given '{current.stm.exp.type}' expected '{t.type}'",
                          t.lineno)
            
    def _get_type(self, t):
          match t.__class__.__name__:
            case "expression_new_instance":
                t.type = t.struct + "*"
                return t.type
            case "expression_attribute":
                return t.type if t.type != None else self._exist_membership(t, "attribute")
            case "expression_method":
                return t.type if t.type != None else self._exist_membership(t, "method")
            case "expression_binop":
                t.type = self._get_effective_type(self._get_type(t.lhs), self._get_type(t.rhs), t)
                return t.type
            case "expression_call":
                t.type = self._current_scope.lookup(t.name).type
                return t.type
            case "expression_integer" | "expression_float" | "expression_boolean" | "expression_char" | "expression_new_array" | "expression_array_indexing" | "expression_group":
                return t.type
            case "expression_identifier":
                t.type = self._current_scope.lookup(t.identifier).type
                return t.type
            case "parameter_list":
                  return t.type
            case "expression_null":
                  return t.type
            case _:
                  error_message("Type Checking", f"_get_type does not implement {t.__class__.__name__}", t.lineno)

    def _get_effective_type(self, type1, type2, t):
        if not type1 or not type2:
            error_message("Type Checking",
                          f"None type detected.",
                          t.lineno)
        match t.op:
            # Comparison operators return a truth value (represented as int)
            case "==" | "!=" | "<" | ">" | "<=" | ">=":
                return "int"
            case "/":
                return "float"
            case "*" | "+" | "-":
                if type1 == "int" and type2 == "int":
                    return "int"
                else: 
                    return "float"
    

    # FIXME : IS THIS ENOUGH ------------------------------------------------------------------------------
    # Type checking does not seem to allow for attributes access more than 1 extension deep for some reason
    # Checks if instance trying to be accessed exits and has field as member
    def _exist_membership(self, t, cat):
        inst = None
        if t.inst == "this":
            # try to find attribute in this class scope
            inst = self._current_scope.lookup_class(t.field if cat == "attribute" else t.name)
            if not inst: # if attribute not in this class scope look through class' extensions
                inst = _lookup_in_extensions(self, t, t.__class__.__name__)
        else:
            inst = self._current_scope.lookup(t.inst)
        if not inst:
            error_message("Type Checking", 
                          f"Instance '{t.inst}' not found.",
                          t.lineno)
        field = None
        desc = None
        # Finding class the attribute / method should be part of and
        if t.inst == "this": 
            class_name = self._current_scope.lookup_this_scope(NameCategory.THIS).cat
            desc = self._current_scope.lookup_all(class_name)
        else: 
            if not inst.type[-1:] == "*":
                error_message("Type Checking",
                              f"Identifier '{t.inst}' is not an instance.",
                              t.lineno)
            desc = self._current_scope.lookup_all(inst.type[:-1])
        # checking for membership
        idx = 0 if cat == "attribute" else 1 # if not attribute then method
        name = t.field if cat == "attribute" else t.name
        while not field:
            for elem in desc.info[idx]:
                if elem[0] == name:
                    field = (elem[0], elem[1], NameCategory.ATTRIBUTE if idx == 0 else NameCategory.FUNCTION)
                    t.type = elem[1]
                    break # stops searching when first match found
            if field or len(desc.info[2]) == 0:
                break # if member found stop looking or no more extension to look through 
            desc = self._current_scope.lookup_all(desc.info[2][0])
        if not field:
            field = t.field if cat == "attribute" else t.name
            error_message("Type Checking",
                          f"Identifier '{field}' not found.",
                          t.lineno)
        return field
        
    def _find_member_in_tuple_list(self, m, tl, cat):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return member[2] if cat == "method" else member
        return None

    def _parameter_check(self, name, params, value, lineno):
        num_given_params = self._getLen(params)
        num_actual_params = len(value.info[0])
        if num_actual_params < num_given_params:
            error_message("Type Checking",
                          f"call to constructor for {name} made with too many argumnets.",
                          lineno)
        elif num_actual_params > num_given_params:
            error_message("Type Checking",
                          f"call to constructor for {name} made with too few arguments.",
                          lineno)
        elif not self._param_type_match(value.info[0], params, name):
            error_message("Type Checking",
                          f"Type of parameters given does not match parameters needed.",
                          lineno) 
            
    def _exp_check(self, name, exp_list, meth, lineno):
        num_given_params = self._getLen(exp_list)
        num_actual_params = self._getLen(meth.par_list) - 1 # minus 1 is to disregard the implicit reference to "this" methods get
        if num_actual_params < num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too many argumnets.",
                          lineno)
        elif num_actual_params > num_given_params:
            error_message("Type Checking",
                          f"call to {name} made with too few arguments.",
                          lineno)
        res = self._check_params_match_function_aux(meth.par_list.next, exp_list)
        if res[0]:
            error_message("Type Checking",
                          f"Type of given parameters '{res[2]}' does not match type needed '{res[1]}'.",
                          lineno) 

    def _check_params_match_function(self, t):
        cn = t.__class__.__name__
        if cn == "expression_method" or cn == "statement_method":
            val = self._current_scope.lookup(t.inst)
            if not val:
                error_message("Type Checking",
                              f"Identifier {t.inst} not found.",
                              t.lineno)
            cd = self._current_scope.lookup_all(val.type[:-1])
            if not cd:
                error_message("Type Checking",
                              f"No class with name '{val.type[:-1]}' found.",
                              t.lineno)
            par_list = None
            for elem in cd.info[1] + cd.info[3]:
                if elem[0] == t.name:
                    par_list = elem[2].par_list
            if not par_list:
                error_message("Type Checking",
                              f"No method with name '{t.name}' in class '{val.type[:-1]}'",
                              t.lineno)
            return self._check_params_match_function_aux(par_list, t.exp_list)
        else:
            val = self._current_scope.lookup(t.name)
            par_list = val.info.par_list
            if hasattr(val.info, "parent"):
                par_list = par_list.next
            return self._check_params_match_function_aux(par_list, t.exp_list)
        
    def _check_params_match_function_aux(self, par_list, exp_list):
        mismatched = False
        while par_list and exp_list:
            if self._get_type(par_list) != self._get_type(exp_list.exp):
                mismatched = True
                break
            par_list = par_list.next
            exp_list = exp_list.next
        if not par_list and exp_list:
            return (True, None, exp_list.exp.type)
        elif par_list and not exp_list:
            return (True, par_list.type, None)
        elif not par_list and not exp_list:
            return (False, None, None)
        else:
            return (mismatched, self._get_type(par_list), self._get_type(exp_list.exp))