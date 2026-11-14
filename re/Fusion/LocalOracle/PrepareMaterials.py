import hashlib
import io
import json
from pathlib import Path
import runpy
import uuid
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

root = Path(__file__).resolve().parent
production = '--production' in sys.argv
sys.path.insert(0, str(root.parents[2] / 'src'))
source = root / ('Features/kit_production_brep_19mm.f3d' if production else 'Features/kit_full_brep_19mm.f3d')
changed = '--changed' in sys.argv or production
output = root / ('Features/kit_production_materials_19mm.f3d' if production else 'Features/kit_changed_materials_19mm.f3d' if changed else 'Features/kit_materials_19mm.f3d')
code = root.parent / 'Reconstruction/ProteinInstances'
decoded = runpy.run_path(str(code / 'DecodeInstances.py'))['inspect'](source)
materials = [{**row['decoded']['header'], 'role': row['toc']['role'], 'definition_properties': row['definition']['fields'], 'properties': row['decoded']['fields']} for row in decoded['records']]
if changed:
    for material in materials:
        for field in material['properties']:
            if field['name'] in ('structural_Density', 'thermal_Density'):
                field['value']['value'] = 6300.0
            if field['name'] == 'metal_f0':
                field['value'] = [0.2, 0.4, 0.6, 1.0]
with ZipFile(source) as archive:
    member = next(name for name in archive.namelist() if name.endswith('.protein'))
    with ZipFile(io.BytesIO(archive.read(member))) as protein:
        candidates = {Path(name).stem: ET.fromstring(protein.read(name)) for name in protein.namelist() if '/Schemas/' in name and name.endswith('.xml')}
        schemas = {name: node for name, node in candidates.items() if node.tag == 'AssetSchema'}
    encoder = runpy.run_path(str(code / 'ProductionBridge.py'))['encode_material_data'] if production else None
    payload = runpy.run_path(str(code / 'EncodePackage.py'))['encode_package'](materials, schemas, str(uuid.uuid4()), str(uuid.uuid4()), '2026-11-12T12:00:00Z', encoder=encoder)
    with ZipFile(output, 'w') as target:
        for entry in archive.infolist():
            target.writestr(entry, payload if entry.filename == member else archive.read(entry))
report = {'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'output': output.name, 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'protein_sha256': hashlib.sha256(payload).hexdigest(), 'protein_size': len(payload), 'instances': len(materials), 'properties': sum(len(row['properties']) for row in materials), 'definition_properties': sum(len(row['definition_properties']) for row in materials), 'schemas': len(schemas), 'production_binary_codec': production, 'scope': 'Same-source semantic material reconstruction with newly allocated blocks, zero padding, regenerated XML and fresh package identities; schemas remain source declarative vocabulary; native acceptance recorded separately'}
(root / ('Features/ProductionMaterialRewrite.json' if production else 'Features/ChangedMaterialRewrite.json' if changed else 'Features/MaterialRewrite.json')).write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
