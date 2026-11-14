import ast
from pathlib import Path
root = Path('src')
seen = set()
classes = {}
def walk(module, name):
    key=(module,name)
    if key in seen: return
    seen.add(key)
    path=root.joinpath(*module.split('.')).with_suffix('.py')
    if not path.exists() or not module.startswith('convert.formats.Fusion') or '.MeshCodec.' in module or name in ('DocumentMesh', 'JournalModel', 'SphereNode', 'TorusNode'): return
    tree=ast.parse(path.read_text())
    imports={alias.asname or alias.name:(node.module,alias.name) for node in ast.walk(tree) if isinstance(node,ast.ImportFrom) and node.module for alias in node.names}
    target=next((node for node in tree.body if isinstance(node,ast.ClassDef) and node.name==name),None)
    if target:
        classes[key]=target
        nodes=[node.annotation for node in target.body if isinstance(node,ast.AnnAssign)]
        nodes+=target.bases
    else:
        nodes=[node for node in tree.body if (isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id==name) or (isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets))]
    names={item.id for node in nodes for item in ast.walk(node) if isinstance(item,ast.Name)}
    for ident in names:
        if ident in imports: walk(*imports[ident])
        elif ident!=name: walk(module,ident)
walk('convert.formats.Fusion.DocumentCodec.Model.DocumentModel','DocumentModel')
walk('convert.formats.Fusion.DocumentCodec.Model.DocumentSpec','DocumentSpec')
folder=Path('src/convert/adapters/Fusion/State/Types');folder.mkdir(parents=True,exist_ok=True)
groups={}
for module,name in sorted(classes): groups.setdefault(module.split('.')[3].replace('Codec',''),[]).append((module,name))
for group,items in groups.items():
    content=''.join(f'from {module} import {name}\n' for module,name in items)
    content+=f'\nK{group}Types: tuple[type[object], ...] = (\n'+''.join(f'    {name},\n' for module,name in items)+')\n'
    (folder/f'{group}Types.py').write_text(content)
content=''.join(f'from convert.adapters.Fusion.State.Types.{group}Types import K{group}Types\n' for group in groups)
content+='\nKStateTypes: tuple[type[object], ...] = (\n'+''.join(f'    *K{group}Types,\n' for group in groups)+')\n\nKStateNames = {f"{ClassType.__module__}.{ClassType.__name__}": ClassType for ClassType in KStateTypes}\n'
Path('src/convert/adapters/Fusion/State/StateTypes.py').write_text(content)
print(len(classes), {group:len(items) for group,items in groups.items()})
