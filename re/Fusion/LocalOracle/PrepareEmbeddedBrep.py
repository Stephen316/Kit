import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[2] / 'src'))
from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

model = CylinderBody(10.0, 19.0, (0.0, 0.0, 0.0))
identity = BodyIdentity(0, 301, 4, 1794477991119457)
tags = TopologyTags(FeatureTag('3', (301,)), FeatureTag('2', (301,)), FeatureTag('1', (301,)), FeatureTag('-1', (301,)), FeatureTag('-102', (301,)), SketchLink(102, 0, 0, 1, 1))
history = HistoryState(4, 2, 4, 1, 2)
stamp = GeometryStamp('Kit', 'Production embedded BRep', '2026-11-12T00:00:00Z')
outputs = {'.smb': EmitSnapshot(model, tags, stamp), '.smbh': EmitHistory(model, identity, tags, history, stamp)}
source = root / 'Features/kit_materials_19mm.f3d'
output = root / 'Features/kit_production_brep_19mm.f3d'
with ZipFile(source) as archive:
    names = {suffix: [name for name in archive.namelist() if name.endswith(suffix)] for suffix in outputs}
    if any(len(values) != 1 for values in names.values()):
        raise RuntimeError('Expected one member for each geometry role')
    replacements = {names[suffix][0]: data for suffix, data in outputs.items()}
    with ZipFile(output, 'w') as target:
        for entry in archive.infolist():
            target.writestr(entry, replacements.get(entry.filename, archive.read(entry)))
report = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'members': [{'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in replacements.items()], 'scope': 'Production EmitSnapshot and EmitHistory author both embedded members from dimensions and explicit identity/state inputs; native acceptance separate; surrounding document remains same-source'}
(root / 'Features/ProductionBrepRewrite.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
