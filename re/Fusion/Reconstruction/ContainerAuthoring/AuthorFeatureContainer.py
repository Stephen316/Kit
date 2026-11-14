import argparse
import hashlib
import json
import lzma
import runpy
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
CONTAINER = runpy.run_path(str(BASE / 'AuthorContainer.py'))


def prepare_feature(kind, specification):
    if kind not in ('circle', 'extrude'):
        raise ValueError('Unsupported authored feature')
    specification = dict(specification, assetId=str(uuid.uuid4()))
    source = BASE.parent / 'DocumentAuthoring' / 'Variants' / ('Author' + ('Circle' if kind == 'circle' else 'Extrude') + '.py')
    author = runpy.run_path(str(source))
    return author['build_' + kind](specification)


def package_feature(design, brep_encoder=None):
    parts = {}
    contract = design['model'].get('brepContract')
    if contract is not None:
        if brep_encoder is None:
            raise ValueError('Extrusion packaging requires an independent semantic BRep history encoder')
        encoded = brep_encoder(contract)
        if not isinstance(encoded, bytes):
            raise TypeError('BRep history encoder must return bytes')
        parts['Breps.BlobParts/' + contract['partName']] = encoded
    envelope = {'assetId': design['model']['specification']['assetId']}
    return CONTAINER['build_container'](design, envelope=envelope, generated_parts=parts)


def write_result(design, result, output, kind):
    output.mkdir(parents=True, exist_ok=True)
    name = 'Authored' + ('Circle' if kind == 'circle' else 'Extrusion') + '.f3d'
    path = output / name
    path.write_bytes(result['archive'])
    models = {'Design': design['model'], 'Envelope': result['model'], 'Act': result['act']['model'], 'Browser': result['browser']['model']}
    for label, model in models.items():
        raw = (json.dumps(model, indent=2) + '\n').encode()
        (output / (label + 'Model.json.xz')).write_bytes(lzma.compress(raw, preset=9))
    report = {'schema': 'FusionAuthoredFeatureContainer/1', 'feature': kind, 'status': 'authored_native_acceptance_pending', 'candidate': str(path), 'sha256': hashlib.sha256(result['archive']).hexdigest(), 'specification': design['model']['specification'], 'sourceArchive': None, 'runtimeVendorTemplate': None, 'designEntityCount': len(design['model']['roles']), 'designRecordCount': len(design['model']['records']), 'brepContract': design['model'].get('brepContract'), 'members': [{'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in result['members'].items()]}
    (output / 'Generation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--specification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    design = prepare_feature('circle', json.loads(arguments.specification.read_text()))
    result = package_feature(design)
    report = write_result(design, result, arguments.output, 'circle')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
