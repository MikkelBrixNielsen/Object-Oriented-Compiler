from dataclasses import dataclass, field
from typing import Any

@dataclass
class global_body:
    variables_decl: Any
    assignment_list: Any
    class_decl: Any
    main_function: Any
    functions_decl: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.variables_decl:
            self.variables_decl.accept(visitor)
        if self.assignment_list:
            self.assignment_list.accept(visitor)
        if self.class_decl:
            self.class_decl.accept(visitor)
        if self.functions_decl:
            self.functions_decl.accept(visitor)
        if self.main_function:
            self.main_function.accept(visitor)
        visitor.postVisit(self)

@dataclass
class body:
    variables_decl: Any
    functions_decl: Any
    stm_list: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.variables_decl:
            self.variables_decl.accept(visitor)
        visitor.preMidVisit(self)
        if self.functions_decl:
            self.functions_decl.accept(visitor)
        #visitor.postMidVisit(self)
        if self.stm_list:
            self.stm_list.accept(visitor)
        #visitor.postVisit(self)

@dataclass
class variables_declaration_list:
    type: Any
    decl: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.decl.accept(visitor)
        visitor.midVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class variables_list:
    variable: Any
    next: Any
    lineno: int
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class functions_declaration_list:
    decl: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.decl.accept(visitor)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class function:
    type: Any
    name: Any
    par_list: Any
    body: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.par_list:
            self.par_list.accept(visitor)
        visitor.midVisit(self)
        self.body.accept(visitor)
        visitor.postVisit(self)

@dataclass
class parameter_list:
    type: Any
    parameter: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class class_declaration_list:
    decl: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.decl.accept(visitor)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)


@dataclass
class class_declaration:
    name: Any
    extends: Any
    descriptor: Any
    lineno: int
    
    def accept(self, visitor):
        visitor.preVisit(self)
        self.descriptor.accept(visitor)
        visitor.postVisit(self)        

@dataclass
class class_descriptor:
    attributes: Any
    methods: Any
    lineno: int
    name: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.attributes:
            self.attributes.accept(visitor)
        visitor.midVisit(self)
        if self.methods:
            self.methods.accept(visitor)
        visitor.postVisit(self)

@dataclass
class attributes_declaration_list:
    type: Any
    decl: Any
    next: Any
    lineno: int
    name: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.decl.accept(visitor)
        visitor.midVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class attributes_list:
    variable: Any
    next: Any
    lineno: int
    type: Any = field(default=None)
    name: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class methods_declaration_list:
    decl: Any
    next: Any
    lineno: int
    parent: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.decl.accept(visitor)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class method:
    type: Any
    name: Any
    par_list: Any
    body: Any
    lineno: int
    parent: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.par_list:
            self.par_list.accept(visitor)
        visitor.midVisit(self)
        self.body.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_attribute:
    inst: Any
    field: Any
    lineno: Any
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_method:
    inst: Any
    name: Any
    exp_list: Any
    lineno: Any
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp_list:
            self.exp_list.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_return:
    exp: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_print:
    exp: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp:
            self.exp.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_assignment:
    lhs: Any
    rhs: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.rhs.accept(visitor)
        #if not isinstance(self.lhs, str):  
        #    self.lhs.accept(visitor)
        visitor.midVisit(self)
        if not isinstance(self.lhs, str):  
            self.lhs.accept(visitor)
        #self.rhs.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_ifthenelse:
    exp: Any
    then_part: Any
    else_part: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.preMidVisit(self)
        self.then_part.accept(visitor)
        visitor.postMidVisit(self)
        self.else_part.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_while:
    exp: Any
    while_part: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.midVisit(self)
        self.while_part.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_call:
    name: str
    exp_list: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp_list:
            self.exp_list.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_method:
    inst: Any
    name: Any
    exp_list: Any
    lineno: Any
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp_list:
            self.exp_list.accept(visitor)
        visitor.postVisit(self)

@dataclass
class statement_list:
    stm: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.stm.accept(visitor)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class assignment_list:
    ass: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        self.ass.accept(visitor)
        if self.next:
            self.next.accept(visitor)

@dataclass
class expression_integer:
    integer: int
    lineno: int
    type: Any = field(default="int")

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_float:
    double: float
    lineno: int
    type: Any = field(default="float")

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_boolean:
    integer: int
    lineno: int
    type: Any = field(default="bool")

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_char:
    char: str
    lineno: int
    type: Any = field(default="char")

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_group:
    exp: Any
    lineno: int
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.postVisit(self)

@dataclass
class array_list:
    variable: Any
    type: Any
    exp: Any
    next: Any
    lineno: int
    name: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp:
            self.exp.accept(visitor)
        visitor.midVisit(self)
        if self.next:
            self.next.accpet(visitor)
        visitor.postVisit(self)

@dataclass
class expression_new_array:
    type: Any
    size: Any
    #data: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.size.accept(visitor)
        visitor.midVisit(self)
        #if self.data:
            #self.data.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_array_indexing:
    identifier: Any
    idx: Any
    lineno: int
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.idx.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_identifier:
    identifier: str
    lineno: int
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_call:
    name: str
    exp_list: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.exp_list:
            self.exp_list.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_binop:
    op: str
    lhs: Any
    rhs: Any
    lineno: int
    type: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.lhs.accept(visitor)
        visitor.midVisit(self)
        self.rhs.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_list:
    exp: Any
    next: Any
    lineno: int

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.midVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)

@dataclass
class expression_null:
    identifier: str
    lineno: int
    type: Any = field(default="null")
    
    def accept(self, visitor):
        visitor.postVisit(self)

@dataclass
class expression_new_instance:
    struct: Any
    params: Any
    lineno: int
    identifier: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        if self.params:
            self.params.accept(visitor)
        visitor.postVisit(self)

@dataclass
class instance_expression_list:
    exp: Any
    next: Any
    lineno: int
    struct: Any = field(default=None)
    param: Any = field(default=None)

    def accept(self, visitor):
        visitor.preVisit(self)
        self.exp.accept(visitor)
        visitor.midVisit(self)
        if self.next:
            self.next.accept(visitor)
        visitor.postVisit(self)