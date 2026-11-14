from pathlib import Path
from hashlib import sha256
from dataclasses import asdict
import json
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'src'))
from convert import open_document, write_document
from interchange import CadDocument

output = root / 're/Fusion/LocalOracle/NativeRotationalPublic'
output.mkdir(exist_ok=True)
report = []
for role in ('circle', 'extrusion', 'frustum'):
    source = root / f're/Fusion/LocalOracle/PublicAdapter/vendor_{role}Edited.f3d'
    document = open_document(source, source_format='f3d')
    neutral = output / (role + '.json')
    neutral.write_text(document.to_json())
    target = output / (role + '.f3d')
    write_document(CadDocument.from_json(neutral.read_text()), target, destination_format='f3d', overwrite=True, allow_carrier=False)
    report.append({'role': role, 'source': str(source.relative_to(root)), 'sourceSha256': sha256(source.read_bytes()).hexdigest(),
                   'output': str(target.relative_to(root)), 'outputSha256': sha256(target.read_bytes()).hexdigest(),
                   'neutralSha256': sha256(neutral.read_bytes()).hexdigest(),
                   'parameters': [{'id': item.id, 'name': item.name, 'value': item.value.value, 'unit': item.value.unit} for item in document.parameters],
                   'bodyIds': [body.id for body in document.bodies],
                   'materials': [asdict(material) for material in document.materials],
                   'sketchEntityIds': [entity.id for sketch in document.sketches for entity in sketch.entities]})
    (output / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(role, report[-1]['outputSha256'], flush=True)
