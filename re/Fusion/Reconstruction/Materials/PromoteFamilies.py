"""Promote the family schema declarations into the writer vocabulary.

A declaration is promoted only when it is the same in every sweep document.
Only tag names, attributes and child declarations move. No instance,
definition, identity or byte payload moves.
"""

import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
SWEEP = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Sweep'
CONTROLS = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Controls'
TARGET = ROOT / 'src/convert/formats/Fusion/DocumentCodec/Materials/Vocabulary/MaterialSchemas.json'
NAMES = (
    'CommonSchema', 'PhysMatSchema',
    'PrismCommonSchema', 'PrismMetalSchema', 'PrismOpaqueSchema', 'PrismTransparentSchema', 'PrismLayeredSchema',
    'StructuralCommonSchema', 'StructuralAdvancedSchema', 'StructuralMetalSchema', 'StructuralBasicSchema', 'StructuralGenericSchema',
    'StructuralPlasticSchema', 'StructuralWoodSchema', 'StructuralGasSchema', 'StructuralLiquidSchema',
    'ThermalCommonSchema', 'ThermalSolidSchema', 'ThermalGasSchema', 'ThermalLiquidSchema',
)


def node(value):
    if value.text and value.text.strip() or value.tail and value.tail.strip():
        raise ValueError('Schema declaration has unexpected text')
    return {'TagName': value.tag, 'Attributes': sorted(value.attrib.items()), 'Children': [node(child) for child in value]}


def declarations(path):
    with ZipFile(path) as outer:
        member = next(name for name in outer.namelist() if name.endswith('.protein'))
        with ZipFile(io.BytesIO(outer.read(member))) as inner:
            return {Path(name).stem: node(ET.fromstring(inner.read(name))) for name in inner.namelist() if 'Schemas/' in name and name.endswith('.xml') and Path(name).stem in NAMES}


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else SWEEP
    found = {}
    counts = {}
    paths = sorted(folder.glob('*.f3d'))
    for path in paths:
        for name, value in declarations(path).items():
            if name not in NAMES:
                continue
            if name in found and found[name] != value:
                raise ValueError('Declaration differs between documents: ' + name)
            found.setdefault(name, value)
            counts[name] = counts.get(name, 0) + 1
    missing = sorted(set(NAMES) - set(found))
    if missing:
        raise ValueError('Missing declarations: ' + ', '.join(missing))
    previous = json.loads(TARGET.read_text())
    for name, value in previous.items():
        if json.loads(json.dumps(found[name])) != value:
            raise ValueError('Promoted declaration changed: ' + name)
    TARGET.write_text(json.dumps({name: found[name] for name in sorted(NAMES)}, indent=2) + '\n')
    subprocess.run(['pnpm', 'dlx', 'prettier@3.6.2', '--write', str(TARGET)], cwd=ROOT, check=True, capture_output=True)
    controls = sorted(CONTROLS.glob('*.f3d'))
    report = {
        'scope': 'Declarative schema vocabulary only: node names, attributes including registered defaults, child declarations; no instances, definitions, source IDs or byte payloads',
        'rule': 'Each declaration is identical in every document of the library sweep',
        'sweep_documents': len(paths),
        'documents_per_schema': dict(sorted(counts.items())),
        'controls': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in controls},
        'target': str(TARGET.relative_to(ROOT)),
        'schemaNames': sorted(NAMES),
        'targetSha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    }
    Path(__file__).with_name('SchemaProvenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['sweep_documents'], len(report['schemaNames']), report['targetSha256'][:12])


if __name__ == '__main__':
    main()
