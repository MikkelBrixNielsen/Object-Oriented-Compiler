from code_generation import Op
from symbols import PRIM_TYPES

_intermediate_to_C = {
    Op.ADD: "+",
    Op.SUB: "-",
    Op.MUL: "*",
    Op.DIV: "/",
    Op.EQ: "==",
    Op.NEQ: "!=",
    Op.LT: "<",
    Op.LTE: "<=",
    Op.GT: ">",
    Op.GTE: ">=",
    }

_print_type = {
    "int": "%d",
    "float": "%f",
    "char": "%c",
    "bool": "%d",
    "string": "%s",
    "*": "%p",
}

# Emitting
class Emit:
    """The class that emits C code
    """
    def __init__(self, intermediate_representation):
        self.intermediate_representation = intermediate_representation
        self.max_width = 80
        self.indent = 4
        self.indent_level = 0
        self.includes = ["#include <stdlib.h>", "\n#include <stdio.h>", "\n#include <stddef.h>"]
        self.signatures = ["\n"]
        self.code = []

    def emit(self):
        for instruction in self.intermediate_representation:
            self._dispatch(instruction)

    def get_code(self):
        self.includes.append("\n")
        self.signatures.append("\n")
        self.includes += self.signatures + self.code
        return "".join(self.includes).replace(";", ";\n")

    def _format_comment(self, comment):
        """Formats comments that would make the total line length too large
           by using multiple lines.
        """
        indent = self.indent * self.indent_level
        width = self.max_width - indent
        page = []
        line = ""
        for word in comment.split():
            if not line:
                line += word
            else:
                if len(line) + 1 + len(word) <= width:
                    line += " " + word
                else:
                    page.append(line)
                    line = word
        if line:
            page.append(line)
        for i in range(len(page)):
            page[i] = indent * " " +  "// " + page[i] + "\n"
        return "".join(page)

    def _raw(self, s):
        self.code.append(s)

    def _add(self, s, comment=""):
        self._addAux(s, self.code, comment)

    def _addSignature(self, s, comment=""):
        temp = self.indent_level
        self.indent_level = 0
        self._addAux(s, self.signatures, comment)
        self.indent_level = temp

    def _addAux(self, s, text, comment=""):
        if not comment == "":
            text.append(self._format_comment(comment))
        text.append(self.indent * " " * self.indent_level + s)

    # Emitting intermediate representation instructions:
    def _dispatch(self, instr): 
        if instr.opcode in _intermediate_to_C:
            self._simpleInstruction(instr)
        else:
            match instr.opcode:
                case Op.CLASS:
                    self._createClassSignature(instr)
                    self._add(f"struct {instr.args[0]}" + " {\n")
                    self.indent_level +=1
                case Op.CLASSMID:
                    self.indent_level -= 1
                    self._add("};\n")
                case Op.VARLIST:
                    self._create_varlist(instr, True)
                case Op.ATTRLIST:
                    self._create_varlist(instr, False)
                case Op.PARAMS:
                    self._addParam(instr)
                case Op.TEMP:
                    self._create_varlist(instr, False)
                case Op.ASSIGN:
                    self._raw(f"{instr.args[0]} = ")
                case Op.ATTRASSIGN:
                    self._add(f"{instr.args[0]}->{instr.args[2]} = ")
                case Op.THIS:
                    self._raw("this->")
                case Op.TYPE:
                    self._addType(instr)
                case Op.INDENT:
                    self._add("")
                case Op.SIGNATURE:
                    self._createFunctionSignature(instr)
                case Op.PRINT:
                    t = instr.args[0]
                    if len(self._get_stars(t)) > 0:
                        t = "*"    
                    s = "\"" + _print_type[t] + "\\n\", "
                    if t == "*":
                        s = s + "(void*)"
                    self._raw(s)
                case Op.START:
                    stars = self._get_stars(instr.args[1])
                    s = str(instr.args[0])
                    if len(stars) > 0:
                        s = " " + stars + instr.args[0].strip()
                    s = s + "("
                    self._raw(s) if instr.args[-1] else self._add(s)
                case Op.PREMID:
                    self._raw(") {\n")
                case Op.MID:
                    self._add("} " + str(instr.args[0]) + " {\n")
                case Op.END:
                    self._add("}\n\n")
                case Op.RET:
                    self._add("return ")
                case Op.IDTL_M:
                    self.indent_level -= 1
                case Op.IDTL_P:
                    self.indent_level += 1
                case Op.COMMA:
                    if instr.args[0]:
                        self._raw(", ")
                case Op.RAW:
                    self._raw(str(instr.args[0]))
                case Op.ALLOC:
                    arg1 = self._is_bool_then_convert_to_int(instr.args[0])
                    arg2 = self._is_bool_then_convert_to_int(instr.args[1])
                    self._raw(f"({arg1})malloc(sizeof({arg2}));")
                case Op.ALLOCSTART:
                    type = instr.args[0].replace("[]", "*")
                    type = self._is_bool_then_convert_to_int(type)
                    self._raw(f"({type})malloc((")
                case Op.ALLOCEND:
                    type = instr.args[0].replace("[]", "*")
                    type = self._is_bool_then_convert_to_int(type)
                    self._raw(f")*sizeof({type}))")
                case Op.MEMCHECK:
                    self._add(f"if ({instr.args[0]} == NULL)" + " {\n")
                    self.indent_level += 1
                    self._add("fprintf(stderr, \"Memory allocation failed.\");")
                    self.indent_level -= 1
                    self._add("}\n")
                case Op.FREE:
                    self._add(f"free({instr.args[0]});")
                case Op.DEFAULTVAL:
                    self._raw(self._generate_default_value(instr.args[0]))
                case _:
                    print(f"ERROR {instr.opcode} NOT DEFINED!")

    def _simpleInstruction(self, instr):
        self._raw(f" {_intermediate_to_C[instr.opcode]} ")

    def _addType(self, instr):
        type = instr.args[0].replace("[]", "").replace("*", "")
        match type:
            case "bool":
                self._add("int", "Was boolean variables in source code")
            case _:
                self._add(type)

    def _addParam(self, instr):
        type = str(instr.args[0]).replace("*", "").replace("[]", "")
        stars = self._get_stars(instr.args[0])
        type = "int" if type == "bool" else type
        s = type + " " + stars + instr.args[1]
        if instr.args[2]:
            s += ", "
        self._raw(s)

    def _createFunctionSignature(self, instr):
        stars = self._get_stars(instr.args[0])
        type = str(instr.args[0]).replace("[]", "").replace("*", "")
        type = "int" if type == "bool" else type
        if not instr.args[1] == "main":
            params = self._formatParams(instr.args[2])
            s = type + " " + stars + instr.args[1] + "(" + params + ");"
            self._addSignature(s)

    def _createClassSignature(self, instr):
        self._addSignature(("typedef struct " + (instr.args[0] + " ")*2)[:-1] + ";")

    def _formatParams(self, params):
        current = params
        s = ""
        while (current):
            type = current.type.replace("*", "").replace("[]", "")
            type = "int" if type == "bool" else type
            s += type + " " + self._get_stars(current.type)  + current.parameter
            if current.next:
                s += ", "
            current = current.next
        return s    
    
    def _create_varlist(self, instr, defval=False):
        s = self._get_stars(instr.args[2]) + instr.args[0]
        if instr.args[2] not in PRIM_TYPES and defval:
            s += " = " + self._generate_default_value(instr.args[2])
        if instr.args[1]:
            s += ","
        self._raw(" " + s)
    
    def _create_temp_var(self, instr):
        s = self._get_stars(instr.args[2]) + instr.args[0]
        if instr.args[1]:
            s += ","
        self._raw(" " + s)

    def _get_stars(self, type):
        return (len(str(type).replace("[]", "*").split("*")) - 1) * "*"
    
    def _is_bool_then_convert_to_int(self, type):
        temp = str(type).replace("[]", "").replace("*", "")
        if temp == "bool":
            return "int" + self._get_stars(type)
        return type

    def _generate_default_value(self, type):
        match (type):
            case "float":
                return "0.0"
            case "char":
                return "'\\0'"
            case _: # ints, bools, array pointers, struct pointers
                return "0"