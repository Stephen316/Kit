import hashlib
import json
import lzma
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
READ=runpy.run_path(str(OUT.parent/'EntityGraph/DecodeGraph.py'))['read_graph']
SOURCES=('Study/pipemodes-87cfa7d8d82b/partial_closed.f3d','Study/pipepaths-3d11bd427946/composite_circular.f3d','Study/specialfillets-d50f7a4f04e0/rule_all_rounds.f3d')
reports=[]
for relative in SOURCES:
    path=ROOT/'re/Fusion'/relative
    graph=READ(path);schema=graph['codec'].schema
    chosen=[]
    print(relative)
    for record in graph['records']:
        names=[schema[group['identifier'].upper()]['name'] for group in record['value']['groups']]
        fields={key:value for group in record['value']['groups'] for key,value in group['fields'].items()}
        if record['primary'] and any('Parameter' in name or 'PipeFeature' in name or 'FilletFeature' in name for name in names):
            chosen.append(dict(identity=record['identity'],classes=names,fields=fields))
            print(record['identity'],names[0],{key:value for key,value in fields.items() if key in ('name','expression','value','unit','sectionSize','radius','startModelHS','endModelHS','expressionString','userName') or 'parameter' in key.lower()})
    reports.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),records=chosen))
raw=lzma.compress(json.dumps(reports,separators=(',',':')).encode());(OUT/'DesignInputs.json.xz').write_bytes(raw)
(OUT/'DesignIndex.json').write_text(json.dumps(dict(path='DesignInputs.json.xz',sha256=hashlib.sha256(raw).hexdigest(),sources=[row['path'] for row in reports]),indent=2)+'\n')
