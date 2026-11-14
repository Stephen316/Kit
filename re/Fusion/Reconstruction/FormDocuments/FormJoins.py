import glob
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode

VOCAB = json.loads((ROOT / 'src/convert/formats/Fusion/DocumentCodec/Vocabulary/FormClasses.json').read_text())
NAMES = {row['NameValue']: row['ClassGuid'].upper() for row in VOCAB}


def fields(record):
    out = {}
    for group in record.Groups:
        for field in group.Fields:
            out[field.FieldName] = field.Value
    return out


def leading(record):
    return record.Groups[0].ClassGuid.upper() if record.Groups else ''


def programs(entities):
    return [surface.Subtrans for surface in ListTsplines(entities) if isinstance(surface.Subtrans, SubtransNode)]


def analyse(path):
    model = ReadDocument(Path(path).read_bytes())
    design = next(segment for segment in model.Segments if segment.Metadata.Header.SegmentId == 0)
    primary = {record.ObjectId: record for record in design.Records if record.IsPrimary}
    by_class = {}
    for record in primary.values():
        by_class.setdefault(leading(record), []).append(record)
    row = {'file': str(Path(path).relative_to(ROOT)), 'forms': len(model.Forms)}
    surfaces = {form.Name.removeprefix('TSplines.BlobParts/'): form.Surface for form in model.Forms}
    meshes = by_class.get(NAMES['ControlFrameMesh'], [])
    row['serializers'] = [fields(record)['partName'] for record in by_class.get(NAMES['TSplineSerializer'], [])]
    counts = []
    for mesh in meshes:
        data = fields(mesh)
        surface_record = primary[data['rSurface'].ObjectId]
        serializer = primary[fields(surface_record)['rSerializer'].ObjectId]
        tsm = surfaces[fields(serializer)['partName']]
        entry = {}
        for key, total in (('facets', len(tsm.Topology.Faces)), ('edges', len(tsm.Topology.Edges)), ('vertices', len(tsm.Topology.Vertices)), ('grips', len(tsm.Grips))):
            refs = data[key].Items
            ids = sorted(fields(primary[ref.ObjectId])['tsID'] for ref in refs)
            entry[key] = {'frame': len(refs), 'tsm': total, 'ids_are_range': ids == list(range(len(ids))), 'max_id': max(ids) if ids else None}
        counts.append(entry)
    row['frames'] = counts
    embedded = []
    for body in model.Bodies:
        model_value = body.History
        entities = getattr(model_value, 'Entities', ())
        embedded.append(('body', [p.Surface == s for p in programs(entities) for s in surfaces.values()]))
    for snap in model.Snapshots:
        entities = getattr(snap.Snapshot, 'Entities', ())
        embedded.append(('snap', [p.Surface == s for p in programs(entities) for s in surfaces.values()]))
    row['embedded'] = embedded
    nodes = by_class.get(NAMES['SubDSurfaceNode'], [])
    row['nodes'] = [{k: repr(fields(n).get(k))[:60] for k in ('rSurface', 'rDcTSplineFeature', 'userName')} for n in nodes]
    return row


if __name__ == '__main__':
    for path in sorted(glob.glob(str(ROOT / 're/Fusion/LocalOracle/TSplineCodec/*.f3d'))):
        try:
            print(json.dumps(analyse(path)))
        except Exception as error:
            print(Path(path).name, 'ERROR', type(error).__name__, error)
