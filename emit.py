
# This module takes the intermediate code and outputs C code.

from code_generation import Op #, T

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
    "char": "%s",
    "bool": "%d",
    "string": "%s",
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
        self.signatures = ["\n"]
        self.code = []

    def emit(self):
        for instruction in self.intermediate_representation:
            self._dispatch(instruction)

    def get_code(self):
        self.signatures.append("\n")
        self.signatures += self.code
        return "".join(self.signatures).replace(";", ";\n")

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
                case Op.TYPE:
                    self._addType(instr)
                case Op.EOL:
                    self._raw(";")
                case Op.INDENT:
                    self._add("")
                case Op.VARLIST:
                    self._addVar(instr)
                case Op.PARAMS:
                    self._addParam(instr)
                case Op.ASSIGN:
                    self._raw(instr.args[0] + " = ")
                case Op.FUNCSTART:
                    self.indent_level += 1
                    self._raw(" " + instr.args[0] + "(")
                case Op.FUNCMID:
                    self._raw(") {\n")
                case Op.FUNCEND:
                    self.indent_level -= 1
                    self._add("}\n\n")
                case Op.CLASS:
                    self._add(f"typedef struct {instr.args[0]}" + " {\n")
                    self.indent_level +=1
                case Op.CLASSMID:
                    self.indent_level -= 1
                    self._add("} " + f"{instr.args[0]}; \n")
                case Op.THIS:
                    self._raw("this->")
                    pass
                case Op.SIGNATURE:
                    self._createFunctionSignature(instr)
                case Op.PRINTSTART:
                    self._add("printf(" + _print_type[instr.args[0]] + ", ")
                case Op.PRINTEND:
                    self._raw(");")
                case Op.CALLSTART:
                    self._raw(instr.args[0] + "(")
                case Op.CALLEND:
                    self._raw(")")
                case Op.COMMA:
                    if instr.args[0]:
                        self._raw(", ")
                case Op.RAW:
                    self._raw(str(instr.args[0]))
                case Op.RET:
                    self._add("return ")
                case _:
                    print(f"ERROR {instr.opcode} NOT DEFINED!")

    def _simpleInstruction(self, instr):
        self._raw(f" {_intermediate_to_C[instr.opcode]} ")

    def _addType(self, instr):
        type = instr.args[0]
        match type:
            case "int" | "float" | "char" | "string": 
                self._add(type)
            case "bool":
                self._add("int", "Were boolean variables in source code")
    
    def _addVar(self, instr):
        s = instr.args[0]
        if instr.args[1]:
            s += ","
        self._raw(" " + s)

    def _addParam(self, instr):
        s = instr.args[0] + " " + instr.args[1]
        if instr.args[2]:
            s += ", "
        self._raw(s)

    def _createFunctionSignature(self, instr):
        if not instr.args[1] == "main":
            params = self._formatParams(instr.args[2])
            s = instr.args[0] + " " + instr.args[1] + "(" + params + ");"
            self._addSignature(s)

    def _formatParams(self, params):
        current = params
        s = ""
        while (current):
            s += current.type + " " + current.parameter
            if current.next:
                s += ", "
            current = current.next
        return s