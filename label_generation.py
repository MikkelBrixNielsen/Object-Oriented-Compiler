from visitors_base import VisitorsBase

class LabelGenerator:
    _counter = "0000"
    def __init__(self, parent):
        self._tab = {}
        self.parent = parent

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

    def preVisit_variables_list(self, t):
        t.label = self.label_generator._generate()
        self._current_scope.lookup_this_scope(t.variable).label = t.label
    
    def preVisit_attributes_list(self, t):
        self._generate_and_set_label_if_none(t, t)
        cd = self._current_scope.lookup_all(t.name).info   
        for i in range(len(cd[0])):
            if len(cd[0][i]) < 3 and cd[0][i][0] == t.variable and  cd[0][i][1] == t.type:
                cd[0][i] = (cd[0][i][0], cd[0][i][1], t.label)

    def preVisit_statement_assignment(self, t):
        # generate lable for temp variable
        if not hasattr(t, "temp_label"):
            t.temp_label = self.label_generator._generate()
        cn = t.rhs.__class__.__name__
        if cn == "expression_new_instance":
            if not hasattr(t.rhs, "temp_label"):
                t.rhs.temp_label = t.temp_label        

    def preVisit_statement_return(self, t):
        # generate lable for temp variable
        t.temp_label = self.label_generator._generate()

    def preVisit_method(self, t):
        self._generate_and_set_label_if_none(t, t)
        self._current_scope.lookup_this_scope(t.name).label = t.label
        self._current_scope = t.symbol_table

    def postVisit_method(self, t):
        self.postVisit_function(t)

    def postVisit_expression_identifier(self, t):
        if not hasattr(t, "label"):
            val = self._current_scope.lookup(t.identifier)
            if not hasattr(val, "label"):
                t.label = self.label_generator._generate()
                self._current_scope.lookup_this_scope(t.identifier).label = t.label
            else:
                t.label = val.label        

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

    def preVisit_instance_expression_list(self, t):
         # generate temp label
        if not hasattr(t, "temp_label"):
            t.temp_label = LabelGenerator._generate()

# auxiliaries
    def midVisit_class_descriptor(self, t):
        self._extend_class(t)

    def _extension_instance(self, t):        
        current = self._current_scope.lookup(t.struct)
        while len(current.info[2]) > 0:
            # generate instance label
            if not hasattr(t, "inst_label"):
                t.inst_label = LabelGenerator._generate()
            # generate temp label
            if not hasattr(t, "temp_label"):
                t.temp_label = LabelGenerator._generate()
            # generate extension label
            if len(current.info[2]) < 2:
                current.info[2].append(LabelGenerator._generate())

            current = self._current_scope.lookup(current.info[2][0])

    def _extend_class(self, t):
        # currently there can only be one extension so it is fine to 
        # put the label for the extension on the tree but if there 
        # can be multiple extensions (multi-inheritannce) the lables
        # should be saved along with the extension name
        cd = self._current_scope.lookup(t.name)
        if not len(cd.info[2]) < 1:
            self._generate_and_set_label_if_none(t, t)
            cd.info[2].append(t.label)

        #if len(cd.info[3]) > 0: # len > 0 => there are additons to generate code for
        #    for member in cd.info[3]: # where the additions are located
        #        if len(member) >= 3: # method
        #            self._process_ext_meth_params(member[2].par_list)
    
    #def _process_ext_meth_params(self, params):
    #    # omit the this reference from the preivous class
    #    params = params.next
    #    while params:
    #        self._generate_and_set_label_if_none(params, params)
    #        params = params.next

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