# Routines for parsing trace files.
#
# Here's an informal grammar of a trace file:
#
# ID: [a-zA-Z0.9-]+
# VAL: NUM | ARRAY
# NUM: [0-9]+
# ARRAY: '[' (VAL ',')? VAL ']'
#
# ACTION: (ID '.')* ID
# ARGLIST: '(' (VAL ',')* VAL ')'
#
# COMMENT: '#' .* '\n'
# EXPORT_ACTION: '>' ACTION ARGLIST ('\n' VAL)? '\n'
# IMPORT_ACTION: '<' ACTION ARGLIST '\n'
#
# TRACE: (COMMENT|IMPORT_ACTION|EXPORT_ACTION)+
#
# Note that actions that return values have that value appear on the next line.

from dataclasses import dataclass
from lark import Lark, Transformer, visitors
from typing import List, Optional, TypeVar, Union

Val = Union[int, str, list]

@dataclass
class Import:
    name: List[str]
    args: List[Val]

@dataclass
class Export:
    name: List[str]
    args: List[Val]
    ret: Optional[Val]

class TraceTransformer(Transformer):
    NUM = int
    ID = str
    array = list
    arglist = list
    action_name = list

    def export_call(self, args) -> Export:
        return Export(*(args + [None]))

    def export_call_with_ret(self, args) -> Export:
        return Export(*args)

    def import_call(self, args) -> Import:
        return Import(*args)

# TODO: we need to handle record types of the form {addr:2130706433,port:49133}
# for things like tcp_test.
grammar = Lark(r"""
    _NL: /(\r?\n)+/
    COMMENT: /#[^\n]*/ _NL
    ID: /[a-zA-Z][a-zA-Z0-9_]*/
    NUM: /[0-9]+/

    ?array: "[" ((val ",")* val)? "]"
    ?val: NUM | ID | array

    ?arglist: "(" (val ",")* val ")"

    ?action_name: (ID ".")* ID
    ?export_call: "> " action_name arglist _NL val _NL -> export_call_with_ret
                | "> " action_name arglist _NL -> export_call

    ?import_call: "< " action_name arglist _NL

    ?start: (import_call | export_call)*

    %ignore COMMENT
""", parser="lalr", transformer=TraceTransformer())

Action = Union[Import, Export]

def actions_from_trace(text: str) -> List[Action]:
    tree = grammar.parse(text)

    # Since the transformer has turned all the children into either Exports or
    # imports, this is safe, but mypy can't figure that out.  So, ignore the
    # typing error here and we'll be fine - famous last words...!
    children: List[Action] = tree.children #type: ignore
    return children
