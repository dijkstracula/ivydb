# Routines around IVy-specific shims.
import modules
import os

import ivy.ivy_art #type: ignore
import ivy.ivy_ast #type: ignore
import ivy.ivy_check #type: ignore
import ivy.ivy_compiler #type: ignore
import ivy.ivy_isolate #type: ignore
import ivy.ivy_logic #type: ignore
import ivy.ivy_logic_utils #type: ignore
import ivy.ivy_module #type: ignore
import ivy.ivy_parser #type: ignore
import ivy.ivy_transrel #type: ignore

from typing import List

def action_to_cpp_name(isolate: str, fn: str) -> str:
    fn = "__".join(fn.split("."))
    return f"{isolate}::ext__{fn}"

def compile(path: str, prog: str) -> ivy.ivy_art.AnalysisGraph:
    os.chdir(path)
    fn = path + "/" + prog + ".ivy"
    with open(fn) as f:
        ivy.ivy_compiler.ivy_load_file(f, create_isolate=False)
        ivy.ivy_module.module.name = fn[:fn.rindex('.')]

    ivy.ivy_isolate.compile_with_invariants.set("true")
    ivy.ivy_isolate.create_isolate('this')

    ag = ivy.ivy_compiler.ivy_new()
    return ag

def resolve_action(m: ivy.ivy_module.Module, action: str) -> str:
    if action in m.actions:
        return action
    if "ext:" + action in m.actions:
        return "ext:" + action
    if "imp__" + action in m.actions:
        return "imp__" + action
    raise Exception(f"No matching action found for {action}")

def clauses_for_action(m: ivy.ivy_module.Module, action: str) -> ivy.ivy_ast.Formula:
    action = resolve_action(m, action)

    upd = m.actions[action].update(m, None)
    tc = ivy.ivy_logic_utils.true_clauses()
    pre = ivy.ivy_transrel.reverse_image(tc, tc, upd)
    pre_clauses = ivy.ivy_logic_utils.trim_clauses(pre)
    # TODO: ivy_to_cpp expands field refs, expands def'ned params, etc...
    # do we need to do any of that for us?
    pre = pre_clauses.to_formula()
    import pdb; pdb.set_trace()
    return pre

def actions(root: ivy.ivy_parser.Ivy) -> List[ivy.ivy_ast.ActionDef]:
    def is_decl(x):
        return isinstance(x, ivy.ivy_ast.ExportDecl) or isinstance(x, ivy.ivy_ast.ImportDecl)

    decls = [x for x in root.decls if is_decl(x)]
    return [root.actions[x.args[0].args[0].rep] for x in decls]

def exported_actions(root: ivy.ivy_parser.Ivy) -> List[ivy.ivy_ast.ActionDef]:
    def is_decl(x):
        return isinstance(x, ivy.ivy_ast.ActionDecl)

    action_decls = [x for x in root.decls if is_decl(x)]
    action = action_decls[-2]

    try:
        action_decls[-2].args[0].rhs().update(ivy.ivy_module.module, None)
    except Exception:
        import pdb; pdb.post_mortem()

    return [root.actions[x.args[0].args[0].rep] for x in action_decls]
