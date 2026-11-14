import hashlib,json,lzma,runpy
from pathlib import Path

BASE=Path(__file__).resolve().parent
SOURCE=BASE.parents[1]/'LocalOracle/TSpline'
TOOLS=runpy.run_path(str(BASE/'InspectControls.py'))


def coordinate(value):return tuple(round(v,12) for v in value)
def edge_key(first,second):return tuple(sorted((coordinate(first),coordinate(second))))


def main():
 capture=json.loads((SOURCE/'CreaseCapture.json').read_text());rows=[];models={}
 for case in capture['cases']:
  for stage,observed in case['stages'].items():
   path=SOURCE/observed['file'];model=TOOLS['parse'](path);facts=TOOLS['check'](model);models[path.name]=model
   points=facts['primaryControlPoints'];native_points=sorted(coordinate(v) for v in observed['vertices'])
   if sorted(coordinate(v) for v in points.values())!=native_points:raise ValueError('Native point correspondence differs')
   crease_keys=[]
   for index in model['creasedEdges']:
    root=model['halfedges'][model['edges'][index]['root']];opposite=model['halfedges'][root['mate']]
    crease_keys.append(edge_key(points[root['vertex']],points[opposite['vertex']]))
   native_keys=[edge_key(edge['start'],edge['end']) for edge in observed['edges'] if edge['creased']]
   if sorted(native_keys)!=sorted(crease_keys):raise ValueError('Native creased edges differ')
   rows.append(dict(file=path.name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),kind=case['kind'],stage=stage,native_edge_count=len(observed['edges']),native_creased_count=len(native_keys),serialized_creased_edges=model['creasedEdges'],serialized_creased_vertices=model['creasedVertices'],smart_grips=model['smartGrips'],grips=len(model['grips']),compound_layouts=len(model['compoundGrips']),native_crease_endpoint_sets_equal=True,native_control_points_equal=True,end_condition_edges=[v['edge'] for v in model['endConditions']]))
 encoded=lzma.compress(json.dumps(models,indent=2).encode());(BASE/'CreaseModels.json.xz').write_bytes(encoded)
 report={'scope':'Independent raw text decoding matched to native edge geometry and crease state; API edge enumeration is not serialized edge allocation','coordinate_comparison':'Components rounded to 12 decimal places in native centimeters','capture_sha256':hashlib.sha256((SOURCE/'CreaseCapture.json').read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(encoded).hexdigest(),'cases':rows}
 (BASE/'CreaseInventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(rows),'all_native_crease_sets_equal':True}))

if __name__=='__main__':main()
