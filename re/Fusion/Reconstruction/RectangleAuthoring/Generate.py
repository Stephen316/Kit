import argparse
import hashlib
import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
sys.dont_write_bytecode = True


def main():
    from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
    from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

    parser = argparse.ArgumentParser()
    parser.add_argument('--width', type=float, default=17.0)
    parser.add_argument('--depth', type=float, default=23.0)
    parser.add_argument('--height', type=float, default=31.0)
    parser.add_argument('--profile', choices=('rectangle', 'cuboid', 'both'), default='both')
    parser.add_argument('--output', type=Path, default=ROOT / 're/Fusion/LocalOracle/RectangleAuthoring')
    arguments = parser.parse_args()
    profiles = ('rectangle', 'cuboid') if arguments.profile == 'both' else (arguments.profile,)
    arguments.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for profile in profiles:
        specification = DocumentSpec(
            'Kit independent rectangle authoring',
            'authoredLength',
            arguments.height,
            ProfileKind=profile,
            WidthMm=arguments.width,
            DepthMm=arguments.depth,
            SketchName='Authored Rectangle',
            ExtrusionName='Authored Cuboid Extrusion',
            BodyName='Authored Cuboid',
            ParamComment='Independent rectangle and cuboid acceptance',
        )
        payload = EmitDocument(specification)
        name = 'ProductionRectangle' if profile == 'rectangle' else 'ProductionCuboid'
        target = arguments.output / (name + '.f3d')
        target.write_bytes(payload)
        report = {
            'schema': 'FusionIndependentRectangleGeneration/1',
            'profile': profile,
            'output': str(target),
            'sourceArchive': None,
            'runtimeTemplate': None,
            'inputsMm': {'width': arguments.width, 'depth': arguments.depth, 'height': arguments.height},
            'drivingParameter': 'authoredLength',
            'sketchDimensions': [],
            'sketchConstraints': [],
            'sketchName': specification.SketchName,
            'extrusionName': specification.ExtrusionName,
            'bodyName': specification.BodyName,
            'bytes': len(payload),
            'sha256': hashlib.sha256(payload).hexdigest(),
            'nativeAcceptance': 'pending',
        }
        target.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
        reports.append(report)
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()
