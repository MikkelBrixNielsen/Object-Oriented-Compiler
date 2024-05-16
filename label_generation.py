from visitors_base import VisitorsBase

class LabelGenerator:
    _counter = "0000"
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

    # Inserts lables into table for the give name
    # and returns name with lable
    #def insert(self, name):
    #    lable = self._numgen()
    #    self._tab[name] = lable
    #    return name + lable

    # Finds the lable corresponding to name if any exist
    # it returns name with lable otherwise returns name
    #def lookup(self, name):
    #    if name in self._tab:
    #        return name + self._tab[name]
    #    elif self.parent:
    #        return self.parent.lookup(name)
    #    else:
    #        return name
        
    # Generates label 
    def _generate():
        temp = int(LabelGenerator._counter) + 1
        counter = 0
        while temp > 0:
            temp = temp // 10
            counter = counter + 1
        LabelGenerator._counter = "0"*(4-counter) + str(int(LabelGenerator._counter) + 1)
        return "_" + LabelGenerator._counter

class ASTLabelGeneratorVisitor(VisitorsBase):
    def __init__(self):
        self. label_generator = LabelGenerator
        self._current_scope = None

    # creates and enters a new scope
    #def _enter_new_scope(self, t):
    #    # saves LabelTable in AST
    #    t._labels = self._labels
    #    t._temp_labels = self._temp_labels
    #    t._comp_labels = self._comp_labels

    #    # goes into the new scope
    #    self._current_scope = t.symbol_table
    #    self._labels = LabelTable(self._labels)
    #    self._temp_labels = LabelTable(self._temp_labels)
    #    self._comp_labels = LabelTable(self._comp_labels)
    
    # exits the current scope and goes to parent scope
    #def _exit_current_scope(self, t):
    #    self._current_scope = self._current_scope.parent
    #    self._labels = self._labels.parent
    #    self._temp_labels = self._temp_labels.parent
    #    self._comp_labels = self._comp_labels.parent
    
    def preVisit_variables_list(self, t):
        t.label = self.label_generator._generate()
        self._current_scope.lookup_this_scope(t.variable).label = t.label

    def preVisit_statement_assignment(self, t):
        # generate lable for temp variable
        t.label = self.label_generator._generate()

    def preVisit_statement_return(self, t):
        # generate lable for temp variable
        t.label = self.label_generator._generate()

    def preVisit_method(self, t):
        self._generate_and_set_label_if_none(t, t)
        self._current_scope.lookup_this_scope(t.name).label = t.label
        self._current_scope = t.symbol_table

    def postVisit_method(self, t):
        self.postVisit_function(t)

    def postVisit_expression_identifier(self, t):
        t.label = self.label_generator._generate()
        self._current_scope.lookup_this_scope(t.identifier).label = t.label

    def preVisit_function(self, t):
        if t.scope_level > 0: # functions defined inside the global scope (so all functions excluding the implicit function for global scope)
            if not t.name == "main" or t.scope_level > 1: # don't generate label for required main function
                self._generate_and_set_label_if_none(t, t)
                self._current_scope.lookup(t.name).label = t.label
        self._current_scope = t.symbol_table
    
    def postVisit_function(self, t):
        self._current_scope = self._current_scope.parent

    def preVisit_class_declaration(self, t):
        self._current_scope = t.symbol_table

    def preVisit_expression_method(self, t):
        self.preVisit_statement_method(t)
    
    def preVisit_statement_method(self, t):
        cd = self._current_scope.lookup_all(self._current_scope.lookup_this_scope(t.inst).type[:-1])
        member = self._find_member_in_tuple_list((t.name, t.type), cd.info[1] + cd.info[3], "method")
        self._generate_and_set_label_if_none(member, t)

    def preVisit_expression_array_indexing(self, t):
        if isinstance(t.identifier, str):
            if t.identifier != "this":
                t.label = self._current_scope.lookup(t.identifier).label
            else:
                t.label = ""

    def preVisit_expression_new_instance(self, t):
        self._extension_instance(t)
        self._current_scope = t.symbol_table

    def _extension_instance(self, t):
        current = self._current_scope.lookup(t.struct)
        while len(current.info[2]) > 0:
            self._temp_labels.insert(current.info[2][0].lower())
            super = self._current_scope.lookup(current.info[2][0])
            for attr in super.info[0]:
                if attr[1][-1] == "*":
                    self._temp_labels.insert(attr[1][:-1].lower())
            current = self._current_scope.lookup(current.info[2][0])

    def _find_member_in_tuple_list(self, m, tl, cat):
        for member in tl:
            if member[0] == m[0] and member[1] == m[1]:
                return member[2] if cat == "method" else member
        return None

    def _generate_and_set_label_if_none(self, member, t):
        if hasattr(member, "label"):
            t.label = member.label
        else:
            member.label = LabelGenerator._generate()
        t.label = member.label