# Routines concerning accessing DWARF state and whatnot.

import lldb #type: ignore
import os

def attach_dbg(path: str, prog: str):
    """Attaches an LLDB to the program at the given path."""

    full = path + "/" + prog
    
    if not os.path.exists(full):
        raise Exception(f"{full} does not exist")
    if not os.access(full, os.X_OK):
        raise Exception(f"{full} is not executable")

    debugger = lldb.SBDebugger.Create()
    debugger.SetAsync(False)
    target = debugger.CreateTarget(full)

    #XXX: Why doesn't this actually set it??  I have to still
    # export this in my calling shell (after disabling SIP)
    target.GetEnvironment().Set("DYLD_LIBRARY_PATH", "/Users/ntaylor/code/ivy/ivy/lib", True)
    print(target.GetEnvironment().Get("DYLD_LIBRARY_PATH"))

    if not target.IsValid():
        raise Exception("Couldn't create a target")
    return target

