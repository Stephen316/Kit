from pathlib import Path
from hashlib import sha256
from dataclasses import asdict
import json
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'src'))
from convert import open_document, write_document
from interchange import CadDocument

output = root / 're/Fusion/LocalOracle/NativePublicAdapter'
output.mkdir(exist_ok=True)
sources = (
    ('OrdinaryRectangle', root / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'),
    ('SavedCuboid', root / 're/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d'),
)
report = []
for name, source in sources:
    document = open_document(source, source_format='f3d')
    neutral = output / (name + '.json')
    neutral.write_text(document.to_json())
    target = output / (name + '.f3d')
    write_document(CadDocument.from_json(neutral.read_text()), target, destination_format='f3d', overwrite=True, allow_carrier=False)
    report.append({'name': name, 'source': str(source), 'sourceSha256': sha256(source.read_bytes()).hexdigest(),
                   'output': str(target), 'outputSha256': sha256(target.read_bytes()).hexdigest(),
                   'neutralSha256': sha256(neutral.read_bytes()).hexdigest(),
                   'parameters': [{'id': item.id, 'name': item.name, 'value': item.value.value, 'unit': item.value.unit} for item in document.parameters],
                   'bodyIds': [body.id for body in document.bodies],
                   'materials': [asdict(material) for material in document.materials],
                   'sketchEntityIds': [entity.id for sketch in document.sketches for entity in sketch.entities]})
    (output / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(name, report[-1]['outputSha256'], flush=True)
