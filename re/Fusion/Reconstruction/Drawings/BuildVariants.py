import argparse
import hashlib
import json
import tempfile
import uuid
from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from compression import zstd  # noqa: E402

from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleLink import BundleLink  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.BundleText import BundleText  # noqa: E402
from convert.formats.Fusion.BundleCodec.Model.FusionBundle import FusionBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.EmitDrawBundle import EmitDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.EmitDrawing import EmitDrawing  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Manifest.ReadRoot import ReadRoot  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Package.ReadPackage import ReadPackage  # noqa: E402
from convert.formats.Fusion.DrawingCodec.ReadDrawing import ReadDrawing  # noqa: E402

OUT = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
BUNDLE_LAYOUT = EntryLayout(8, 0x0808, 0x6000, 0x5B6C, 20, 20, 0)
DWG_FOLDER = 'Documentation[Active]/Dwg.BlobParts/'


def inflate(data, size):
    value = zstd.decompress(data)
    if len(value) != size:
        raise ValueError('zstd size mismatch')
    return value


def compress(data):
    codec = zstd.ZstdCompressor(options={zstd.CompressionParameter.compression_level: 3, zstd.CompressionParameter.checksum_flag: 1, zstd.CompressionParameter.content_size_flag: 0})
    return codec.compress(data) + codec.flush()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def description(root, label):
    link = root.References[0]
    props = dict(link.Properties)
    design_version = int(props['URL'].rsplit('=', 1)[1]) if '?version=' in props['URL'] else 1
    drawing_path = str(uuid.uuid5(uuid.NAMESPACE_URL, label + ':drawing')) + '.f2d'
    design_path = str(uuid.uuid5(uuid.NAMESPACE_URL, label + ':design')) + '.f3d'
    design_name = props['toDocDisplayName']
    role = BundleText('neutronRole', link.Role)
    design = BundleObject(2, design_version, props['URL'], props['LineageUrn'], 'urn:adsk.objects:os.object:wip.dm.prod/' + design_path, design_path, design_path, design_name, design_name + '.f3d', 'f3d', (), (), None)
    token = str(uuid.uuid5(uuid.NAMESPACE_URL, label + ':lineage'))
    lineage = 'urn:adsk.wipprod:dm.lineage:' + token
    relation = BundleRefs('DERIVED', (2,), (BundleLink(2, (role, BundleText('neutronData', ''))),))
    drawing = BundleObject(1, 1, 'urn:adsk.wipprod:fs.file:vf.' + token + '?version=1', lineage, 'urn:adsk.objects:os.object:wip.dm.prod/' + drawing_path, drawing_path, drawing_path, root.DocumentName, root.DocumentName + '.f2d', 'f2d', (relation,), (), None)
    graph = BundleGraph('2026-11-12T00:00:00+0000', 'wipdm', (1,), (design, drawing))
    return BundleModel('0', root.DocumentName, '1', graph, drawing_path), drawing_path, design_path


def opaque_bundle(drawing_bytes, source, label):
    package = ReadPackage(drawing_bytes, inflate)
    root = ReadRoot(next(entry.Payload for entry in package.Entries if entry.Name == 'Manifest.dat'))
    model, drawing_path, design_path = description(root, label)
    return EmitBundle(FusionBundle(model, (BundleFile(design_path, source), BundleFile(drawing_path, drawing_bytes))))


def typed_bundle(drawing, source, label):
    model, drawing_path, design_path = description(drawing.Root, label)
    layout = tuple(PackageSlot(name, BUNDLE_LAYOUT) for name in ('Manifest.json', 'DesignDescription.json', design_path, drawing_path))
    return EmitDrawBundle(DrawingBundle(model, drawing, (BundleFile(design_path, source),), layout), compress)


def without_database(data, replacement=None):
    package = ReadPackage(data, inflate)
    entries = []
    for entry in package.Entries:
        if entry.Name.startswith(DWG_FOLDER) and entry.Name.endswith('.dwg'):
            if replacement is None:
                continue
            entry = replace(entry, Payload=replacement)
        entries.append(entry)
    if len(entries) == len(package.Entries) and replacement is None:
        raise ValueError('No embedded database to omit')
    return EmitPackage(DrawingPackage(tuple(entries)), compress)


def database(data):
    package = ReadPackage(data, inflate)
    return next(entry.Payload for entry in package.Entries if entry.Name.startswith(DWG_FOLDER) and entry.Name.endswith('.dwg'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--historical', required=True)
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--views-only', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--typed', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {'variants': []}
    historical = Path(args.historical).read_bytes()
    emitted = EmitDrawBundle(ReadDrawBundle(historical))
    plan['historical'] = {'source_sha256': digest(historical), 'emitted_sha256': digest(emitted), 'byte_exact': emitted == historical}
    dimension_bytes = Path(args.with_dimension).read_bytes()
    views_bytes = Path(args.views_only).read_bytes()
    source = Path(args.source).read_bytes()
    plan['inputs'] = {'with_dimension_sha256': digest(dimension_bytes), 'views_only_sha256': digest(views_bytes), 'source_sha256': digest(source)}
    rows = [('H0Historical', emitted)]
    rows.append(('P0Control', opaque_bundle(dimension_bytes, source, 'P0')))
    rows.append(('P2NoDwg', opaque_bundle(without_database(dimension_bytes), source, 'P2')))
    rows.append(('P3SwappedDwg', opaque_bundle(without_database(dimension_bytes, database(views_bytes)), source, 'P3')))
    rows.append(('P4ViewsControl', opaque_bundle(views_bytes, source, 'P4')))
    rows.append(('P5ReverseSwap', opaque_bundle(without_database(views_bytes, database(dimension_bytes)), source, 'P5')))
    if args.typed:
        dimension = ReadDrawing(dimension_bytes, inflate)
        again = EmitDrawing(dimension, compress)
        plan['modern'] = {'emitted_sha256': digest(again), 'byte_exact': again == dimension_bytes, 'views_only_byte_exact': EmitDrawing(ReadDrawing(views_bytes, inflate), compress) == views_bytes}
        rows.append(('M1Reemitted', typed_bundle(dimension, source, 'M1')))
        rows.append(('M2Reemitted', typed_bundle(dimension, source, 'M2')))
    for label, data in rows:
        path = OUT / (label + '.f3z')
        path.write_bytes(data)
        plan['variants'].append({'label': label, 'file': path.name, 'bytes': len(data), 'sha256': digest(data)})
    (OUT / 'Plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
