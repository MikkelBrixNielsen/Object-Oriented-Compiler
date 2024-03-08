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

    def postVisit_statement_assignment(self, t):
        lhs = self._current_scope.lookup(t.lhs)
        t_rhs = self.get_type(t.rhs)

        if not lhs:
            error_message("Symbol Collection",
                          f"Variable '{t.lhs}' not found.",
                          t.lineno)
        if lhs.cat == NameCategory.PARAMETER:
            error_message("Type Checking",
                          f"Assignment to parameter '{t.lhs}' not allowed.",
                          t.lineno)
        elif lhs.cat == NameCategory.FUNCTION:
            error_message("Type Checking",
                          f"Assignment to function '{t.lhs}' not allowed.",
                          t.lineno)
        ### check whether what is being assigned has the same type as what is being assigned to
        t_lhs = lhs.type
        if not t_lhs == t_rhs:
            error_message("Type Checking",
                          f"Incorrect assignment: Assigning type {t_rhs} to type {t_lhs}",
                          t.rhs.lineno)
            
    def postVisit_expression_identifier(self, t):
        value = self._current_scope.lookup(t.identifier)
        if not value:
            error_message("Symbol Collection",
                          f"Identifier '{t.identifier}' not found.",
                          t.lineno)
        if value.cat == NameCategory.FUNCTION:
            error_message(
                "Type Checking",
                f"Function name '{t.identifier}' cannot be an identifier.",
                t.lineno)

    def preVisit_expression_call(self, t):
        self.number_of_actual_parameters.append(0)

    def postVisit_expression_call(self, t):
        value = self._current_scope.lookup(t.name)
        if not value:
            error_message("Symbol Collection",
                          f"Function '{t.name}' not found.",
                          t.lineno)
        elif value.cat != NameCategory.FUNCTION:
            error_message("Symbol Collection",
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

    def midVisit_expression_list(self, t):
        self.number_of_actual_parameters[-1] += 1

    def postVisit_expression_binop(self, t):
        t.type = self.get_effective_type(self.get_type(t.lhs), self.get_type(t.rhs), t)

    def get_type(self, t):
          match t.__class__.__name__:
            case "expression_binop":
                return self.get_effective_type(self.get_type(t.lhs), self.get_type(t.rhs), t)
            case "expression_call":
                return self._current_scope.lookup(t.name).type
            case "expression_integer" | "expression_float" | "expression_boolean" | "expression_char":
                return t.type
            case "expression_identifier":
                return self._current_scope.lookup(t.identifier).type
            case "expression_group":
                # FIXME - evaluate expression groupe somehow
                return None
            case _:
                  error_message("Type Checking", f"get_type does not implement {t.__class__.__name__}", t.lineno)


    # FIXME - figure out if it is needed to check which operation is performed
    def get_effective_type(self, type1, type2, t):
        print(t)
        match t.op:
            case "==" | "!=" | "<" | ">" | "<=" | ">=":
                if type1 and type2:
                    return "int"
                else:
                    error_message("Type Checking",
                                  f"None type detected - please fix.",
                                  t.lineno)
            case "/" | "*" | "+" | "-":
                if type1 == "int" and type2 == "int":
                    return "int"
                else: 
                    return "float"
                """
                match type1+type2:
                    case "intfloat" | "floatint":
                        return "float"
                    case "intint":
                        return "int"
                    case "floatfloat":
                        return "float"
                    case "charint"
                        return "char"
                    case "intchar"
                        return "char"
                    case "charchar"
                        return "char"
                    # FIXME - IMPLEMENT FOR CHARS AND BOOLS
                    case _: # Default case throwss erros since not implemented / allowed
                        error_message("Type Checking", f"{t.op} is not defined for {type1} and {type2}", t.lineno)
                """
# FIXME     Something seems off with line numbers 
            # line number for some reason points 
            # to the next line of code after the 
            # line where the error actually occurred