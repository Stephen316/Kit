"""Research-only reader: native converted Form BRep -> typed converted body.

Production code never reads archives. This module turns the converted body
that Fusion stored in a native control archive into the typed `FormBody`
the source-free builder accepts, so closed and creased bodies can be fed to
the builder without any archive bytes crossing into production.
"""

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import SplineCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import NegateCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import EntitySubtree
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import WalkSubtypes
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import GeometryState
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormCurve import FormCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody, FormEdge, FormFace, FormSurface, FormUse, FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import GroupFields
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

FEATURE_GUID = '6C90740C-229E-4EE5-8F35-A4E5AE4F7C73'


def subtype_table(entities):
    table = []
    for entity in entities:
        for found in WalkSubtypes(EntitySubtree(entity)):
            if not isinstance(found, SubtypeRef):
                table.append(found)
    return table


def resolve(value, table):
    while isinstance(value, SubtypeRef):
        value = table[value.Index]
    return value


def label_of(entities, attribute):
    labels = []
    while attribute >= 0:
        node = entities[attribute]
        if isinstance(node, TagAttrib):
            labels.extend(tag.PrimaryId for tag in node.Groups)
        attribute = node.Links.NextAttrib
    if len(labels) > 1:
        raise ValueError('more than one tag label on one entity')
    return labels[0] if labels else ''


def windows_by_tag(model):
    owners = {r.ObjectId: r for r in model.Segments[0].Records if r.IsPrimary}
    feature = next(r for r in owners.values() if r.Groups and r.Groups[0].ClassGuid.upper() == FEATURE_GUID)
    info = GroupFields(feature.Groups)['subDInfoMap']
    (pair,) = info.Entries
    table = owners[pair.Second.Second.ObjectId]
    result = {}
    for entry in GroupFields(table.Groups)['ProgenitorTagVec'].Items:
        prog = GroupFields(owners[entry.First.ObjectId].Groups)
        rows = []
        for item in prog['tsEntityProgenitors'].Items:
            fields = GroupFields(item.Groups)
            rows.append(FormWindow(fields['faceIndex'], fields['uLow'], fields['uHigh'], fields['vLow'], fields['vHigh']))
        result[str(entry.Second)] = (prog['entityType'], tuple(rows))
    return result


def walk_faces(entities):
    body = next(e for e in entities if isinstance(e, BodyNode))
    shell = entities[entities[body.FirstLump].FirstShell]
    faces, index = [], shell.FirstFace
    while index >= 0:
        faces.append(index)
        index = entities[index].NextFace
    return faces


def walk_loop(entities, face):
    loop = entities[entities[face].FirstLoop]
    if loop.NextLoop != -1:
        raise ValueError('multi-loop faces are outside this research reader')
    uses, index = [], loop.FirstCoedge
    while True:
        uses.append(index)
        index = entities[index].NextCoedge
        if index == loop.FirstCoedge:
            return uses


def jumps_of(curve):
    return tuple(tuple(entry) for entry in curve.Body.Context.Discontinuities)


class Reader:
    def __init__(self, entities, windows):
        self.entities, self.windows = entities, windows
        self.table = subtype_table(entities)
        self.edges, self.edge_ids, self.vertex_ids, self.points = [], {}, {}, []
        self.regions = None

    def vertex(self, index):
        if index not in self.vertex_ids:
            self.vertex_ids[index] = len(self.points)
            self.points.append(self.entities[self.entities[index].PointRef].PositionCm)
        return self.vertex_ids[index]

    def edge(self, index):
        if index in self.edge_ids:
            return self.edge_ids[index]
        node = self.entities[index]
        curve_node = self.entities[node.CurveRef]
        curve = SplineCurve(curve_node.Curve)
        jumps = jumps_of(curve_node.Curve)
        if FormCurve(curve, jumps) != curve_node.Curve or curve_node.Reversed or node.Reversed:
            raise ValueError('edge curve is outside the exact_int_cur form')
        bounds = (node.StartParam, node.EndParam)
        bounds = None if bounds == (curve.Knots[0], curve.Knots[-1]) else bounds
        label = label_of(self.entities, node.Prefix.Attribute)
        windows = self.windows[label][1] if label else ()
        start, end = self.vertex(node.StartVertex), self.vertex(node.EndVertex)
        self.edge_ids[index] = len(self.edges)
        self.edges.append(FormEdge(start, end, curve, jumps, node.Convexity, label, windows, bounds))
        return self.edge_ids[index]

    def use(self, index, region_face):
        node = self.entities[index]
        pcurve = self.entities[node.Pcurve]
        body = pcurve.Curve.Body
        surface = resolve(body.Surface.Body[1], self.table)
        if surface.FaceIndex != region_face or pcurve.Reversed or (pcurve.OffsetU, pcurve.OffsetV) != (0.0, 0.0):
            raise ValueError('pcurve carrier or form differs from the builder contract')
        curve = NegateCurve(body.Spline) if node.Reversed else body.Spline
        return FormUse(self.edge(node.EdgeRef), node.Reversed, curve, body.FitTolerance)

    def face(self, index):
        node = self.entities[index]
        surface = resolve(self.entities[node.Surface].Surface, self.table)
        if not isinstance(surface, TsplineSurf):
            raise ValueError('face is not a converted T-spline surface')
        constants = (surface.Revision, surface.FitTolerance, surface.Ranges, surface.TypeCode)
        if constants != (23100, 0.0, (1.0, 0.0, 1.0, 0.0), 0):
            raise ValueError(f'unexpected t_spl_sur constants {constants}')
        scope = resolve(surface.Subtrans, self.table)
        if not isinstance(scope, SubtransNode):
            raise ValueError('t_spl_sur names no subtransform scope')
        self.regions = scope.Regions if self.regions is None else self.regions
        if scope.Regions != self.regions:
            raise ValueError('faces disagree on the patch program')
        uses = tuple(self.use(use, surface.FaceIndex) for use in walk_loop(self.entities, index))
        form = FormSurface(surface.Cache, surface.Jumps, surface.FaceIndex)
        return FormFace(form, uses, label_of(self.entities, node.Prefix.Attribute), node.DoubleSided, node.Contained), scope.Surface


def extract(path):
    model = ReadDocument(Path(path).read_bytes())
    if len(model.Forms) != 1 or len(model.Bodies) != 1:
        raise ValueError('expected exactly one Form and one BRep body')
    history = model.Bodies[0].History
    if not isinstance(history, JournalModel):
        raise ValueError('native body is not a journal')
    entities = history.Entities[: history.ActiveCount]
    reader = Reader(entities, windows_by_tag(model))
    faces, cages = zip(*(reader.face(index) for index in walk_faces(entities)))
    if any(cage != model.Forms[0].Surface for cage in cages):
        raise ValueError('embedded cage differs from the document T-spline part')
    body = FormBody(tuple(reader.points), tuple(reader.edges), tuple(faces), reader.regions)
    return model.Forms[0].Surface, body, model


def native_marks(model):
    history = model.Bodies[0].History
    micros = next(e.UnixMicros for e in history.Entities if isinstance(e, TimeAttrib))
    return history.Stamp, int(micros)


def without_tags(entities, keep_body):
    result = []
    for entity in entities:
        prefix = getattr(entity, 'Prefix', None)
        if isinstance(prefix, EntityPrefix) and prefix.EntityTag != -1 and not (keep_body and isinstance(entity, BodyNode)):
            entity = replace(entity, Prefix=replace(prefix, EntityTag=-1))
        result.append(entity)
    return tuple(result)


def face_windows(body):
    result = {}
    for face in body.Faces:
        if face.Label:
            cells = sorted(body.Regions[face.Surface.Region], key=lambda cell: cell.Face)
            result[face.Label] = (0, tuple(FormWindow(c.Face, float(c.Window[0]), float(c.Window[1]), float(c.Window[2]), float(c.Window[3])) for c in cells))
    for edge in body.Edges:
        if edge.Label:
            result[edge.Label] = (1, edge.Windows)
    return result


__all__ = ['extract', 'native_marks', 'without_tags', 'face_windows', 'windows_by_tag', 'GeometryState', 'ValueObject', 'LocalRef']
