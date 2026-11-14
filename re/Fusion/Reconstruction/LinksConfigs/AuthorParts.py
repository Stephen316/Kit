import hashlib
import json
import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

target = repository / 're/Fusion/LocalOracle/LinksConfigs/tmp/author'
target.mkdir(parents=True, exist_ok=True)
specs = {
    'KitAsmPartA': DocumentSpec('KitAsmPartA', 'heightA', 5.0, ProfileKind='extrusion', RadiusMm=10.0, SketchName='Part A Circle', ExtrusionName='Part A Extrusion', BodyName='Part A Body'),
    'KitAsmPartB': DocumentSpec('KitAsmPartB', 'lengthB', 12.0, ProfileKind='extrusion', RadiusMm=4.0, SketchName='Part B Circle', ExtrusionName='Part B Extrusion', BodyName='Part B Body'),
}
report = {'outputs': []}
for name, spec in specs.items():
    data = EncodeDocument(MakeFusionDoc(spec))
    model = ReadDocument(data)
    path = target / (name + '.f3d')
    path.write_bytes(data)
    report['outputs'].append({
        'name': name,
        'operation': 'EncodeDocument(MakeFusionDoc(DocumentSpec))',
        'profile': spec.ProfileKind,
        'parameter': spec.ParamName,
        'length_mm': spec.LengthMm,
        'radius_mm': spec.RadiusMm,
        'asset_id': model.Asset.AssetId,
        'output_bytes': len(data),
        'output_sha256': hashlib.sha256(data).hexdigest(),
    })
(target / 'Parts.json').write_text(json.dumps(report, indent=2) + '\n')
for entry in report['outputs']:
    print(entry['name'], entry['output_bytes'], entry['output_sha256'][:16])
