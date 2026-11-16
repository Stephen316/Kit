import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from interchange.Features.DistanceParam import KLengthFactors

COLLECTIONS = (
    "configurations",
    "parameters",
    "support_planes",
    "sketches",
    "selections",
    "feature_timeline",
    "bodies",
    "materials",
)
REFERENCES = {
    "ConstraintRef": {"entity_id"},
    "SketchRelation": {"parameter_id"},
    "Sketch": {"support_plane_id", "parameter_ids", "closed_profile_entity_ids"},
    "Parameter": {"owner_id"},
    "Expression": {"parameter_ids"},
    "SupportPlane": {"support_selection_id", "offset_parameter_id"},
    "SelectPathElem": {"entity_id"},
    "FeatureStep": {
        "input_feature_ids",
        "sketch_id",
        "parameter_ids",
        "selection_ids",
    },
    "Configuration": {"parent_id", "suppressed_feature_ids"},
    "ParamOverride": {"parameter_id"},
    "FeatureCfgState": {"configuration_id"},
    "DesignBody": {"final_feature_id", "material_id"},
    "DistanceExtrude": {
        "AlongParameterId",
        "AgainstParameterId",
        "StartOffsetId",
        "TaperParameterId",
        "SecondTaperId",
    },
    "PlaneExtrude": {
        "PlaneSelectionId",
        "OffsetParameterId",
        "LengthParameterId",
        "TaperParameterId",
    },
    "AngularRevolve": {"AxisSelectionId", "AlongParameterId", "AgainstParameterId"},
    "PlaneRevolve": {"AxisSelectionId", "PlaneSelectionIds"},
    "ExtrudeFeature": {"up_to_reference", "second_up_to_reference"},
}
UNORDERED_REFERENCES = {"parameter_ids", "suppressed_feature_ids"}
LENGTH_FIELDS = {
    "PointGeometry": {"point"},
    "LineGeometry": {"start", "end"},
    "CircleGeometry": {"center", "radius"},
    "ArcGeometry": {"center", "radius"},
    "EllipseGeometry": {"center", "major_radius", "minor_radius"},
    "ArcEllipseGeom": {"center", "major_radius", "minor_radius"},
    "HyperbolaGeom": {"center", "major_radius", "minor_radius"},
    "ArcHyperGeom": {"center", "major_radius", "minor_radius"},
    "ParabolaGeom": {"center", "focal_length"},
    "ArcParabGeom": {"center", "focal_length"},
    "SplineGeometry": {"control_points"},
    "Transform": {"origin"},
    "BoundingBox": {"minimum", "maximum"},
    "Selection": {"point"},
}
DIMENSIONLESS_FIELDS = {
    "Transform": {"x_axis", "y_axis", "z_axis"},
    "DistanceExtrude": {"Direction"},
    "PlaneExtrude": {"Direction"},
    "AngularRevolve": {"AxisDirection"},
    "PlaneRevolve": {"AxisDirection"},
    "ExtrudeFeature": {"direction"},
    "EllipseGeometry": {"major_axis"},
    "ArcEllipseGeom": {"major_axis"},
    "HyperbolaGeom": {"major_axis"},
    "ArcHyperGeom": {"major_axis"},
    "ParabolaGeom": {"axis"},
    "ArcParabGeom": {"axis"},
    "SplineGeometry": {"knots", "weights"},
    "MaterialRecord": {"ColorValue"},
}


def tag(value):
    return value.value if isinstance(value, Enum) else value


def pointer(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def evidence_digest(value):
    from interchange.serialization.EncodeData import ToData

    encoded = json.dumps(
        ToData(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def build_graph(document, geometry_unit, *, max_nodes=4096, max_fields=100000):
    if geometry_unit not in KLengthFactors:
        raise ValueError("geometry unit must explicitly select mm, cm, m, in or ft")
    if type(max_nodes) is not int or not 1 <= max_nodes <= 20000:
        raise ValueError("node limit must be an integer from 1 through 20000")
    if type(max_fields) is not int or not 1 <= max_fields <= 200000:
        raise ValueError("field limit must be an integer from 1 through 200000")
    factor = KLengthFactors[geometry_unit]
    graph = {
        "nodes": {},
        "issues": [],
        "observations": [],
        "geometry_unit": geometry_unit,
    }
    count = 0

    def issue(path, reason, value=None):
        item = {"path": path, "reason": reason}
        if value is not None:
            item["evidence_sha256"] = evidence_digest(value)
        graph["issues"].append(item)

    def atom(node, path, value, quantity="exact", scale=1.0):
        nonlocal count
        count += 1
        if count > max_fields:
            raise ValueError("semantic graph exceeds its field limit")
        value = tag(value)
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("semantic graph contains a nonfinite number")
        if isinstance(value, str) and len(value) > 65536:
            raise ValueError("semantic field text exceeds 65536 characters")
        if (
            quantity != "exact"
            and value is not None
            and type(value) not in (int, float)
        ):
            raise ValueError("semantic quantities require numeric magnitudes")
        if type(value) in (int, float) and quantity != "exact":
            value *= scale
            if not math.isfinite(value):
                raise ValueError("normalized semantic quantity is nonfinite")
        node["fields"][path] = {"value": value, "quantity": quantity}

    def reference(node, role, value, ordered=True):
        if value is None or value == "":
            atom(node, role, value)
            return
        if isinstance(value, str):
            if len(value) > 512:
                raise ValueError("semantic reference exceeds 512 characters")
            node["links"].append({"role": role, "target": value})
            return
        if not isinstance(value, (tuple, list)):
            raise ValueError("semantic reference must be an identity or collection")
        atom(node, role + "/count", len(value))
        for index, child in enumerate(value):
            reference(node, role + (f"/{index}" if ordered else "/member"), child)

    def walk(node, value, path, quantity="exact", scale=1.0, depth=0):
        if depth > 48:
            raise ValueError("semantic graph exceeds its nesting limit")
        if isinstance(value, Enum):
            atom(node, path, value.value)
            if value.value == "native":
                issue(node["path"] + path, "uninterpreted_native_value", value)
            return
        if value is None or type(value) in (str, bool, int, float):
            atom(node, path, value, quantity, scale)
            if isinstance(value, str) and (
                value == "native" or value.startswith("native:")
            ):
                issue(node["path"] + path, "uninterpreted_native_value", value)
            return
        if isinstance(value, bytes):
            atom(node, path + "/size_bytes", len(value))
            atom(node, path + "/sha256", hashlib.sha256(value).hexdigest())
            issue(node["path"] + path, "retained_bytes_are_not_portable_semantics")
            return
        if isinstance(value, Mapping):
            atom(node, path + "/count", len(value))
            for key in sorted(value):
                if not isinstance(key, str):
                    raise ValueError("semantic mapping requires text keys")
                walk(node, value[key], path + "/" + pointer(key), depth=depth + 1)
            return
        if isinstance(value, (tuple, list, set, frozenset)):
            children = (
                sorted(value, key=lambda item: str(tag(item)))
                if isinstance(value, (set, frozenset))
                else value
            )
            atom(node, path + "/count", len(children))
            for index, child in enumerate(children):
                walk(node, child, path + f"/{index}", quantity, scale, depth + 1)
            return
        if not is_dataclass(value):
            raise ValueError("semantic graph contains an unsupported record")
        kind = type(value).__name__
        atom(node, path + "/record_type", kind)
        if kind in {"NativeGeometry", "NativeFeature", "NativeFeatureDefinition"}:
            issue(node["path"] + path, "native_only_record")
        if kind == "Expression" and value.language != "kit":
            issue(
                node["path"] + path, "uninterpreted_expression_language", value.language
            )
        if kind == "ParameterValue":
            category, unit = tag(value.kind), value.unit
            if category in {"length", "angle"} and type(value.value) not in (
                int,
                float,
            ):
                raise ValueError("dimensional parameters require numeric magnitudes")
            if category == "length" and unit in KLengthFactors:
                atom(node, path + "/kind", category)
                atom(
                    node,
                    path + "/value",
                    value.value,
                    "length_mm",
                    KLengthFactors[unit],
                )
                graph["observations"].append(
                    {"path": node["path"] + path, "original_unit": unit}
                )
                return
            if category == "angle" and unit in {"rad", "deg"}:
                atom(node, path + "/kind", category)
                atom(
                    node,
                    path + "/value",
                    value.value,
                    "angle_rad",
                    1.0 if unit == "rad" else math.pi / 180,
                )
                graph["observations"].append(
                    {"path": node["path"] + path, "original_unit": unit}
                )
                return
            if category in {"length", "angle", "quantity"} or unit:
                issue(node["path"] + path, "unsupported_parameter_quantity", value)
        for field in fields(value):
            name = field.name
            child = getattr(value, name)
            location = path + "/" + pointer(name)
            if kind == "FeatureStep" and name == "definition" and child is None:
                issue(node["path"] + location, "missing_feature_definition")
            if name in {"id", "EntityId", "provenance"} or (
                name in {"name", "EntityName"} and kind != "MaterialRecord"
            ):
                graph["observations"].append(
                    {
                        "path": node["path"] + location,
                        "evidence_sha256": evidence_digest(child),
                    }
                )
                continue
            if name in {"attributes", "metadata"}:
                if child:
                    issue(
                        node["path"] + location,
                        "unclassified_native_or_extension_fields",
                        child,
                    )
                continue
            if name in REFERENCES.get(kind, set()):
                reference(node, location, child, name not in UNORDERED_REFERENCES)
                continue
            if kind == "Sketch" and name in {"entities", "constraints"}:
                atom(node, location + "/count", len(child))
                continue
            child_quantity, child_scale = quantity, scale
            if name in LENGTH_FIELDS.get(kind, set()):
                child_quantity, child_scale = "length_mm", factor
            elif name in DIMENSIONLESS_FIELDS.get(kind, set()):
                child_quantity, child_scale = "dimensionless", 1.0
            elif kind in {"AngularRevolve", "PlaneRevolve"} and name == "AxisOrigin":
                child_quantity, child_scale = "length_mm", 1.0
            elif kind == "TopologyCounts" and name == "volume":
                child_quantity, child_scale = "volume_mm3", factor**3
            elif kind == "TopologyCounts" and name == "surface_area":
                child_quantity, child_scale = "area_mm2", factor**2
            elif name in {"start_angle", "end_angle"} and kind in {
                "ArcGeometry",
                "ArcEllipseGeom",
                "ArcHyperGeom",
                "ArcParabGeom",
            }:
                child_quantity, child_scale = "angle_rad", 1.0
            elif kind == "PlaneRevolve" and name in {"StartRadians", "EndRadians"}:
                child_quantity, child_scale = "angle_rad", 1.0
            walk(node, child, location, child_quantity, child_scale, depth + 1)

    def add(value, path, owner, role):
        identity = value.id
        if not isinstance(identity, str) or not identity or len(identity) > 512:
            raise ValueError("semantic node requires a bounded nonempty identity")
        if identity in graph["nodes"] or len(graph["nodes"]) >= max_nodes:
            raise ValueError(
                "semantic node identity is duplicated or exceeds its limit"
            )
        kind = type(value).__name__
        if hasattr(value, "kind"):
            kind += ":" + str(tag(value.kind))
        label = value.name if hasattr(value, "name") else None
        if label is not None and (not isinstance(label, str) or len(label) > 65536):
            raise ValueError("semantic label exceeds its text limit")
        node = {"kind": kind, "fields": {}, "links": [], "path": path, "label": label}
        graph["nodes"][identity] = node
        graph["nodes"][owner]["links"].append({"role": role, "target": identity})
        node["links"].append({"role": "owned_by", "target": owner})
        walk(node, value, "")
        if type(value).__name__ == "Sketch":
            for collection in ("entities", "constraints"):
                for index, child in enumerate(getattr(value, collection)):
                    add(child, path + f"/{collection}/{index}", identity, collection)

    root = {"kind": "CadDocument", "fields": {}, "links": [], "path": ""}
    graph["nodes"]["@document"] = root
    atom(root, "/schema_version", document.schema_version)
    walk(root, document.capabilities, "/capabilities")
    graph["observations"].append(
        {"path": "/units", "original_unit": tag(document.units)}
    )
    for collection in COLLECTIONS:
        records = getattr(document, collection)
        atom(root, "/" + collection + "/count", len(records))
        for index, value in enumerate(records):
            add(value, f"/{collection}/{index}", "@document", collection)
    for name in (
        "assembly",
        "brep",
        "brep_payloads",
        "meshes",
        "diagnostics",
        "metadata",
    ):
        value = getattr(document, name)
        if value:
            issue("/" + name, "domain_requires_independent_comparison", value)
    for identity, node in graph["nodes"].items():
        for link in node["links"]:
            if link["target"] not in graph["nodes"]:
                issue(
                    node["path"] + link["role"], "unresolved_reference", link["target"]
                )
    graph["field_count"] = count
    return graph
