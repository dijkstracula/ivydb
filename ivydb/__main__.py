import modules

import argparse
import logging
import os
import sys

import debugger
import ivy_shim

import ivy # type: ignore

# Tell MyPy to ignore the lldb import, since we patch in its location in the
# `modules` import and it won't know about it.
import lldb #type: ignore

from typing import List

def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="IVy introspector",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    ivyp = parser.add_argument_group("IVy project parameters")
    ivyp.add_argument("-i", "--ivy-isolate",
            help="The path to the IVy source file.",
            required=True)
    ivyp.add_argument("-v", "--verbose",
            help="Dump more info.  More 'v's ==> more info.",
            action='count', default=0)
    return parser.parse_args(args)

def init_logging(args: argparse.Namespace):
    l = logging.WARNING
    if args.verbose == 1:
        l = logging.INFO
    elif args.verbose == 2:
        l = logging.DEBUG
    elif args.verbose >= 2:
        # TODO: maybe a custom hyper-verbose level?
        l = logging.DEBUG
    logging.basicConfig(format='ivydb:%(levelname)s:%(message)s', level=l)

def main(argv: List[str]) -> int:
    args = parse_args(argv[1:])
    init_logging(args)

    with ivy.ivy_module.Module() as im:
        dname = os.path.dirname(args.ivy_isolate)
        pname = os.path.basename(args.ivy_isolate)
        ivy_shim.compile(dname, pname)

        clauses = ivy_shim.clauses_for_action(im, "server.read")
        import pdb; pdb.set_trace()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
