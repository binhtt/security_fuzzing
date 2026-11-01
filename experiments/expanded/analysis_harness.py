"""Load only recorded pure functions for analysis; never import an LLM runtime."""
import ast,collections,json,random,types
from pathlib import Path
from cases import CASES,POLICY_TEXT
source=Path(__file__).resolve().parents[2]/'src/harness/study.py'
tree=ast.parse(source.read_text())
functions={'mutate','prompts','select_parent'};constants={'OPS','METHODS'}
nodes=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in functions:nodes.append(node)
    elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):nodes.append(node)
namespace={'collections':collections,'json':json,'random':random,'CASES':CASES,'POLICY_TEXT':POLICY_TEXT}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
assert functions|constants <= namespace.keys()
harness=types.SimpleNamespace(**{k:namespace[k] for k in functions|constants|{'CASES','POLICY_TEXT'}})
