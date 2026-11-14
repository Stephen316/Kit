import hashlib
import io
import json
import math
import sys
import zipfile
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue

oracle = repository / 're/Fusion/LocalOracle/LinksConfigs'
source = oracle / 'tmp/links'
target = oracle / 'tmp/accept'
target.mkdir(parents=True, exist_ok=True)
cos30, sin30 = math.cos(math.pi / 6), math.sin(math.pi / 6)
native_matrix = (cos30, -sin30, 0.0, 5.0, sin30, cos30, 0.0, 2.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0)
cos45 = math.cos(math.pi / 4)
moved_matrix = (cos45, -cos45, 0.0, 7.0, cos45, cos45, 0.0, -3.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 1.0)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def close(left, right):
    return len(left) == len(right) and all(abs(a - b) < 1e-9 for a, b in zip(left, right))


def move(value, counter):
    if isinstance(value, MatrixValue):
        if value.Entries is not None and close(value.Entries, native_matrix):
            counter.append(1)
            return MatrixValue(moved_matrix)
        return value
    if is_dataclass(value) and not isinstance(value, type):
        changes = {}
        for item in fields(value):
            old = getattr(value, item.name)
            new = move(old, counter)
            if new is not old:
                changes[item.name] = new
        return replace(value, **changes) if changes else value
    if isinstance(value, tuple):
        items = tuple(move(item, counter) for item in value)
        return items if any(a is not b for a, b in zip(items, value)) else value
    return value


def compare(before, after):
    left, right = members(before), members(after)
    return {
        'member_count': len(left),
        'same_member_names': set(left) == set(right),
        'changed_members': sorted(name.split('/')[-1].split('.')[-1] if '.BlobParts/' in name else name for name in left if left[name] != right.get(name)),
    }


report = {'outputs': []}
plain_source = (source / 'R5_saved.f3d').read_bytes()
plain_model = ReadDocument(plain_source)
plain_output = EmitParsed(plain_model)
(target / 'KitLinkReplayR5.f3d').write_bytes(plain_output)
report['outputs'].append({
    'name': 'KitLinkReplayR5',
    'source_control': 'R5_saved',
    'operation': 'ReadDocument then EmitParsed',
    'source_sha256': digest(plain_source),
    'output_bytes': len(plain_output),
    'output_sha256': digest(plain_output),
    'model_equal_after_reread': ReadDocument(plain_output) == plain_model,
    **compare(plain_source, plain_output),
})
moved_source = (source / 'R1_part_a.f3d').read_bytes()
moved_model = ReadDocument(moved_source)
counter = []
edited = move(moved_model, counter)
moved_output = EmitParsed(edited)
(target / 'KitLinkMovedR1.f3d').write_bytes(moved_output)
report['outputs'].append({
    'name': 'KitLinkMovedR1',
    'source_control': 'R1_part_a',
    'operation': 'ReadDocument, replace the Part A occurrence matrix in the typed model, then EmitParsed',
    'native_matrix': native_matrix,
    'written_matrix': moved_matrix,
    'replaced_matrix_fields': len(counter),
    'source_sha256': digest(moved_source),
    'output_bytes': len(moved_output),
    'output_sha256': digest(moved_output),
    'model_equal_after_reread': ReadDocument(moved_output) == edited,
    **compare(moved_source, moved_output),
})
(target / 'Prepare.json').write_text(json.dumps(report, indent=2) + '\n')
for entry in report['outputs']:
    print(entry['name'], entry['output_sha256'][:16], entry['model_equal_after_reread'], entry.get('replaced_matrix_fields'), entry['changed_members'])
