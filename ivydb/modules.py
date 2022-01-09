import subprocess
import sys

import ivy.ivy_init # type: ignore
import ivy.ivy_utils # type: ignore

def setup_lldb():
    ret = subprocess.check_output(['lldb', '-P'])
    ret = ret.strip().decode("utf-8")
    print(ret)
    sys.path.append(ret)

def setup_ivy():
    sys.path.append("/Users/ntaylor/code/ivy")
    ivy.ivy_init.read_params()
    ivy.ivy_utils.set_parameters({
        'coi':'false',
        "create_imports":'true',
        "enforce_axioms":'true',
        'ui':'none',
        'isolate_mode':'test',
        'assume_invariants':'false'})

def setup_z3():
    #TODO: if DYLD_LIBRARY_PATH is set by the user, do we need this?
    import builtins
    builtins.Z3_LIB_DIRS = [ '/Users/ntaylor/code/ivy/lib' ]

setup_lldb()
setup_ivy()
#setup_z3()

