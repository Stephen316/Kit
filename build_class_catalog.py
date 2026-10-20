"""Aggregate opaque native class IDs and observed meanings from a local corpus.

Labels are evidence from the partial decoder, not a complete class schema.
Unknown classes retain GUIDs, ancestry and namespaces without guessed names.
"""

import argparse
import json
from pathlib import Path

from decode_basics import decode_basics


def build_catalog(paths, zstd_library=None):
    classes, examples = {}, []
    for path in paths:
        decoded = decode_basics(path, zstd_library)
        examples.append(str(path))
        for stream in decoded["streams"]:
            for entry in stream["record_index"].get("class_registry", []):
                guid = entry["class_guid"]
                current = classes.setdefault(guid, {"class_guid": guid, "base_class_guids": set(),
                                                    "namespaces": set(), "stored_versions_or_flags": set(),
                                                    "observed_semantics": set(), "example_files": set()})
                current["base_class_guids"].add(entry["base_class_guid"])
                current["namespaces"].add(entry["namespace"])
                current["stored_versions_or_flags"].add(entry["stored_version_or_flags"])
                if entry["record_count"] and len(current["example_files"]) < 3:
                    current["example_files"].add(str(path))
            for feature in stream["features"]:
                for constraint in feature.get("constraints", []):
                    if constraint.get("class_guid") in classes:
                        entry = classes[constraint["class_guid"]]
                        entry["observed_semantics"].add("Observed sketch relationship: "+constraint["kind"])
                        if len(entry["example_files"]) < 3:
                            entry["example_files"].add(str(path))
                if feature.get("class_guid"):
                    entry = classes[feature["class_guid"]]
                    if feature["kind"] == "UnsupportedFeature":
                        label = feature.get("native_kind_label")
                        entry["observed_semantics"].add("Unsupported feature with stored label: "+label if label
                                                        else "Observed feature ancestry; schema unsupported")
                    else:
                        entry["observed_semantics"].add("Named feature: "+feature["kind"])
                    if len(entry["example_files"]) < 3:
                        entry["example_files"].add(str(path))
            parameters = [p for f in stream["features"] for p in f["parameters"]]+stream["unbound_parameters"]
            properties = stream.get("body_properties", {})
            for key, label in (("bodies", "Observed native body properties"),
                               ("collections", "Observed native body collection membership")):
                for item in properties.get(key, []):
                    if item.get("class_guid") in classes:
                        entry = classes[item["class_guid"]]
                        entry["observed_semantics"].add(label)
                        if len(entry["example_files"]) < 3:
                            entry["example_files"].add(str(path))
            for parameter in parameters:
                if parameter.get("class_guid"):
                    entry = classes[parameter["class_guid"]]
                    entry["observed_semantics"].add("Observed numeric model parameter")
                    if len(entry["example_files"]) < 3:
                        entry["example_files"].add(str(path))
    normalized = []
    for guid, entry in sorted(classes.items()):
        normalized.append({key: sorted(value) if isinstance(value, set) else value for key, value in entry.items()})
    return {"scope": "Observed native class identities across a local Fusion corpus; not a field schema",
            "file_count": len(examples), "files": examples, "class_count": len(classes),
            "classes_with_observed_semantics": sum(bool(c["observed_semantics"]) for c in normalized),
            "classes": normalized}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps(build_catalog(args.files, args.zstd_library), indent=2))
