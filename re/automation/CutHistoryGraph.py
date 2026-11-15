"""Extract archive-backed operation roles for the bounded P04 comparison."""

import math
from dataclasses import dataclass

from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


class GraphGap(ValueError):
    def __init__(self, reason, status="unclassified"):
        super().__init__(reason)
        self.status = status


@dataclass(frozen=True)
class ProfileRole:
    feature: FeatureStep
    owner: FeatureStep
    sketch: Sketch
    plane: SupportPlane
    perimeter: tuple


@dataclass(frozen=True)
class CutHistory:
    base: ProfileRole
    cut: ProfileRole
    support: Selection
    target: Selection
    body: DesignBody
    parameters: dict[str, Parameter]


def check(condition, reason, status="unclassified"):
    if not condition:
        raise GraphGap(reason, status)


def unique(values, role):
    candidates = tuple(values)
    check(candidates, f"missing {role}")
    check(len(candidates) == 1, f"multiple candidates for {role}", "ambiguous")
    return candidates[0]


def index(values, role):
    indexed = {item.id: item for item in values}
    check(len(indexed) == len(values), f"duplicate {role} identities", "ambiguous")
    return indexed


def ref(values, key, role):
    check(key in values, f"unresolved {role}")
    return values[key]


def xyz(vector):
    return (vector.x, vector.y, vector.z)


def world(frame, point):
    along = OffsetVector(frame.origin, frame.x_axis, point.x)
    return xyz(OffsetVector(along, frame.y_axis, point.y))


def profile_role(document, steps, feature):
    sketch = ref(
        index(document.sketches, "sketch"), feature.sketch_id, "profile sketch"
    )
    inputs = tuple(
        ref(steps, key, "feature input") for key in feature.input_feature_ids
    )
    owner = unique(
        (
            item
            for item in inputs
            if item.sketch_id == sketch.id and item.operation is None
        ),
        "profile sketch owner",
    )
    check(
        not sketch.suppressed and not owner.suppressed and owner.order < feature.order,
        "inactive or out of order profile sketch owner",
    )
    plane = ref(
        index(document.support_planes, "support plane"),
        sketch.support_plane_id,
        "profile plane",
    )
    loop = unique(sketch.closed_profile_entity_ids, "selected profile perimeter")
    check(len(loop) == len(set(loop)) == 4, "expected four distinct perimeter members")
    if "fusion.profile_entity_ids" in feature.attributes:
        check(
            frozenset(feature.attributes["fusion.profile_entity_ids"])
            == frozenset(loop),
            "feature and sketch disagree on the selected profile",
        )
    entities = index(sketch.entities, "sketch entity")
    perimeter = []
    for identity in loop:
        entity = ref(entities, identity, "profile boundary entity")
        check(
            isinstance(entity.geometry, LineGeometry)
            and not entity.construction
            and "fusion.projection_mode" not in entity.attributes,
            "selected profile contains an unsupported boundary entity",
        )
        line = entity.geometry
        perimeter.append(
            (
                identity,
                (world(plane.transform, line.start), world(plane.transform, line.end)),
            )
        )
    return ProfileRole(feature, owner, sketch, plane, tuple(perimeter))


def selected_producer(selection, steps, role):
    sources = {
        part.entity_id for part in selection.path if part.entity_kind == "feature"
    }
    query_source = selection.query.get("source_feature_id")
    if query_source:
        sources.add(query_source)
    key = unique(sources, role)
    return ref(steps, key, role)


def read_history(document):
    steps = index(document.feature_timeline, "feature")
    selections = index(document.selections, "selection")
    body = unique(document.bodies, "final body")
    cutter = unique(
        (item for item in steps.values() if item.operation == BooleanOp.KCutOperation),
        "Cut operation",
    )
    check(
        cutter.kind == FeatureKind.KExtrusion
        and not cutter.suppressed
        and body.final_feature_id == cutter.id,
        "Cut does not own the final body",
    )
    cut = profile_role(document, steps, cutter)
    support = ref(selections, cut.plane.support_selection_id, "Cut support selection")
    check(
        support.query.get("role") == "sketch_support"
        and support.query.get("kind")
        in ("historical_face_recipe", "historical_face_occurrence"),
        "Cut is missing its saved historical support face",
    )
    targets = tuple(
        ref(selections, key, "Cut selection") for key in cutter.selection_ids
    )
    target = unique(
        (
            item
            for item in targets
            if item.query.get("role") == "target"
            or item.query.get("topology_role") == "historical_cut_target"
        ),
        "Cut target selection",
    )
    producer = selected_producer(support, steps, "support producer")
    check(
        selected_producer(target, steps, "target producer").id == producer.id
        and producer.order < cutter.order
        and producer.kind == FeatureKind.KExtrusion
        and producer.operation in (BooleanOp.KCreate, BooleanOp.KJoin)
        and not producer.suppressed,
        "Cut support and target lack the same earlier base extrusion producer",
    )
    base = profile_role(document, steps, producer)
    check(base.sketch.id != cut.sketch.id, "base and Cut share the same profile owner")
    return CutHistory(
        base, cut, support, target, body, index(document.parameters, "parameter")
    )


def length_mm(value):
    scales = {"cm": 10.0, "mm": 1.0}
    check(
        value is not None
        and value.kind == ValueKind.KLength
        and value.unit in scales
        and type(value.value) in (int, float)
        and math.isfinite(value.value),
        "unsupported length quantity",
    )
    return value.value * scales[value.unit]


def extent(role, parameters, cut):
    definition = role.feature.definition
    if not cut and isinstance(definition, DistanceExtrude):
        parameter = ref(
            parameters, definition.AlongParameterId, "base extent parameter"
        )
        check(
            definition.SideMode == "one_sided"
            and definition.StartOffsetId is None
            and parameter.owner_id == role.feature.id
            and parameter.id in role.feature.parameter_ids,
            "base extent lacks its single owned profile plane distance",
        )
        return "blind", abs(length_mm(parameter.value))
    check(isinstance(definition, ExtrudeFeature), "unsupported extrusion definition")
    condition = definition.end_condition
    if cut and condition == ExtrudeEnd.KThroughAll:
        check(
            definition.length is None, "through all unexpectedly has an active length"
        )
        return "through_all", None
    check(condition == ExtrudeEnd.KBlind, "unsupported end condition")
    return "blind", abs(length_mm(definition.length))


def plane_metrics(plane):
    frame = plane.transform
    normal, offset = xyz(frame.z_axis), DotVector(frame.z_axis, frame.origin)
    check(
        math.isclose(math.hypot(*normal), 1.0, rel_tol=0, abs_tol=1e-9)
        and math.isfinite(offset),
        "unsupported support plane normal or offset",
    )
    return normal, offset


def body_metrics(body, application):
    topo = body.topology
    centroid = body.attributes.get(f"{application}.body_centroid_mm")
    check(
        topo.solid_count == 1
        and topo.bounding_box is not None
        and topo.volume is not None
        and isinstance(centroid, tuple),
        "missing archived body measurements",
    )
    return {
        "counts": [topo.face_count, topo.edge_count, topo.vertex_count],
        "bounds_mm": [xyz(topo.bounding_box.minimum), xyz(topo.bounding_box.maximum)],
        "volume_mm3": topo.volume,
        "center_of_mass_mm": centroid,
    }
