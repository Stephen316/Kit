from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'src'))
from convert import open_document, write_document
from convert.adapters.Fusion import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

out = root / 're/Fusion/LocalOracle/PublicAdapter'
out.mkdir(exist_ok=True)
report = []
for kind in ('parameter', 'circle', 'rectangle', 'extrusion', 'cuboid', 'frustum'):
    spec = DocumentSpec('Public ' + kind, 'publicHeight', 17.0, kind, RadiusMm=12.0,
                        SketchName='Public Profile', ExtrusionName='Public Extrusion',
                        BodyName='Public Solid', WidthMm=19.0, DepthMm=23.0,
                        Material=MaterialSpec('Public Material',2870.0,ColorValue(0.2,0.4,0.6,1.0)),
                        TaperDegrees=5.0 if kind == 'frustum' else 0.0,
                        ConstrainRectangle=kind in ('rectangle','cuboid'))
    document = MakeFusionDoc(spec)
    source = out / (kind + '.f3d')
    result = write_document(document, source, destination_format='f3d', overwrite=True, allow_carrier=False)
    (out / (kind + '.authoring.json')).write_text(document.to_json())
    projected = open_document(source, source_format='f3d')
    (out / (kind + '.native.json')).write_text(projected.to_json())
    target = out / (kind + '.reemit.f3d')
    write_document(type(projected).from_json(projected.to_json()), target, destination_format='f3d', overwrite=True, allow_carrier=False)
    report.append({'kind':kind,'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                   'reemit':str(target),'reemitSha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                   'nativeBytesEqual':source.read_bytes()==target.read_bytes(), 'solidCount':len(projected.bodies),
                   'parameters':[{'name':p.name,'value':p.value.value,'unit':p.value.unit} for p in projected.parameters]})
    (out/'Preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(kind, len(source.read_bytes()), flush=True)
