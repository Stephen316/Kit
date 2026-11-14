def reader_evidence(document):
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
            if kind:
                status = "typed_unverified"
                if kind in {"NativeFeatureDefinition", "NativeGeometry"}:
                    status = "native_only"
                    unresolved.append({"path": path, "reason": "native_only_record"})
                if kind == "FeatureStep" and value.get("definition") is None:
                    status = "partially_interpreted"
                    unresolved.append({"path": path + "/definition", "reason": "missing_feature_definition"})
                records.append({
                    "path": path, "type": kind, "id": value.get("id"),
                    "status": status, "provenance": provenance,
                    "span_scope": "enclosing_record_only" if provenance else "unavailable",
                })
                if kind in {"ExtrusionFeature", "RevolutionFeature"}:
                    unresolved.append({
                        "path": path, "reason": "direction_frame_operation_require_independent_evidence",
                    })
                if kind == "Parameter":
                    attributes = value.get("attributes", {})
                    if attributes.get("unresolved_inch_dimension") is True:
                        unresolved.append({
                            "path": path + "/value",
                            "reason": "unresolved_inch_dimension",
                            "display": attributes.get("source_text"),
                        })
                    if "unresolved_equation_references" in attributes:
                        references = attributes["unresolved_equation_references"]
                        unresolved.append({
                            "path": path + "/expression",
                            "reason": "unresolved_equation_reference",
                            "references": references["$tuple"],
                        })
                if kind == "CadDocument":
                    target_key = "solidworks.unresolvedEquationReferences"
                    metadata = value.get("metadata", {})
                    targets = metadata.get(target_key, {}) if isinstance(metadata, dict) else {}
                    if isinstance(targets, dict):
                        for index, target in enumerate(targets.get("$tuple", ())):
                            unresolved.append({
                                "path": f"{path}/metadata/{target_key}/$tuple/{index}",
                                "reason": "unresolved_equation_target",
                                "target": target,
                            })
                if kind == "Diagnostic":
                    unresolved.append({"path": path, "reason": "reader_diagnostic", "diagnostic": value})
            if "$bytes" in value:
                unresolved.append({"path": path, "reason": "retained_bytes_are_not_portable_semantics"})
                continue
            for key, child in reversed(sorted(value.items())):
                if key == "provenance":
                    continue
                pointer = key.replace("~", "~0").replace("/", "~1")
                stack.append((child, path + "/" + pointer, provenance))
        elif isinstance(value, list):
            stack.extend((child, path + "/" + str(index), provenance) for index, child in reversed(list(enumerate(value))))
        else:
            fields.append({"path": path, "status": "reader_observation", "provenance": provenance})
            if isinstance(value, str) and value.startswith("native:"):
                unresolved.append({"path": path, "reason": "uninterpreted_native_code", "value": value})
    unresolved.append({
        "path": "", "reason": "independent_source_inventory_and_native_acceptance_unavailable",
    })
    return {
        "records": records, "fields": fields, "unresolved": unresolved,
        "semantic_qualification": "unverified",
        "byte_accounting": "unavailable",
        "portable_complete": False,
        "native_acceptance": "not_established",
        "counts": {"records": len(records), "fields": len(fields), "unresolved": len(unresolved)},
    }
