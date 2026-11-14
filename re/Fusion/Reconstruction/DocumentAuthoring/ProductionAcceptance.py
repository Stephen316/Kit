import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.dont_write_bytecode = True


def main():
    from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
    from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', choices=('parameter', 'circle', 'extrusion', 'rectangle', 'cuboid'), default='extrusion')
    parser.add_argument('--length', type=float, default=17.25)
    parser.add_argument('--radius', type=float, default=12.5)
    parser.add_argument('--width', type=float, default=17.0)
    parser.add_argument('--depth', type=float, default=23.0)
    arguments = parser.parse_args()
    names = dict(SketchName='Authored Rectangle', ExtrusionName='Authored Cuboid Extrusion', BodyName='Authored Cuboid') if arguments.profile in ('rectangle', 'cuboid') else {}
    specification = DocumentSpec('Kit Production Author', 'authoredLength', arguments.length, arguments.profile, arguments.radius, 'Production native codec acceptance', WidthMm=arguments.width, DepthMm=arguments.depth, **names)
    data = EmitDocument(specification)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(data)
    report = {'schema': 'FusionProductionDocumentGeneration/1', 'profile': arguments.profile, 'sourceArchive': None, 'runtimeTemplate': None, 'nativeAcceptance': 'pending', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'lengthMillimeters': arguments.length, 'radiusMillimeters': arguments.radius, 'widthMillimeters': arguments.width, 'depthMillimeters': arguments.depth}
    arguments.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
