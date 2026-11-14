"""Research: read the converted Form body that Fusion saved next to its cage.

The reader follows tests/.../Form/ReadConverted.py (copied, not imported) and
adds the raw Fusion-side facts the shape rule is compared with: entity order of
points and curves, pcurve traces, fit tolerances and progenitor windows.
"""

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import PcurveSpline, SplineCurve  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import NegateCurve  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import SubtypeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import EntitySubtree  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import WalkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import ExactIntCur, ExpParCur  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import FormBody, FormEdge, FormFace, FormSurface, FormUse, FormWindow  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import GroupFields  # noqa: E402
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap  # noqa: E402
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject  # noqa: E402
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair  # noqa: E402
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries  # noqa: E402
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef  # noqa: E402

FEATURE_GUID = '6C90740C-229E-4EE5-8F35-A4E5AE4F7C73'
WINDOW_NAMES = ('uLow', 'uHigh', 'vLow', 'vHigh')

OLD_SAVES = {
    'Box': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleBoxFresh.f3d',
    'CreasedPlane': 're/Fusion/LocalOracle/FormDocuments/Acceptance/Saved/PlaneCreasedControl.f3d',
    'CreasedBox': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleCreasedBoxFresh.f3d',
    'Box3': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleBox3Fresh.f3d',
    'Valence5': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleValence5Fresh.f3d',
    'Valence6': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleValence6Fresh.f3d',
    'Valence7': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Carriers/Valence7.f3d',
    'Valence8': 're/Fusion/LocalOracle/FormDocuments/StencilAccept/Saved/OracleValence8Fresh.f3d',
}
GENERAL = ('Box111', 'Box122', 'Box234', 'LPrism', 'TPrism', 'Step', 'Valence5Tall', 'Valence3Prism', 'Mixed56', 'Mixed78', 'Torus86', 'SharpBox')
GENERAL_DIR = ROOT / 're/Fusion/LocalOracle/FormDocuments/General'


@dataclass
class Saved:
    body: FormBody
    surface: object
    point_order: list = field(default_factory=list)  # entity index of each body vertex point
    curve_order: list = field(default_factory=list)  # entity index of each body edge curve
    curves: dict = field(default_factory=dict)  # entity index -> BsCurve
    label_types: dict = field(default_factory=dict)  # label -> entityType
    face_windows: dict = field(default_factory=dict)  # label -> windows


def active(model):
    for body in model.Bodies:
        history = body.History
        if isinstance(history, JournalModel):
            return history.Entities[: history.ActiveCount]
    raise RuntimeError('no journal')


def subtype_table(entities):
    return tuple(found for entity in entities for found in WalkSubtypes(EntitySubtree(entity)) if not isinstance(found, SubtypeRef))


def resolve(value, table):
    while isinstance(value, SubtypeRef):
        value = table[value.Index]
    return value


def entity_label(entities, attribute):
    labels = []
    while attribute >= 0:
        entry = entities[attribute]
        if isinstance(entry, TagAttrib):
            labels += [tag.PrimaryId for tag in entry.Groups]
        links = getattr(entry, 'Links', None)
        assert isinstance(links, AttribLinks)
        attribute = links.NextAttrib
    assert len(labels) <= 1
    return labels[0] if labels else ''


def object_window(item):
    fields = GroupFields(item.Groups)
    return FormWindow(fields['faceIndex'], *(fields[name] for name in WINDOW_NAMES))


def tag_windows(model):
    owners = {record.ObjectId: record for record in model.Segments[0].Records if record.IsPrimary and record.Groups}
    features = [record for record in owners.values() if record.Groups[0].ClassGuid.upper() == FEATURE_GUID]
    assert len(features) == 1
    info = GroupFields(features[0].Groups)['subDInfoMap']
    assert isinstance(info, ValueMap) and len(info.Entries) == 1
    pairing = info.Entries[0].Second
    vector = GroupFields(owners[pairing.Second.ObjectId].Groups)['ProgenitorTagVec']
    found = {}
    for entry in vector.Items:
        fields = GroupFields(owners[entry.First.ObjectId].Groups)
        items = fields['tsEntityProgenitors']
        found[str(entry.Second)] = (fields['entityType'], tuple(object_window(item) for item in items.Items))
    return found


def face_chain(entities):
    bodies = [entity for entity in entities if isinstance(entity, BodyNode)]
    lump = entities[bodies[0].FirstLump]
    shell = entities[lump.FirstShell]
    chain, current = [], shell.FirstFace
    while current >= 0:
        chain.append(current)
        current = entities[current].NextFace
    return chain


def loop_uses(entities, face_index):
    face = entities[face_index]
    loop = entities[face.FirstLoop]
    assert loop.NextLoop == -1
    chain = [loop.FirstCoedge]
    while True:
        coedge = entities[chain[-1]]
        if coedge.NextCoedge == loop.FirstCoedge:
            return chain
        chain.append(coedge.NextCoedge)


def read_saved(path):
    model = ReadDocument(Path(path).read_bytes())
    entities = active(model)
    table = subtype_table(entities)
    windows = tag_windows(model)
    edges, edge_slots, vertex_slots, points, regions = [], {}, {}, [], []
    saved = Saved(None, model.Forms[0].Surface)
    saved.label_types = {label: value[0] for label, value in windows.items()}

    def vertex_slot(index):
        if index not in vertex_slots:
            vertex = entities[index]
            point = entities[vertex.PointRef]
            vertex_slots[index] = len(points)
            points.append(point.PositionCm)
            saved.point_order.append(vertex.PointRef)
        return vertex_slots[index]

    def edge_slot(index):
        if index in edge_slots:
            return edge_slots[index]
        edge = entities[index]
        assert not edge.Reversed
        carrier = entities[edge.CurveRef]
        assert isinstance(carrier, IntcurveNode) and not carrier.Reversed
        curve = SplineCurve(carrier.Curve)
        jumps = tuple(tuple(entry) for entry in carrier.Curve.Body.Context.Discontinuities)
        bounds = (edge.StartParam, edge.EndParam)
        label = entity_label(entities, edge.Prefix.Attribute)
        start = vertex_slot(edge.StartVertex)
        final = vertex_slot(edge.EndVertex)
        wins = windows[label][1] if label else ()
        shape = FormEdge(start, final, curve, jumps, edge.Convexity, label, wins)
        if bounds != (curve.Knots[0], curve.Knots[-1]):
            shape = replace(shape, Bounds=bounds)
        edge_slots[index] = len(edges)
        edges.append(shape)
        saved.curve_order.append(edge.CurveRef)
        saved.curves[edge.CurveRef] = curve
        return edge_slots[index]

    def read_use(index, region):
        coedge = entities[index]
        carrier = entities[coedge.Pcurve]
        assert isinstance(carrier, PcurveNode) and not carrier.Reversed
        trace = PcurveSpline(carrier.Curve)
        members = carrier.Curve.Body
        holder = members.Surface
        surface = resolve(holder.Body[1], table)
        assert isinstance(surface, TsplineSurf) and surface.FaceIndex == region
        trace = NegateCurve(trace) if coedge.Reversed else trace
        edge_index = edge_slot(coedge.EdgeRef)
        return FormUse(edge_index, coedge.Reversed, trace, members.FitTolerance)

    faces = []
    for face_index in face_chain(entities):
        face = entities[face_index]
        carrier = entities[face.Surface]
        surface = resolve(carrier.Surface, table)
        scope = resolve(surface.Subtrans, table)
        regions.append(scope.Regions)
        uses = tuple(read_use(use, surface.FaceIndex) for use in loop_uses(entities, face_index))
        label = entity_label(entities, face.Prefix.Attribute)
        if label:
            saved.face_windows[label] = windows[label][1]
        faces.append(FormFace(FormSurface(surface.Cache, surface.Jumps, surface.FaceIndex), uses, label, face.DoubleSided, face.Contained))
    assert regions and len(set(regions)) == 1
    saved.body = FormBody(tuple(points), tuple(edges), tuple(faces), regions[0])
    return saved


def old_saved(label):
    return read_saved(ROOT / OLD_SAVES[label])


def general_saved(name):
    return read_saved(GENERAL_DIR / 'tmp' / (name + '.f3d'))


def general_surface(name):
    from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline
    return ReadTspline((GENERAL_DIR / (name + '.tsm')).read_bytes())
