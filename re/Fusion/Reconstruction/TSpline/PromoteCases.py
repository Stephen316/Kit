import hashlib,json,lzma,runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'re/Fusion/LocalOracle/TSpline'
EXTRA=ROOT/'re/Fusion/LocalOracle/FormDocuments/General/CapAccept'
OUT=Path(__file__).resolve().parent
PARSE=runpy.run_path(str(OUT/'InspectControls.py'))['parse']


def point(values):return dict(zip(('CoordX','CoordY','CoordZ','Weight'),values))
def pairs(values):return [dict(SourceIndex=a,TargetIndex=b) for a,b in values]
def symmetry_map(model,role):return dict(Forward=pairs(model['symmetryMaps'][role]),Reverse=pairs(model['symmetryMaps'][role+'r']))


def typed(model,path):
 d=model['declarations']
 header=dict(Degree=int(d['degree'][0]),CapType=d['cap-type'][0],StarSmoothness=float(d['star-smoothness'][0]),UnitScale=float(d['units'][0]),UnitName=d['units'][1],EndConditions=d['end-conditions'][0],StarKnotRule=d['star-knot-rule'][0],Tolerance=float(d['tol'][0]),GeometryTol=float(d['geom-tol'][0]),VersionCount=int(d['ver'][0]),BehaviorVersion=d['behavior-version'][0],CompatVersion=d['compat-version'][0])
 topology=dict(Faces=[dict(OriginLink=v['root'],IsHidden=v['isHidden']) for v in model['faces']],Edges=[dict(OriginLink=v['root'],KnotInterval=v['knotInterval']) for v in model['edges']],Vertices=[dict(OriginLink=v['root'],Direction=v['direction']) for v in model['vertices']],Links=[dict(Previous=v['previous'],NextLink=v['next'],Opposite=v['mate'],VertexIndex=v['vertex'],FaceIndex=v['face'],EdgeIndex=v['edge'],ValenceOffset=v['valenceOffset']) for v in model['halfedges']],EndConditions=[dict(EdgeIndex=v['edge'],EndValue=v['value']) for v in model['endConditions']])
 mapping=dict(Owners=[dict(VertexIndex=v['vertex'],IsPrimary=v['primary']) for v in model['gripMap']],Compounds=[dict(VertexIndex=v['vertex'],SpokeLengths=v['spokeLengths'],GripIndices=v['gripIndices']) for v in model['compoundGrips']]) if model.get('oddGripMap') else None
 creases=dict(EdgeIndices=model['creasedEdges'],VertexIndices=model['creasedVertices']) if any(v.startswith('100edges') for v in path.read_text().splitlines()) else None
 symmetry=None
 if model.get('symmetryFrame'):
  frame=model['symmetryFrame'];symmetry=dict(Origin=point(frame['origin']),FirstAxis=point(frame['firstAxis']),SecondAxis=point(frame['secondAxis']),FaceMap=symmetry_map(model,'f'),EdgeMap=symmetry_map(model,'e'),VertexMap=symmetry_map(model,'v'))
 return dict(Header=header,Topology=topology,Grips=[point([*v['position'],v['weight']]) for v in model['grips']],Mapping=mapping,Creases=creases,Symmetry=symmetry,SmartGrips=model['smartGrips'])


def main():
 cases=[]
 for path in sorted(SOURCE.glob('*.tsm')) + sorted(EXTRA.glob('*.tsm')):
  model=PARSE(path);value=typed(model,path)
  semantic=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
  cases.append(dict(Name=path.stem,Source=str(path.relative_to(ROOT)),SourceHash=hashlib.sha256(path.read_bytes()).hexdigest(),SemanticHash=hashlib.sha256(semantic).hexdigest(),Faces=len(model['faces']),Vertices=len(model['vertices']),Grips=len(model['grips'])))
 target=ROOT/'tests/convert/formats/FusionCodec/TSpline/TsmSources.xz';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(lzma.compress(json.dumps(cases,separators=(',',':')).encode()))
 print(json.dumps(dict(cases=len(cases),fixture=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))

if __name__=='__main__':main()
