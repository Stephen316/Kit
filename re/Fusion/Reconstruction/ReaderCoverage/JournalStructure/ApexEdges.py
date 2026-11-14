import collections
import glob
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

import convert.formats.Fusion.BrepCodec.Journal.Reading.ReadBoardMut as BoardModule
import convert.formats.Fusion.Topology.AsmEdge.AsmTable as StatesModule

BoardModule.KBoardChanges = 1 << 20
StatesModule.KRecordTokens = 1 << 20
from Journals import members, raw_model
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntitiesMut import ReadEntitiesMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor


def tables(path):
    for member, payload in members(path, '.smbh').items():
        model = raw_model(payload)
        yield 'smbh', model.Entities, model.ActiveCount
    for member, payload in members(path, '.smb').items():
        cursor = MetaCursor(payload)
        ReadModelHead(cursor, False)
        entities = ReadEntitiesMut(cursor, 'End-of-ASM-data')
        yield 'smb', entities, len(entities)


def apex_gap(cone, point):
    axis = cone.AxisVector
    radius = math.dist(cone.MajorAxisCm, (0.0, 0.0, 0.0))
    if cone.SineAngle == 0:
        return None
    reach = radius * cone.CosineAngle / cone.SineAngle
    apex = tuple(o - a * reach for o, a in zip(cone.OriginCm, axis))
    return math.dist(apex, point)


# every edge whose curve is null: its vertices, params, single coedge and the surface of the face it bounds
def main():
    shapes = collections.Counter()
    gaps = []
    examples = {}
    unread = 0
    for path in sorted(glob.glob(str(ROOT / 're/**/*.f3d'), recursive=True)):
        try:
            found = list(tables(path))
        except Exception:
            unread += 1
            continue
        for kind, entities, active in found:
            for slot, edge in enumerate(entities):
                if not isinstance(edge, EdgeNode) or edge.CurveRef != -1:
                    continue
                coedge = entities[edge.OwnerCoedge]
                loop = entities[coedge.OwnerLoop] if isinstance(coedge, CoedgeNode) else None
                face = None
                if isinstance(loop, LoopNode):
                    face = entities[loop.OwnerFace]
                surface = entities[face.Surface] if isinstance(face, FaceNode) else None
                vertex = entities[edge.StartVertex]
                point = entities[vertex.PointRef] if isinstance(vertex, VertexNode) else None
                gap = apex_gap(surface, point.PositionCm) if isinstance(surface, ConeNode) and isinstance(point, PointNode) else None
                if gap is not None and slot < active:
                    gaps.append(gap)
                key = json.dumps({
                    'kind': kind,
                    'live': slot < active,
                    'same_vertex': edge.StartVertex == edge.EndVertex,
                    'params': [edge.StartParam, edge.EndParam],
                    'reversed': edge.Reversed,
                    'convexity': edge.Convexity,
                    'coedge_partner': None if not isinstance(coedge, CoedgeNode) else ('none' if coedge.Partner == -1 else 'some'),
                    'coedge_ring_is_self': isinstance(coedge, CoedgeNode) and coedge.NextCoedge == edge.OwnerCoedge and coedge.PriorCoedge == edge.OwnerCoedge,
                    'coedge_pcurve': None if not isinstance(coedge, CoedgeNode) else coedge.Pcurve != -1,
                    'surface': type(surface).__name__,
                    'vertex_edge_is_self': isinstance(vertex, VertexNode) and vertex.OwnerEdge == slot,
                    'vertex_at_apex': (gap is not None and gap < 1e-9) if slot < active else None,
                }, sort_keys=True)
                shapes[key] += 1
                examples.setdefault(key, f'{Path(path).relative_to(ROOT)} {kind} slot {slot}')
    report = {
        'scope': 'Every edge record with a null curve in every .smbh (live and archived) and .smb under re/',
        'unread_files': unread,
        'archived_note': 'Archived journal records hold slot ids, so their surface and vertex lookups are not resolved and vertex_at_apex is null',
        'max_apex_gap_cm': max(gaps, default=None),
        'shapes': [{'count': count, 'example': examples[key], **json.loads(key)} for key, count in shapes.most_common()],
    }
    Path(__file__).with_name('ApexEdges.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
