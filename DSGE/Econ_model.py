from os.path import isfile
import json

from DSGE.Equation_parser import Econ_model_parser
from DSGE.Computation import make_equations


class Econ_model:
    """
    Generic economic model class
    """

    def __init__(self,model_name,model_path,param_path):
        self.model_name = model_name
        self.model_path = model_path
        self.param_path = param_path
        self.model_parameters = {}

    def __call__(self,n_simulation,n_iteration):
        self._load_simulation_parameters()
        self._load_equations()
        self._assign_parameter_value()
        for i in range(n_simulation):
            print("Simulation {}".format(i))
            for j in range(n_iteration):
                print("Iteration {}".format(j))
                self._compute_variables()
                self._store_iteration_results()
                print("\n")
            self._store_simulation_results()
            

    def _load_simulation_parameters(self):
        with open(self.param_path) as f:
            self.model_parameters = json.load(f)

    def _load_equations(self):
        parser = Econ_model_parser()
        with open(self.model_path,'r') as f:
            for line in f:
                parser.run(line)

        param,eoc,all_vars = make_equations(
            parser.variables,
            parser.get_end_of_chain_variables(),
            parser.get_parameters()
            )

        self.parameter_objects = param
        self.end_of_chain_variables = eoc
        self.all_variables = all_vars

    def _assign_parameter_value(self):
        for p,v in self.model_parameters.items():
            self.all_variables[p].value = v

    def _compute_variables(self):
        for v in self.end_of_chain_variables.values():
            v()

        for v in self.all_variables.values():
            pass
            print(v)


    def _store_iteration_results(self):
        pass

    def _store_simulation_results(self):
        pass


    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self,n):
        self._model_name = n

    @property
    def param_path(self):
        return self._param_path

    @param_path.setter
    def param_path(self,p):
        self._param_path = p
        
    @property
    def model_parameters(self):
        return self._model_parameters
    
    @model_parameters.setter
    def model_parameters(self,param):
        self._model_parameters = param    

    
        
    
