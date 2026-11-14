import hashlib
import io
import json
import runpy
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 're/Fusion/LocalOracle/RectangleAuthoring/mass_probe_ProductionCuboid.f3d'
TARGET = ROOT / 'src/convert/formats/Fusion/DocumentCodec/Materials/Vocabulary/MaterialSchemas.json'
NAMES = ('CommonSchema', 'PhysMatSchema', 'PrismCommonSchema', 'PrismMetalSchema', 'StructuralCommonSchema', 'StructuralAdvancedSchema', 'StructuralMetalSchema', 'ThermalCommonSchema', 'ThermalSolidSchema')


def node(value):
    if value.text and value.text.strip() or value.tail and value.tail.strip():
        raise ValueError('Schema declaration has unexpected text')
    return {'TagName': value.tag, 'Attributes': sorted(value.attrib.items()), 'Children': [node(child) for child in value]}


def main():
    tools = runpy.run_path(str(ROOT / 're/Fusion/Reconstruction/ReflectedFeatures.py'))
    with ZipFile(SOURCE) as archive:
        member = next(name for name in archive.namelist() if name.endswith('.protein'))
    with ZipFile(io.BytesIO(tools['archive_member'](SOURCE, member))) as archive:
        candidates = {Path(name).stem: ET.fromstring(archive.read(name)) for name in archive.namelist() if '/Schemas/' in name and name.endswith('.xml')}
    declarations = {name: node(candidates[name]) for name in sorted(NAMES)}
    TARGET.write_text(json.dumps(declarations, indent=2) + '\n')
    subprocess.run(['pnpm', 'dlx', 'prettier@3.6.2', '--write', str(TARGET)], cwd=ROOT, check=True)
    report = {'scope': 'Declarative schema vocabulary only: node names, attributes including registered defaults, child declarations; no instances, definitions, source IDs or byte payloads', 'source': str(SOURCE.relative_to(ROOT)), 'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'target': str(TARGET.relative_to(ROOT)), 'schemaNames': sorted(NAMES), 'targetSha256': hashlib.sha256(TARGET.read_bytes()).hexdigest()}
    Path(__file__).with_name('SchemaProvenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
