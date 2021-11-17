import subprocess
import sys

def setup_lldb():
    ret = subprocess.check_output(['lldb', '-P'])
    ret = ret.strip().decode("utf-8")
    sys.path.append(ret)

def setup_ivy():
    sys.path.append("/Users/ntaylor/code/ivy")

def setup_z3():
    import builtins
    builtins.Z3_LIB_DIRS = [ '/Users/ntaylor/code/ivydb-py/venv/lib/python3.8/site-packages/z3/lib/libz3.dylib' ]

setup_lldb()
setup_ivy()
setup_z3()

