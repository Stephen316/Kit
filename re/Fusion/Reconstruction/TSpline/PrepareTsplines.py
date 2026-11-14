import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.MakeClosedCage import MakeClosedCage
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.CageOrientation import CageOrientation

SOURCE=ROOT/'re/Fusion/LocalOracle/TSpline'
TARGET=ROOT/'re/Fusion/LocalOracle/TSplineCodec'
TARGET.mkdir(parents=True,exist_ok=True)
cases=[]
for path in sorted(SOURCE.glob('*.tsm')):
    print("preparing",path.name,flush=True)
    payload=path.read_bytes();model=ReadTspline(payload);encoded=EmitTspline(model)
    output=TARGET/(path.stem+'Reemitted.tsm');output.write_bytes(encoded)
    cases.append({'name':path.stem,'source_file':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(payload).hexdigest(),'output_file':str(output.relative_to(ROOT)),'output_sha256':hashlib.sha256(encoded).hexdigest(),'byte_identical':encoded==payload,'faces':len(model.Topology.Faces),'edges':len(model.Topology.Edges),'vertices':len(model.Topology.Vertices),'grips':len(model.Grips),'symmetry':model.Symmetry is not None,'creased_edges':list(model.Creases.EdgeIndices) if model.Creases else []})
vertices=tuple(ControlGrip(x,y,z) for x,y,z in ((0,0,0),(0,2.3,0),(1.7,0,0),(1.7,2.3,0),(0,0,3.1),(0,2.3,3.1),(1.7,0,3.1),(1.7,2.3,3.1)))
faces=((2,0,1,3),(0,2,6,4),(0,4,5,1),(4,6,7,5),(5,7,3,1),(6,2,3,7))
orientation=CageOrientation(Spokes=(1,5,3,7,5,1,7,3),EdgeOrigins=((0,2),(0,1),(0,4),(4,6),(4,5),(1,3),(1,5),(5,7),(2,3),(2,6),(6,7),(3,7)))
independent=MakeClosedCage(vertices,faces,Orientation=orientation)
output=TARGET/'AuthoredClosedCage.tsm';encoded=EmitTspline(independent);output.write_bytes(encoded)
cases.append({'name':'AuthoredClosedCage','output_file':str(output.relative_to(ROOT)),'output_sha256':hashlib.sha256(encoded).hexdigest(),'source_free':True,'faces':6,'edges':12,'vertices':8,'grips':8,'control_points_cm':[[p.CoordX,p.CoordY,p.CoordZ] for p in vertices],'input_quad_faces':[list(v) for v in faces],'face_origins':'first loop vertex','vertex_spokes':list(orientation.Spokes),'edge_origins':[list(v) for v in orientation.EdgeOrigins]})
report={'scope':'Complete TSM component regeneration and independently declared closed quad cage; explicit face-origin, vertex-orientation and edge-origin state','cases':cases}
(TARGET/'Preparation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'cases':len(cases),'byte_identical':sum(c.get('byte_identical',False) for c in cases),'preparation':str(TARGET/'Preparation.json')}))
