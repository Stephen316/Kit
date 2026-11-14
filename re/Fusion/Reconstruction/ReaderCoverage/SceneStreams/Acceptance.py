import io
import json
import sys
import zipfile
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import Scope
from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import EmitSceneParts
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import ReadSceneParts
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace

REENCODED = ('.protein', '.smb', '.smbh')
BUNDLES = ('re/Fusion/examples/.f3z/example1.f3z', 're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z')


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def swap(value, kind, change):
    if isinstance(value, kind):
        return change(value)
    if isinstance(value, tuple):
        return tuple(swap(entry, kind, change) for entry in value)
    if is_dataclass(value) and not isinstance(value, type):
        return replace(value, **{item.name: swap(getattr(value, item.name), kind, change) for item in fields(value) if item.init})
    return value


def count(value, kind):
    if isinstance(value, kind):
        return 1
    if isinstance(value, tuple):
        return sum(count(entry, kind) for entry in value)
    if is_dataclass(value) and not isinstance(value, type):
        return sum(count(getattr(value, item.name), kind) for item in fields(value))
    return 0


def scene(data):
    container = ReadContainer(data)
    value = ReadSceneParts(container.Parts)
    emitted = EmitSceneParts(value)
    original = {part.Name: part.Payload for part in container.Parts if part.Name.startswith('OGS.BlobFolder/')}
    return {part.Name: part.Payload for part in emitted} == original and ReadSceneParts(emitted) == value, {name.rsplit('/', 1)[1]: len(payload) for name, payload in original.items()}


def rejects(model, kind, change):
    try:
        EmitParsed(swap(model, kind, change))
    except ValueError as error:
        return str(error)
    return None


if __name__ == '__main__':
    report = {'documents': {}, 'scenes': {}, 'bundles': {}}
    documents = [name for name in Scope.FILES if name.endswith('.f3d') and 'example2' not in name] + ['re/Fusion/LocalOracle/RolledHistory/RolledHistoryReemitted.f3d']
    for name in documents:
        source = (ROOT / name).read_bytes()
        model = ReadDocument(source)
        output = EmitParsed(model)
        before, after = members(source), members(output)
        changed = sorted(entry for entry in before if before[entry] != after.get(entry) and not entry.endswith(REENCODED))
        scene_members = sorted(entry.rsplit('/', 1)[1] for entry in before if 'DefaultScene/' in entry)
        report['documents'][name] = {
            'model_equal': ReadDocument(output) == model,
            'same_names': set(before) == set(after),
            'changed': changed,
            'scene_members_equal': all(before[entry] == after[entry] for entry in before if 'DefaultScene/' in entry),
            'scene_members': scene_members,
            'edges': count(model, EnhancedEdge),
            'faces': count(model, EnhancedFace),
        }
    bundle = ReadBundle((ROOT / BUNDLES[0]).read_bytes())
    ordered = sorted((entry.FileName, entry.DataValue) for entry in bundle.Documents if entry.FileName.lower().endswith('.f3d'))
    for position, (_, data) in enumerate(ordered):
        try:
            report['scenes'][f'example1 member {position}'] = scene(data)
        except Exception as error:
            report['scenes'][f'example1 member {position}'] = f'{type(error).__name__}: {error}'
    report['scenes']['re/Fusion/examples/.f3d/example2.f3d'] = scene((ROOT / 're/Fusion/examples/.f3d/example2.f3d').read_bytes())
    for name in BUNDLES:
        value = ReadBundle((ROOT / name).read_bytes())
        report['bundles'][name] = ReadBundle(EmitBundle(value)) == value
    model = ReadDocument((ROOT / documents[0]).read_bytes())
    report['edge_rejection'] = rejects(model, EnhancedEdge, lambda value: replace(value, Normals=value.Normals[:-1]))
    report['face_rejection'] = rejects(model, EnhancedFace, lambda value: replace(value, EdgeIds=(65536,)))
    print(json.dumps(report, indent=1, default=str))
