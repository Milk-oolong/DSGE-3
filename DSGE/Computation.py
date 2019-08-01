import numpy as np
import hashlib

########################################################################
# MODULE DESCRIPTION
#
# This module contains the main classes and functions used to store
# and define variables and parameters.
# 
# Inputs for the classes contained in this module are mainly function
# trees created by the Econ_model_parser class
#

########################################################################
# TO DO
#
#
#

########################################################################
# HELPER FUNCTION
#
# evaluation_function_tree
#     Recursively evaluate the functions in a function tree
#     This function is used to implement __call__ in Variable instances
#
# make_variable
#     Recursively creates the variables based on parameters
#
# make_equations
#     Use a dict of all variables {var_name: function_tree}, set of
#     end of chain variables {var_name} and list of parameters 
#     {param_name} to generate all instances required for computations
#

def evaluate_function_tree(f_tree,kwargs):
    # Takes a function tree and dict of arguments as input and returns
    # the value of the function
    if f_tree[0] is None:
        # If tree[0] is None, then it is either an variable argument
        # or a numeric argument
        if type(f_tree[1]) is str:
            return kwargs[f_tree[1]]   #Return argument from kwargs
        else:
            return f_tree[1]  # Return value (this is int or float)
    else:
        # If tree is not none, then recursively apply to all arguments
        args = [evaluate_function_tree(elt,kwargs) for elt in f_tree[1:]]
        return f_tree[0](*args)

    
def make_variable(variables,var_name,deps,fun_tree,final_list):
    """
    Description
    -----------
    Creates a Variable instance from parameters.
    When the specific instance relies on other Variable, they are also recursively created and added to the final_list dict
    NB: this function assumes that all parameters are already instanciated in final_list

    Arguments
    ---------
    * variables: dict with the following form: {var_name: {'dependencies':dep_list,'function':fun_tree}}
    * var_name: name of the Variable instance to create
    * fun_tree: function tree of the Variable instance to create
    * final_list: list of all Variable and Parameter instances
    """
    dep_list = set()      # Used to store Variable and Parameter instances used to instanciate the Variable to create
    for d in deps:
        if d in final_list.keys():
            # If dep already exists, retrieve it and add it to the list
            dep_list.add(final_list[d])
        else:
            # Else, create it and add it to the list
            new_name = d
            new_deps = variables[d]['dependencies']
            new_fun = variables[d]['function']
            new_var = make_variable(variables, new_name, new_deps, new_fun, final_list)
            final_list[d] = new_var
            dep_list.add(new_var)
    return Variable(var_name,fun_tree,dep_list)

    
def make_equations(variables,eoc_variables,parameters):
    # Create dict storing subsets of Variable and Parameter instances
    # used in the simulation
    all_vars = {}   # Store all Variable and Parameter instances
    eoc_vars = {}   # Store only end of chain Variable instances
    params = {}     # Sotre only parameters
    for p in parameters:
        #First create Parameter instances
        param_object = Parameter(p,np.nan)
        params[p] = param_object
        all_vars[p] = param_object
    for var_name, data in eoc_variables.items():
        # Then create Variable instance
        # This is done recursively from end of chain Variable instances
        deps = data['dependencies']
        fun = data['function']
        tmp_var = make_variable(variables,var_name,deps,fun,all_vars)
        all_vars[var_name] = tmp_var
        eoc_vars[var_name] = tmp_var
    # return as tuple
    return (all_vars,eoc_vars,params)
        
class Computable:
    """
    Base class for variables and parameters. 
    """

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
    """
    Variable are Computable for which a value is computed based on other Computable instances
    """

    def __init__(self,name,fun_tree,deps):
        """
        Variable instanciation

        Arguments
        ---------
        * name: str  Name of the variable
        * fun_tree: list   Function tree of the variable
        * deps:  iterable   List of dependencies of the variable
        """
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

