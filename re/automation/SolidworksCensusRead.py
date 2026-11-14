import hashlib
import json
import subprocess
import sys
from collections import Counter


def native_read(content, path):
    from convert.adapters.solidworks.container.Container import SldprtArchive
    from convert.adapters.solidworks.container.Format import KitDocStream
    from convert.adapters.solidworks.core.Adapter import NativePartModel

    try:
        archive = SldprtArchive.from_bytes(content, path)
        if archive.get(KitDocStream) is not None:
            raise ValueError("embedded Kit document is not native evidence")
        model = NativePartModel(archive, None)
    except (ValueError, TypeError, KeyError, RecursionError) as error:
        return {"status": "native_decode_failed", "error": str(error)[:2048]}

    return {
        "status": "decoded",
        "features": [
            {"name": item.name, "id": item.object_id, "kind": item.kind}
            for item in model.features
        ],
        "dimensions": [
            {
                "name": f"{dim.name}@{item.name}", "value_mm": dim.value_mm,
                "role": dim.native_role, "kind": dim.kind,
            }
            for item in model.features for dim in item.dimensions
        ],
        "sketches": [
            {
                "name": item.name, "support_kind": item.support_kind,
                "support_source": item.support_source, "support_plane_id": item.support_plane_id,
                "profiles": len(item.profiles), "constraint_count": len(item.constraints),
            }
            for item in model.sketches
        ],
        "operations": [
            {
                "name": item.name, "kind": item.kind, "profile_id": item.profile_id,
                "dependencies": item.dependencies, "length_mm": item.length_mm,
                "direction_code": item.direction_code, "termination_code": item.termination_code,
            }
            for item in model.operations
        ],
        "equations": [
            {
                "lhs": item.lhs, "rhs": item.rhs, "references": item.references,
                "stream": item.native_stream, "offset": item.native_offset,
            }
            for item in model.equations
        ],
        "diagnostics": list(model.diagnostics),
    }


def neutral_read(root, manifest, asset, output, revision):
    from interchange.document.models.DocumentModel import CadDocument

    command = [
        sys.executable, str(root / "re/automation/SolidworksReader.py"),
        "--manifest", str(manifest), "--asset", asset["path"], "--output", str(output),
    ]
    try:
        result = subprocess.run(
            command, cwd=root, capture_output=True, text=True, timeout=120, check=False
        )
    except subprocess.TimeoutExpired:
        return {"status": "reader_timeout"}
    if result.returncode:
        return {
            "status": "reader_rejected",
            "returncode": result.returncode,
            "error": result.stderr[-4096:],
        }

    receipt = json.loads((output / "receipt.json").read_bytes())
    content = (output / "document.json").read_bytes()
    neutral_sha = hashlib.sha256(content).hexdigest()
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    document = CadDocument.from_json(content.decode())
    if (
        receipt["source"] != asset or receipt["neutral_sha256"] != neutral_sha
        or receipt["manifest_sha256"] != manifest_sha
        or receipt["sdk_revision"] != revision or receipt["corpus_revision"] != revision
        or document.source.sha256 != asset["sha256"]
        or receipt["portable_complete"] is not False
        or receipt["native_acceptance"] != "not_established"
        or receipt["validation"] != "model_and_reconstruction_passed"
    ):
        raise ValueError(f"reader receipt identity or acceptance mismatch: {asset['path']}")
    return neutral_data(document, receipt)


def neutral_data(document, receipt):
    feature_names = {item.id: item.name for item in document.feature_timeline}
    parameter_names = {
        item.id: f"{item.name}@{feature_names.get(item.owner_id, item.owner_id)}"
        for item in document.parameters
    }
    plane_by_id = {item.id: item for item in document.support_planes}
    selection_by_id = {item.id: item for item in document.selections}
    return {
        "status": "decoded",
        "sdk_revision": receipt["sdk_revision"],
        "fingerprint": receipt["fingerprint"],
        "neutral_sha256": receipt["neutral_sha256"],
        "unresolved": dict(Counter(row["reason"] for row in receipt["unresolved"])),
        "canonical_unit": str(document.units),
        "native_display_unit": document.metadata.get("source_display_units"),
        "solid_count": sum(item.topology.solid_count for item in document.bodies),
        "features": [neutral_feature(item, feature_names) for item in document.feature_timeline],
        "parameters": [
            {
                "name": parameter_names[item.id], "id": item.id, "role": str(item.role),
                "value": item.value.value, "unit": item.value.unit,
                "expression": None if item.expression is None else {
                    "rhs": item.expression.source,
                    "parameter_ids": item.expression.parameter_ids,
                    "references": [parameter_names[key] for key in item.expression.parameter_ids],
                },
            }
            for item in document.parameters
        ],
        "sketches": [
            neutral_sketch(item, plane_by_id[item.support_plane_id], selection_by_id, feature_names)
            for item in document.sketches
        ],
    }


def neutral_feature(item, names):
    from interchange.features.FeatureExtrude import ExtrudeFeature

    definition = item.definition
    extrude = isinstance(definition, ExtrudeFeature)
    return {
        "name": item.name, "id": item.id, "kind": str(item.kind),
        "operation": None if item.operation is None else str(item.operation),
        "definition": type(definition).__name__ if definition is not None else None,
        "dependencies": [names.get(key, key) for key in item.input_feature_ids],
        "sketch_id": item.sketch_id,
        "selection_ids": item.selection_ids,
        "length_mm": definition.length.value if extrude and definition.length.unit == "mm" else None,
        "reversed": definition.reversed if extrude else None,
        "end_condition": str(definition.end_condition) if extrude else None,
        "native_direction_code": item.attributes.get("direction_code"),
        "native_termination_code": item.attributes.get("termination_code"),
        "direction_multiplier": item.attributes.get("direction_multiplier"),
    }


def vector(value):
    return value.x, value.y, value.z


def world_point(point, transform):
    return tuple(
        origin + point.x * x_axis + point.y * y_axis
        for origin, x_axis, y_axis in zip(
            vector(transform.origin), vector(transform.x_axis), vector(transform.y_axis), strict=True
        )
    )


def neutral_sketch(item, plane, selections, feature_names):
    from interchange.geometry.models.GeometryCurves import LineGeometry

    support = selections.get(plane.support_selection_id)
    return {
        "name": item.name, "id": item.id, "support_name": plane.name,
        "support_selection_id": plane.support_selection_id,
        "support_face_producer": next((
            feature_names.get(part.entity_id, part.entity_id) for part in support.path
            if part.subelement.startswith("face:")
        ), None) if support is not None else None,
        "support_path": [] if support is None else [
            {
                "kind": part.entity_kind, "entity_id": part.entity_id, "subelement": part.subelement,
            }
            for part in support.path
        ],
        "support_source": item.attributes.get("support_plane_source"),
        "basis": {
            "origin_mm": vector(plane.transform.origin), "u": vector(plane.transform.x_axis),
            "v": vector(plane.transform.y_axis), "normal": vector(plane.transform.z_axis),
        },
        "world_segments_mm": [
            (world_point(entity.geometry.start, plane.transform), world_point(entity.geometry.end, plane.transform))
            for entity in item.entities
            if not entity.construction and isinstance(entity.geometry, LineGeometry)
        ],
        "parameter_ids": item.parameter_ids,
        "relations": [
            {
                "kind": rel.kind, "parameter_id": rel.parameter_id, "driving": rel.driving,
                "reference_count": len(rel.references), "inferred": rel.attributes.get("inferred", False),
            }
            for rel in item.constraints
        ],
    }
