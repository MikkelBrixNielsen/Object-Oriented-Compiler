from visitors_base import VisitorsBase

class LabelTable:
    _counter = "0000"
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

    # Inserts lables into table for the give name
    # and returns name with lable
    def insert(self, name):
        lable = self._numgen()
        self._tab[name] = lable
        return name + lable

    # Finds the lable corresponding to name if any exist
    # it returns name with lable otherwise returns name
    def lookup(self, name):
        if name in self._tab:
            return name + self._tab[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            return name
        
    # Generates the numbers for the lables 
    def _numgen(self):
        temp = int(LabelTable._counter) + 1
        counter = 0
        while temp > 0:
            temp = temp // 10
            counter = counter + 1
        LabelTable._counter = "0"*(4-counter) + str(int(LabelTable._counter) + 1)
        return "_" + LabelTable._counter

class ASTLabelGeneratorVisitor(VisitorsBase):
    def __init__(self):
        self._labels = LabelTable(None)
        self._temp_labels = LabelTable(None)
        self._comp_labels = LabelTable(None)

    # creates and enters a new scope
    def _enter_new_scope(self, t):
        # saves LabelTable in AST
        t._labels = self._labels
        t._temp_labels = self._temp_labels
        t._comp_labels = self._comp_labels

        # goes into the new scope
        self._current_scope = t.symbol_table
        self._labels = LabelTable(self._labels)
        self._temp_labels = LabelTable(self._temp_labels)
        self._comp_labels = LabelTable(self._comp_labels)
    
    # exits the current scope and goes to parent scope
    def _exit_current_scope(self, t):
        self._current_scope = self._current_scope.parent
        self._labels = self._labels.parent
        self._temp_labels = self._temp_labels.parent
        self._comp_labels = self._comp_labels.parent
    
    def preVisit_variables_list(self, t):
        self._labels.insert(t.variable)

    def preVisit_statement_assignment(self, t):
        self._temp_labels.insert("TEMP")

    def preVisit_statement_return(self, t):
        self._temp_labels.insert("TEMP")

    def preVisit_method(self, t):
        self._comp_labels.insert(t.name)
        self._enter_new_scope(t)

    def postVisit_method(self, t):
        self.postVisit_function(t)

    def preVisit_function(self, t):
        if t.scope_level > 0: # functions defined instide the global scope (so all functions excluding the implicit function for global scope)
            if not t.name == "main" or t.scope_level > 1:
                self._labels.insert(t.name)
        self._enter_new_scope(t)
    
    def postVisit_function(self, t):
        self._exit_current_scope(t)

    def preVisit_expression_new_instance(self, t):
        self._extension_instance(t)
        self._enter_new_scope(t)

    def _extension_instance(self, t):
        current = self._current_scope.lookup(t.struct)
        while len(current.info[2]) > 0:
            self._temp_labels.insert(current.info[2][0].lower())
            super = self._current_scope.lookup(current.info[2][0])
            for attr in super.info[0]:
                if attr[1][-1] == "*":
                    self._temp_labels.insert(attr[1][:-1].lower())
            current = self._current_scope.lookup(current.info[2][0])