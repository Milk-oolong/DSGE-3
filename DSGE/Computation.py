import numpy as np
import hashlib


class Computable:

    def __init__(self,name):
        self.name = name
        self._value = np.nan

    def __call__(self):
        pass

    def __str__(self):
        return '{} = {}'.format(self.name,self.value)

    def __hash__(self):
        a = hashlib.md5(self.name.encode())
        b = a.hexdigest()
        return int(b, 16)

    def __eq__(self,other):
        return self.name == other.name

    @property
    def value(self):
        return self._value
        

class Variable(Computable):

    def __init__(self,name,fun_tree,deps):
        Computable.__init__(self,name)
        self.fun_tree = fun_tree
        self.deps = deps

    def __call__(self):
        for dep in self.deps:
            dep()
        kwargs = {dep.name: dep.value for dep in self.deps}
        self._value = evaluate_function_tree(self.fun_tree,kwargs)
        return self.value


class Parameter(Computable):

    def __init__(self,name,val=np.nan):
        Computable.__init__(self,name)
        self.value = val

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,v):
        self._value = v


def evaluate_function_tree(f_tree,kwargs):
    if f_tree[0] is None:
        if type(f_tree[1]) is str:
            return kwargs[f_tree[1]]
        else:
            return f_tree[1]
    else:
        
        args = [evaluate_function_tree(elt,kwargs) for elt in f_tree[1:]]
        return f_tree[0](*args)

    
def make_variable(variables,var_name,deps,fun_tree,final_list):
    dep_list = set()
    for d in deps:
        if d in final_list.keys():
            dep_list.add(final_list[d])
        else:
            new_name = d
            new_deps = variables[d]['dependencies']
            new_fun = variables[d]['function']
            new_var = make_variable(variables, new_name, new_deps, new_fun, final_list)
            final_list[d] = new_var
            dep_list.add(new_var)
    return Variable(var_name,fun_tree,dep_list)


    
def make_equations(variables,eoc_variables,parameters):
    params = {}
    eoc_vars = {}
    all_vars = {}
    for p in parameters:
        param_object = Parameter(p,np.nan)
        params[p] = param_object
        all_vars[p] = param_object
    for var_name, data in eoc_variables.items():
        deps = data['dependencies']
        fun = data['function']
        tmp_var = make_variable(variables,var_name,deps,fun,all_vars)
        all_vars[var_name] = tmp_var
        eoc_vars[var_name] = tmp_var
    return (params,eoc_vars,all_vars)
        
    
