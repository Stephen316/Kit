import hashlib
import json
import runpy
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent
repository = root.parents[2]
sys.path.insert(0, str(repository / 'src'))
sys.dont_write_bytecode = True

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview
from convert.formats.Fusion.MetaIndex import SegmentKind

author = runpy.run_path(str(root.parent / 'Reconstruction/ContainerAuthoring/PrepareExtrusion.py'))
spec = json.loads((root.parent / 'Reconstruction/DocumentAuthoring/Variants/ExtrudeSpecification.json').read_text())
design = author['AUTHOR']['prepare_feature']('extrude', spec)
model = design['model']
snapshot = str(uuid.uuid4())
act = author['AUTHOR']['CONTAINER']['act_segment'](design, snapshot)
browser = author['AUTHOR']['CONTAINER']['browser_segment'](design)
history, evidence = author['encode_history'](model['brepContract'], datetime.now(timezone.utc).isoformat())
asset_id = model['specification']['assetId']
versions = (('Application', 1), ('CAM', 4), ('ParaMesh', 8), ('SimCommon', 30005), ('SimFEACSObjects', 2), ('SimFluidDynamics', 2), ('SimStructuralAttributes', 10002))
document = DocumentHeader(str(uuid.uuid4()), str(uuid.uuid4()), (2706 << 50) | (1 << 38) | 17, versions, asset_id)
slots = tuple(SegmentSlot(index, kind, kind.value) for index, kind in enumerate((SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)))
asset = AssetHeader(asset_id, snapshot, (('Application', 139), ('ParaMesh', 13), ('Server', 36), ('VolField', 4)), 3, slots)
streams = tuple(SegmentStreams(index, result['metadata'], result['bulk']) for index, result in enumerate((design, act, browser)))
previews = tuple(ContainerPart('Previews/' + name + '.png', EmitPreview(size, size, bytes((242, 242, 242, 255)) * size * size)) for name, size in (('big', 256), ('small', 64)))
parts = (ContainerPart('Breps.BlobParts/' + model['brepContract']['partName'], history),)
encoded = EmitContainer(FusionContainer(document, asset, streams, previews, parts))
output = root / 'Authored/kit_production_container.f3d'
output.write_bytes(encoded)
report = {'scope': 'Independent complete document generated from semantic specification, research Design/ACT/Browser author plus production container/previews/BRep history; no source archive or template', 'archive': output.name, 'sha256': hashlib.sha256(encoded).hexdigest(), 'brep': evidence, 'productionContainer': True, 'sourceArchive': None, 'vendorRuntimeInWriter': False}
(output.parent / 'ProductionContainerGeneration.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'archive': str(output), 'sha256': report['sha256']}))
