from os.path import isfile
import json


class Econ_model:
    """
    Generic economic model class
    """

    def __init__(self,model_name,param_path):
        self.model_name = model_name
        self.param_path = param_path
        self.model_parameters = {}

    def __call__(self,n_simulation,n_iteration):
        self._load_simulation_parameters()
        self._load_equations()
        for i in range(n_simulation):
            for j in range(n_iteration):
                self._generate_exogeneous_variables()
                self._compute_endogeneous_variables()
                self._store_iteration_results()
            self._store_simulation_results()

    def _load_simulation_parameters(self):
        with open(self.param_path) as f:
            self.model_parameters = json.load(f)

    def _load_equations(self):
        pass
            
    def _generate_exogeneous_variables(self):
        pass

    def _compute_endogeneous_variables(self):
        pass

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


class Equation:
    """
    """

    def __init__(self,fun,var,desc):
        """
        """
        self.fun = fun
        self.var = var
        self.desc = desc

    def __call__(self,*args,**kwargs):
        return self.fun(*args,**kwargs)

    @property
    def fun(self):
        return self._fun

    @fun.setter
    def fun(self,f):
        self._fun = f

    @property
    def var(self):
        return self._var

    @var.setter
    def var(self,v):
        self._var = v

    

    
        
    
