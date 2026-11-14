import collections
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListPrograms import ListPrograms
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import WritePatches
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

ARCHIVES = sorted(set((ROOT / 're/Fusion/LocalOracle/TSpline').glob('*.f3d')) | set((ROOT / 're/Fusion/LocalOracle/TSplineCodec').glob('vendor_*.f3d')))


def surfaces(entities):
    yield from ListTsplines(entities)


def member(name, payload, program):
    entities = (ReadGeometry(payload) if name.endswith('.smb') else ReadJournal(payload)).Entities
    kinds = collections.Counter(type(entity).__name__ for entity in entities if isinstance(entity, (SplineNode, IntcurveNode, PcurveNode)))
    defined, referenced = collections.Counter(), collections.Counter()
    for entity in entities:
        for kind, index in ListSubtypes(entity):
            (defined if index is None else referenced)[kind] += 1
    texts = [len(EmitTspline(surface.Subtrans.Surface)) for surface in surfaces(entities) if isinstance(surface.Subtrans, SubtransNode)]
    patches = [len(WritePatches(surface.Subtrans.Regions)) for surface in surfaces(entities) if isinstance(surface.Subtrans, SubtransNode)]
    regions = [len(surface.Subtrans.Regions) for surface in surfaces(entities) if isinstance(surface.Subtrans, SubtransNode)]
    face_count = len(ReadTspline(program).Topology.Faces)
    return {
        'member': name.split('/')[-1].rsplit('.', 1)[-1],
        'entities': dict(kinds),
        'subtype_definitions': dict(defined),
        'subtype_references': dict(referenced),
        'embedded_text_bytes': sorted(set(texts)),
        'tsm_member_bytes': len(program),
        'text_tag': sorted({7 if size <= 255 else 8 for size in texts}),
        'patch_regions': sorted(set(regions)),
        'patch_text_bytes': sorted(set(patches)),
        'patch_text_tag': sorted({7 if size <= 255 else 8 for size in patches}),
        'tsm_faces': face_count,
        'embedded_equals_member': all(value == ReadTspline(program) for value in ListPrograms(entities)),
    }


def main():
    rows = []
    for path in ARCHIVES:
        data = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            programs = [name for name in names if name.endswith('.tsm')]
            if len(programs) != 1:
                continue
            program = archive.read(programs[0])
            members = [member(name, archive.read(name), program) for name in names if name.endswith(('.smb', '.smbh'))]
        rows.append({'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'members': members})
    flat = [item for row in rows for item in row['members']]
    summary = {
        'archives': len(rows),
        'members': len(flat),
        'embedded_equals_member': sum(item['embedded_equals_member'] for item in flat),
        'tag8_members': sum(8 in item['text_tag'] for item in flat),
        'tag7_members': sum(7 in item['text_tag'] for item in flat),
        'largest_tag7_text_bytes': max((size for item in flat for size in item['embedded_text_bytes'] if size <= 255), default=None),
        'smallest_tag8_text_bytes': min((size for item in flat for size in item['embedded_text_bytes'] if size > 255), default=None),
        'patch_tag7_members': sum(7 in item['patch_text_tag'] for item in flat),
        'patch_tag8_members': sum(8 in item['patch_text_tag'] for item in flat),
        'largest_tag7_patch_bytes': max((size for item in flat for size in item['patch_text_bytes'] if size <= 255), default=None),
        'smallest_tag8_patch_bytes': min((size for item in flat for size in item['patch_text_bytes'] if size > 255), default=None),
        'tsm_bytes_equal_embedded': sum(item['embedded_text_bytes'] == [item['tsm_member_bytes']] for item in flat),
        'members_with_references': sum(bool(item['subtype_references']) for item in flat),
    }
    report = {'scope': 'Production spline journal readers over local Form archives; subtype table, embedded TSM text and patch programs', 'python': sys.version.split()[0], 'summary': summary, 'rows': rows}
    (BASE / 'SplineCensus.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
