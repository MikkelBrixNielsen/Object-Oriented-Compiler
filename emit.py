
# This module takes the intermediate code and outputs C code.

from code_generation import Op

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
        self.includes = ["#include <stdlib.h>", "\n#include <stdio.h>", "\n#include <stddef.h>"]
        self.signatures = ["\n"]
        self.classes = []
        self.code = []

    def emit(self):
        for instruction in self.intermediate_representation:
            self._dispatch(instruction)

    def get_code(self):
        self.includes.append("\n")
        self.signatures.append("\n")
        self.classes.append("\n")
        self.includes += self.signatures + self.classes + self.code
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

    def _raw2(self, s):
        self.classes.append(s)

    def _add(self, s, comment=""):
        self._addAux(s, self.code, comment)

    def _add2(self, s, comment=""):
        self._addAux(s, self.classes, comment)

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
                # FIXME - THIS IS FUCKING SHIT ADD2!??!?!? raw2 ?!?!?! WHAT EVEN IS THIS GARBAGE!?!?!?!?!
                case Op.CLASS:
                    self._createClassSignature(instr)
                    self._add2(f"struct {instr.args[0]}" + " {\n")
                    self.indent_level +=1
                case Op.CLASSMID:
                    self.indent_level -= 1
                    self._add2("};\n")
                case Op.TYPE2:
                    self._addType(instr, "2")
                case Op.EOL2:
                    self._raw2(";")
                case Op.VARLIST2:
                    self._create_varlist(instr, 2)
                case Op.VARLIST:
                    self._create_varlist(instr, 1)
                case Op.PARAMS:
                    self._addParam(instr)
                case Op.ASSIGN:
                    s = instr.args[0] + " = "
                    self._raw2(s) if len(instr.args) > 1 and instr.args[1] == 1 else self._raw(s)
                        
                case Op.INSTANCE:
                    struct = instr.args[0]
                    self._raw(f"({struct}*)" + f"malloc(sizeof({struct}));")
                case Op.ATTRASSIGN:
                    self._add(f"{instr.args[0]}->{instr.args[2]} = ")
                case Op.THIS:
                    self._raw("this->")
                case Op.TYPE:
                    self._addType(instr, "1")
                case Op.INDENT:
                    self._add("")
                case Op.SIGNATURE:
                    self._createFunctionSignature(instr)
                case Op.PRINT:
                    self._raw("\"" + _print_type[instr.args[0]] + "\\n\", ")
                case Op.START:
                    self._add(instr.args[0] + "(")
                case Op.PREMID:
                    self._raw(") {\n")
                case Op.MID:
                    self._add("} " + instr.args[0] + " {\n")
                case Op.END:
                    self._add("}\n\n")
                case Op.RPAREN:
                    self._raw(")")
                case Op.LPAREN:
                    self._raw("(")
                case Op.RCURL:
                    self._raw("}")
                case Op.LCURL:
                    self._raw("{")
                case Op.EOL:
                    self._raw(";")
                case Op.RET:
                    self._add("return ")
                case Op.IDT_M:
                    self.indent_level -= 1
                case Op.IDT_P:
                    self.indent_level += 1
                case Op.COMMA:
                    if instr.args[0]:
                        self._raw(", ")
                case Op.RAW:
                    s = str(instr.args[0])
                    self._raw2(s) if len(instr.args) > 1 and instr.args[1] == 1 else self._raw(s)
                case _:
                    print(f"ERROR {instr.opcode} NOT DEFINED!")

    def _simpleInstruction(self, instr):
        self._raw(f" {_intermediate_to_C[instr.opcode]} ")

    # FIXME - WHAT EVEN THE FUCK IS THIS DUPLICATED CASES WHAT THE ACTUAL FUCKING SHIT IS THIS OMG I HATE IT SO MUCH FUCKING FIX THIS EXTREME PILE OF DOGSHIT
    def _addType(self, instr, flag):
        type = instr.args[0]
        if flag == "1":
            match type:
                case "bool":
                    self._add("int", "Were boolean variables in source code")
                case _:
                    self._add(type)
        else:
            match type:
                case "bool":
                    self._add2("int", "Were boolean variables in source code")
                case _:
                    self._add2(type)

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

    def _createClassSignature(self, instr):
        self._addSignature(("typedef struct " + (instr.args[0] + " ")*2)[:-1] + ";")

    def _formatParams(self, params):
        current = params
        s = ""
        while (current):
            s += current.type + " " + current.parameter
            if current.next:
                s += ", "
            current = current.next
        return s    
    
    def _create_varlist(self, instr, flag):
        s = instr.args[0]
        if instr.args[1]:
            s += ","
        self._raw(" " + s) if flag == 1 else self._raw2("" + s)