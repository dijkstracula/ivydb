# Routines around IVy-specific shims.
import modules

import ivy.ivy_ast #type: ignore
import ivy.ivy_compiler #type: ignore
import ivy.ivy_parser #type: ignore

from typing import List

def action_to_cpp_name(isolate: str, fn: str) -> str:
    fn = "__".join(fn.split("."))
    return f"{isolate}::ext__{fn}"

def compile(path: str, prog: str):
    fn = path + "/" + prog
    return ivy.ivy_compiler.import_module(fn)

def exported_actions(root: ivy.ivy_parser.Ivy) -> List[ivy.ivy_ast.ActionDef]:
    exp_decls = [x for x in root.decls if isinstance(x, ivy.ivy_ast.ExportDecl)]
    return [root.actions[x.args[0].args[0].rep] for x in exp_decls]
