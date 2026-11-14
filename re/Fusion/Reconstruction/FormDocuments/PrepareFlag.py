import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import GeometryState
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

SOURCE = 're/Fusion/LocalOracle/TSpline/Plane.f3d'
CAGE = 're/Fusion/LocalOracle/FormDocuments/Grid/Warped.tsm'
TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Flag'
TSURFACE = '22709494-9149-4A70-A829-7D748A7B5DB1'


def flagged(model, value):
    segments = []
    hits = 0
    for segment in model.Segments:
        records = []
        for record in segment.Records:
            groups = []
            for group in record.Groups:
                if group.ClassGuid == TSURFACE:
                    fields = tuple(replace(field, Value=value) if field.FieldName == 'bConversionFailed' else field for field in group.Fields)
                    hits += sum(field.FieldName == 'bConversionFailed' for field in group.Fields)
                    group = replace(group, Fields=fields)
                groups.append(group)
            records.append(replace(record, Groups=tuple(groups)))
        segments.append(replace(segment, Records=tuple(records)))
    if hits != 1:
        raise RuntimeError('expected one conversion flag')
    return replace(model, Segments=tuple(segments))


def embedded(entities, surface):
    result = []
    for entity in entities:
        if isinstance(entity, SplineNode) and isinstance(entity.Surface, TsplineSurf) and isinstance(entity.Surface.Subtrans, SubtransNode):
            subtrans = replace(entity.Surface.Subtrans, Surface=surface)
            entity = replace(entity, Surface=replace(entity.Surface, Subtrans=subtrans))
        result.append(entity)
    return tuple(result)


def stale(model, surface):
    bodies = tuple(replace(body, History=replace(body.History, Entities=embedded(body.History.Entities, surface))) if isinstance(body.History, JournalModel) else body for body in model.Bodies)
    snaps = tuple(replace(snap, Snapshot=replace(snap.Snapshot, Entities=embedded(snap.Snapshot.Entities, surface))) if isinstance(snap.Snapshot, GeometryState) else snap for snap in model.Snapshots)
    return replace(model, Bodies=bodies, Snapshots=snaps, Forms=(replace(model.Forms[0], Surface=surface),), Graphics=None)


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    data = (ROOT / SOURCE).read_bytes()
    model = ReadDocument(data)
    cage = ReadTspline((ROOT / CAGE).read_bytes())
    variants = {
        'FlagControl': flagged(model, True),
        'StaleCage': stale(model, cage),
        'StaleCageFlag': flagged(stale(model, cage), True),
    }
    rows = []
    for name, document in variants.items():
        payload = EmitParsed(document)
        if ReadDocument(payload) != document:
            raise RuntimeError('variant does not read back')
        path = TARGET / (name + '.f3d')
        path.write_bytes(payload)
        rows.append({'variant': name, 'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(payload).hexdigest()})
    report = {
        'scope': 'TsSurface.bConversionFailed as a reconversion trigger: flagged native plane, and the Warped Kit cage stored over the stale native plane body with and without the flag',
        'python': sys.version.split()[0],
        'source': SOURCE,
        'source_sha256': hashlib.sha256(data).hexdigest(),
        'cage': CAGE,
        'cage_sha256': hashlib.sha256((ROOT / CAGE).read_bytes()).hexdigest(),
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
