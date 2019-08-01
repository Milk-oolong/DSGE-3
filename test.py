from os import getcwd
from os.path import join
from DSGE.Econ_model import Econ_model
from DSGE.Equation_parser import Econ_model_parser, get_dependencies
from DSGE.Computation import make_equations, evaluate_function_tree

model = Econ_model('IMF',join(getcwd(),'models','test','simple_model'),join(getcwd(),'models','test','params'))
model(1,100)

print(model.results['Y'][0])
#print(model.results)

from DSGE.Computation import Variable, Lagged_variable



