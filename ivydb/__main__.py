import modules

import argparse
import os
import sys

import debugger
import ivy_shim

# Tell MyPy to ignore the lldb import, since we patch in its location in the
# `modules` import and it won't know about it.
import lldb #type: ignore

from typing import List

def parse_args(args: List[str]):
    parser = argparse.ArgumentParser(
        description="IVy introspector",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    ivyp = parser.add_argument_group("IVy project parameters")
    ivyp.add_argument("-i", "--ivy_project_dir",
            help="The location of the IVy source file(s).",
            required=True)
    ivyp.add_argument("-p", "--program",
            help="The name of the program.",
            required=True)
    return parser.parse_args(args)


def main(argv: List[str]) -> int:
    args = parse_args(argv[1:])

    target = debugger.attach_dbg(args.ivy_project_dir, args.program)

    p = ivy_shim.compile(args.ivy_project_dir, args.program)

    # Set breakpoints on all the exported actions
    for action in ivy_shim.exported_actions(p):
        name = ivy_shim.action_to_cpp_name(args.program, action.args[0].rep)
        fns = target.FindGlobalFunctions(name, 1, lldb.eMatchTypeRegex)
        if len(fns) != 1:
            raise Exception(f"Non-unique result for {name}: {list(fns)}")

        cpp_name = fns[0].symbol.name
        entry_pc = fns[0].symbol.GetStartAddress().file_addr
        print(f"{action.args[0]} is {cpp_name} at {hex(entry_pc)}")
        #target.BreakpointCreateByAddress(entry_pc)

    #target.BreakpointCreateByName("main")

    #XXX: probably want to do something with ivy_launch directly.
    pargs = ["1",
            "1",
            "[[0,{addr:0x7f000001,port:49124}],[1,{addr:0x7f000001,port:49125}]]",
            "[[0,{addr:0x7f000001,port:49126}],[1,{addr:0x7f000001,port:49127}]]"]

    process = target.LaunchSimple(pargs, None, args.ivy_project_dir)
    if not process:
        raise Exception("Oops")
    print(process)

    for f in process.GetThreadAtIndex(0):
        print(f)


    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
