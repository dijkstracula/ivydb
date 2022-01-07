import modules

import argparse
import os
import sys

import debugger
import ivy_shim

import ivy # typing: ignore

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

    with ivy.ivy_module.Module() as im:
        ag = ivy_shim.compile(args.ivy_project_dir, args.program)
        clauses = ivy_shim.clauses_for_action(im, "server.read")
        import pdb; pdb.set_trace()
        # Set breakpoints on all the exported actions
        for action in ivy_shim.exported_actions(ag):
            name = ivy_shim.action_to_cpp_name(args.program, action.args[0].rep)
            fns = target.FindGlobalFunctions(name, 1, lldb.eMatchTypeRegex)
            if len(fns) != 1:
                print(f"Non-unique result for {name}: {list(fns)}")
                continue

            cpp_name = fns[0].symbol.name
            entry_pc = fns[0].symbol.GetStartAddress().file_addr
            #print(f"{action.args[0]} is {cpp_name} at {hex(entry_pc)}")
            target.BreakpointCreateByAddress(entry_pc)

            # Show pre/posts for all actions
            for action in ivy_shim.actions(p):
                seq = action.args[1]
                update = seq.update(im, None)
                print(f"{action.args[0]}: {update}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
