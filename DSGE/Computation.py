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
# /!\ Solve warning in make_variable function
# Improve naming convention of lagged value
# For now, get_n_lagged is call when evaluating variable. Probably more
#     efficient if stored before. Should think about solution
# Improve _make_lag
#     e.g. self.lag = (None,0) would make sense
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
            return kwargs[f_tree[1]].value  #Return argument from kwargs
        else:
            return f_tree[1]  # Return value (this is int or float)
    elif f_tree[0] == 'LAG':
        # If tree[1] is 'LAG', then the value stored in the lagged
        # variable instance should be returned
        lagged_var = kwargs[f_tree[1][1]]
        lag = f_tree[2][1]
        return lagged_var.get_n_lagged(lag)
    else:
        # If tree is not none, then recursively apply to all arguments
        args = [evaluate_function_tree(elt,kwargs) for elt in f_tree[1:]]
        return f_tree[0](*args)

    
def make_variable(variables,
                  max_lags,
                  lagged_vars,
                  var_name,
                  deps,
                  fun_tree,
                  final_list
):
    """
    Description
    -----------
    Creates a Variable instance from parameters.
    When the specific instance relies on other Variable, they are also recursively created and added to the final_list dict
    NB: this function assumes that all parameters are already instanciated in final_list

    Arguments
    ---------
    * variables: dict with the following form: {var_name: {'dependencies':dep_list,'function':fun_tree}}
    * max_lags: dict of maximum lag: {'var_name': lag}
    * lagged_var: dict of lagged Variable instances (byref)
    * var_name: name of the Variable instance to create
    * deps: list of dependencies (str)
    * fun_tree: function tree of the Variable instance to create
    * final_list: list of all Variable and Parameter instances
    """
    dep_list = set()      # Used to store Variable and Parameter instances used to instanciate the Variable to create
    for d in deps:
        if d in final_list.keys():
            # If dep already exists, retrieve it and add it to the list
            dep_list.add(final_list[d])
        elif not d == var_name:
            # Else, create it and add it to the list
            #######################################
            #   /!\ WARNING /!\   /!\ WARNING /!\
            ######################################
            # elif not d == var_name
            # solves recursivity problems for
            # Y = LAG(Y,1)
            # But does not solve:
            # Y = LAG(X,1)
            # X = LAG(Y,1)
            #######################################
            new_name = d
            new_deps = variables[d]['dependencies']
            new_fun = variables[d]['function']
            # make new Variable instance (RECURSIVITY)
            new_var = make_variable(
                variables,
                max_lags,
                lagged_vars,
                new_name,
                new_deps,
                new_fun,
                final_list)
            # Add dependency to the final list
            final_list[d] = new_var
            # Add dependency Variable instance to dependency list
            dep_list.add(new_var)
    # Create new Variable instance
    tmp_var = Variable(var_name,fun_tree,dep_list)
    if var_name in max_lags:
        # If variables rely on lagged values from var_name, then
        # run _make_lag method with max_lag as argument
        lag = max_lags[var_name]
        tmp_var._make_lag(lag,var_name,final_list)
        lagged_vars[var_name] = tmp_var
    return tmp_var

    
def make_equations(variables,eoc_variables,parameters,max_lags):
    # Create dict storing subsets of Variable and Parameter instances
    # used in the simulation
    all_vars = {}     # Store all Variable and Parameter instances
    eoc_vars = {}     # Store only end of chain Variable instances
    params = {}       # Store only parameters
    lagged_vars = {}  # Store variables with lag
    for p in parameters:
        #First create Parameter instances
        param_object = Parameter(p,np.nan)
        params[p] = param_object
        all_vars[p] = param_object
    for v_name,lag in max_lags.items():
        # Then add initial value of lagged parameter to params
        for i in range(int(lag)):
            # Initial parameters for lagged values are named this way:
            # e.g.: LAG(B,2) => B_t_minus_2
            param_name = v_name + '_t_minus_' + str(i+1)
            param_object = Parameter(param_name,np.nan)
            params[param_name] = param_object
            all_vars[param_name] = param_object
    for var_name, data in eoc_variables.items():
        # Then create Variable instance
        # This is done recursively from end of chain Variable instances
        deps = data['dependencies']
        fun = data['function']
        tmp_var = make_variable(
            variables,
            max_lags,
            lagged_vars,
            var_name,
            deps,
            fun,
            all_vars)
        all_vars[var_name] = tmp_var
        eoc_vars[var_name] = tmp_var
    # return as tuple
    return (all_vars,eoc_vars,params,lagged_vars)
        
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
        a = hashlib.sha1(self.name.encode())
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
        self.lag = None

    def __call__(self):
        for dep in self.deps:
            dep()
        kwargs = {dep.name: dep for dep in self.deps}
        #The next line is here for var such as: Y = LAG(Y,1)
        kwargs[self.name] = self
        self._value = evaluate_function_tree(self.fun_tree,kwargs)
        return self.value

    def _make_lag(self,n_iter,v_name,variables):
        # Creates and store a Lagged_variable instance
        # Assume that variables already includes the parameters defining
        # the init values
        if self.lag is not None:
            # If either the variable is lagged,
            # or is not lagged but has a lagged value
            lag_var, c_lag = self.lag
            param_name = v_name + '_t_minus_' + str(c_lag+1)
            if lag_var is None:
                # /!\ lag_var should not be not None.
                # To check and improve
                lag_var = Lagged_variable(
                    v_name,
                    c_lag + 1,
                    variables[param_name])
        else:
            # If self.lag is None, then we are calling from the initial
            # variable. current lag = 0 and we need to create a new
            # Lagged_variable instance
            c_lag = 0
            param_name = v_name + '_t_minus_' + str(c_lag+1)
            lag_var = Lagged_variable(
                v_name,
                c_lag + 1,
                variables[param_name]
            )
        self.lag = (lag_var,c_lag)
        if not (n_iter == 1):
            # If n_iter > 1, we recursively add lag
            lag_var._make_lag(n_iter-1,lag_var.main_var_name,variables)

    def get_lagged(self):
        """
        Returns the lagged variable from the original variable
        """
        if self.lag is None:
            return None
        else:
            lag_var, c_lag = self.lag
            return lag_var

    def get_n_lagged(self,i_iter):
        """
        Returns the n-lagged variable from the original variable
        If there is less than n-lagged variables, then raise an exception
        """
        if i_iter == 1:
            return self.get_lagged().value
        else:
            lagged_var, c = self.lag
            return lagged_var.get_n_lagged(i_iter - 1)
            

class Lagged_variable(Variable):

    def __init__(self,var_name,lag,param_object):
        lag_name = 'LAG_' + str(lag) + '_' + var_name
        Variable.__init__(self,lag_name,None,None)
        self.main_var_name = var_name
        self.lag = (None,lag)
        self._init_param = param_object

    def __call__(self):
        return self.value

    def _make_lag(self,n_iter,v_name,variables):
        Variable._make_lag(self,n_iter,self.main_var_name,variables)
        lag_obj, lag = self.lag

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,v):
        self._value = v

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

