from collections import Counter


def root_sketch_rows(document):
    if not isinstance(document, dict) or document.get("$type") != "CadDocument":
        return [], []
    source = document.get("source")
    if (
        not isinstance(source, dict)
        or source.get("$type") != "CadSource"
        or any(
            not isinstance(source.get(name), str)
            for name in ("format_id", "path", "sha256")
        )
    ):
        return [], []
    collections = {}
    for name in (
        "configurations",
        "parameters",
        "support_planes",
        "sketches",
        "selections",
        "feature_timeline",
        "bodies",
    ):
        value = document.get(name)
        if (
            not isinstance(value, dict)
            or len(value) != 1
            or "$tuple" not in value
            or not isinstance(value["$tuple"], list)
        ):
            return [], []
        collections[name] = value["$tuple"]
    if not collections["configurations"]:
        return [], []
    return collections["sketches"], collections["feature_timeline"]


def is_root_row(value, path, name, rows):
    parts = path.split("/")
    if (
        len(parts) != 4
        or parts[:3] != ["", name, "$tuple"]
        or not parts[3].isascii()
        or not parts[3].isdigit()
    ):
        return False
    index = int(parts[3])
    return index < len(rows) and rows[index] is value


def record_sketch(value, path, rows, counts, eligible):
    if not is_root_row(value, path, "sketches", rows):
        return
    identity = value.get("id")
    if not isinstance(identity, str) or not 1 <= len(identity) <= 512:
        return
    counts[identity] += 1
    entities = value.get("entities")
    if (
        isinstance(value.get("name"), str)
        and isinstance(value.get("support_plane_id"), str)
        and isinstance(entities, dict)
        and len(entities) == 1
        and "$tuple" in entities
        and isinstance(entities["$tuple"], list)
    ):
        eligible.add(identity)


def is_sketch_reference(value, path, sketches, steps):
    if not is_root_row(value, path, "feature_timeline", steps):
        return False
    kind = value.get("kind")
    reference = kind == "reference" or (
        isinstance(kind, dict)
        and len(kind) == 2
        and "$enum" in kind
        and "value" in kind
        and kind["$enum"] == "FeatureKind"
        and kind["value"] == "reference"
    )
    target = value.get("sketch_id")
    return (
        reference
        and "operation" in value
        and value["operation"] is None
        and "definition" in value
        and value["definition"] is None
        and isinstance(target, str)
        and sketches.get(target) == 1
    )


def reader_evidence(document):
    sketch_rows, steps = root_sketch_rows(document)
    sketch_counts, eligible_sketches = Counter(), set()
    missing_definitions = []
    records = []
    unresolved = []
    fields = []
    stack = [(document, "", None)]
    while stack:
        value, path, provenance = stack.pop()
        if len(records) + len(fields) + len(unresolved) + len(stack) > 200000:
            raise ValueError("reader evidence exceeds 200000 entries")
        if isinstance(value, dict):
            provenance = value.get("provenance") or provenance
            kind = value.get("$type")
            if kind == "Sketch":
                record_sketch(
                    value, path, sketch_rows, sketch_counts, eligible_sketches
                )
            if kind:
                status = "typed_unverified"
                missing = None
                if kind in {"NativeFeatureDefinition", "NativeGeometry"}:
                    status = "native_only"
                    unresolved.append({"path": path, "reason": "native_only_record"})
                if kind == "FeatureStep" and value.get("definition") is None:
                    status = "partially_interpreted"
                    missing = {
                        "path": path + "/definition",
                        "reason": "missing_feature_definition",
                    }
                    unresolved.append(missing)
                records.append(
                    {
                        "path": path,
                        "type": kind,
                        "id": value.get("id"),
                        "status": status,
                        "provenance": provenance,
                        "span_scope": (
                            "enclosing_record_only" if provenance else "unavailable"
                        ),
                    }
                )
                if missing is not None:
                    missing_definitions.append((value, path, records[-1], missing))
                if kind in {"ExtrusionFeature", "RevolutionFeature"}:
                    unresolved.append(
                        {
                            "path": path,
                            "reason": "direction_frame_operation_require_independent_evidence",
                        }
                    )
                if kind == "Parameter":
                    attributes = value.get("attributes", {})
                    if attributes.get("unresolved_inch_dimension") is True:
                        unresolved.append(
                            {
                                "path": path + "/value",
                                "reason": "unresolved_inch_dimension",
                                "display": attributes.get("source_text"),
                            }
                        )
                    if "unresolved_equation_references" in attributes:
                        references = attributes["unresolved_equation_references"]
                        unresolved.append(
                            {
                                "path": path + "/expression",
                                "reason": "unresolved_equation_reference",
                                "references": references["$tuple"],
                            }
                        )
                if kind == "CadDocument":
                    target_key = "solidworks.unresolvedEquationReferences"
                    metadata = value.get("metadata", {})
                    targets = (
                        metadata.get(target_key, {})
                        if isinstance(metadata, dict)
                        else {}
                    )
                    if isinstance(targets, dict):
                        for index, target in enumerate(targets.get("$tuple", ())):
                            unresolved.append(
                                {
                                    "path": f"{path}/metadata/{target_key}/$tuple/{index}",
                                    "reason": "unresolved_equation_target",
                                    "target": target,
                                }
                            )
                if kind == "Diagnostic":
                    unresolved.append(
                        {
                            "path": path,
                            "reason": "reader_diagnostic",
                            "diagnostic": value,
                        }
                    )
            if "$bytes" in value:
                unresolved.append(
                    {
                        "path": path,
                        "reason": "retained_bytes_are_not_portable_semantics",
                    }
                )
                continue
            for key, child in reversed(sorted(value.items())):
                if key == "provenance":
                    continue
                pointer = key.replace("~", "~0").replace("/", "~1")
                stack.append((child, path + "/" + pointer, provenance))
        elif isinstance(value, list):
            stack.extend(
                (child, path + "/" + str(index), provenance)
                for index, child in reversed(list(enumerate(value)))
            )
        else:
            fields.append(
                {"path": path, "status": "reader_observation", "provenance": provenance}
            )
            if isinstance(value, str) and value.startswith("native:"):
                unresolved.append(
                    {
                        "path": path,
                        "reason": "uninterpreted_native_code",
                        "value": value,
                    }
                )
    sketches = {identity: sketch_counts[identity] for identity in eligible_sketches}
    recognized = set()
    for value, path, record, missing in missing_definitions:
        if is_sketch_reference(value, path, sketches, steps):
            record["status"] = "typed_unverified"
            recognized.add(id(missing))
    unresolved = [issue for issue in unresolved if id(issue) not in recognized]
    unresolved.append(
        {
            "path": "",
            "reason": "independent_source_inventory_and_native_acceptance_unavailable",
        }
    )
    return {
        "records": records,
        "fields": fields,
        "unresolved": unresolved,
        "semantic_qualification": "unverified",
        "byte_accounting": "unavailable",
        "portable_complete": False,
        "native_acceptance": "not_established",
        "counts": {
            "records": len(records),
            "fields": len(fields),
            "unresolved": len(unresolved),
        },
    }
