from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import EmitSceneParts
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    output = ROOT / 're/Fusion/LocalOracle/NativeDocuments'
    output.mkdir(parents=True, exist_ok=True)
    cases = (
        ('OrdinaryRectangle', 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d', 'd1', 37.0),
        ('SavedCuboid', 're/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d', 'authoredLength', 43.0),
    )
    reports = []
    for name, relative, parameter, edited_height in cases:
        source = ROOT / relative
        model = ReadDocument(source.read_bytes())
        if len(model.Bodies) != 1 or not isinstance(model.Bodies[0].History, PrismHistory) or model.Graphics is None:
            raise ValueError('Expected one complete typed prism document and graphics scene')
        encoded = EmitParsed(model)
        target = output / (name + '.f3d')
        target.write_bytes(encoded)
        geometry = model.Bodies[0].History.Model
        graphic_parts = EmitSceneParts(model.Graphics)
        with ZipFile(source) as archive:
            graphics = [{
                'member': part.Name,
                'bytes': len(part.Payload),
                'sha256': digest(part.Payload),
                'source_sha256': digest(archive.read('FusionAssetName[Active]/' + part.Name)),
                'identical': part.Payload == archive.read('FusionAssetName[Active]/' + part.Name),
            } for part in graphic_parts]
        reports.append({
            'name': name,
            'source': relative,
            'source_sha256': digest(source.read_bytes()),
            'output_file': str(target.relative_to(ROOT)),
            'output_sha256': digest(encoded),
            'output_bytes': len(encoded),
            'geometry_mm': asdict(geometry),
            'height_parameter': parameter,
            'edited_height_mm': edited_height,
            'typed_counts': {
                'segments': len(model.Segments),
                'records': sum(len(segment.Records) for segment in model.Segments),
                'histories': len(model.Bodies),
                'materials': len(model.Materials),
                'snapshots': len(model.Snapshots),
                'configurations': len(model.Configurations),
                'graphics_objects': len(model.Graphics.Objects),
                'graphics_streams': len(graphic_parts) - 1,
            },
            'graphics': graphics,
            'construction': 'Complete ReadDocument -> EmitParsed; all three entity segments, BRep history and snapshot, material packages, configuration payloads and graphics are typed-decoded and independently serialized. Preview images remain explicit image parts',
            'native_acceptance': 'Pending parent-coordinated native execution',
        })
    result = {'scope': 'Qualified complete native-document reserialization', 'cases': reports, 'execution': 'Authorized native artifact generation, no local tests or native application calls'}
    (output / 'Preparation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    prepare()
