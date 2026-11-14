import hashlib
import json
import lzma
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
api = runpy.run_path(str(out.parent / 'EntityGraph/DecodeGraph.py'))
paths = ('re/Fusion/Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d', 're/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d')
reports = []
for relative in paths:
    path = root / relative
    graph = api['read_graph'](path)
    classes = graph['codec'].schema
    selected = []
    for record in graph['records']:
        groups = record['value']['groups']
        fields = {key: value for group in groups for key, value in group['fields'].items()}
        names = [classes[group['identifier'].upper()]['name'] for group in groups]
        if any('ModelHS' in key or 'modelHistory' in key.lower() for key in fields) or any('BRepHistory' in name or 'FeatureTransaction' in name or 'FeatureCollection' in name for name in names) or any('Parameter' in name or 'Body' == name for name in names):
            selected.append({'entityId':record['identity'], 'primary':record['primary'], 'classes':names, 'frame':record['value']['frame'], 'groups':groups})
    reports.append({'source':relative, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'totalRecords':len(graph['records']), 'selected':selected})
    print(relative, len(graph['records']), 'selected', len(selected))
    for entry in selected:
        values={key:value for group in entry['groups'] for key,value in group['fields'].items()}
        print(entry['entityId'], entry['classes'][0], {key:value for key,value in values.items() if 'ModelHS' in key or key in ('name','partName','modelHS','stateId','currentModelHS','nextTag')})
encoded=lzma.compress(json.dumps(reports,indent=2).encode())
(out/'DesignStates.json.xz').write_bytes(encoded)
(out/'DesignStatesSummary.json').write_text(json.dumps({'schema':'FusionJournalDesignStateJoins/1','scope':'Read-only complete research entity decoding; selected timeline and history joins; no product or native execution','evidence':'DesignStates.json.xz','sha256':hashlib.sha256(encoded).hexdigest(),'sources':[{key:value for key,value in report.items() if key!='selected'} for report in reports]},indent=2)+'\n')
