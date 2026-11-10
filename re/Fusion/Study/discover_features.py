"""Use observed class ancestry to expose unsupported feature records explicitly."""

import re
import struct

from decode_parameters import read_string


FEATURE_BASE_GUID = "A2052F46-21B4-4AAA-9AF1-C371F0AB6CAB"


def discover_features(data, records, known_features, record_index):
    registry = {c["class_guid"]: c for c in record_index.get("class_registry", [])}
    known_ids = {f["object_id"] for f in known_features}
    found = []
    for record in records:
        if not record.is_primary or record.object_id in known_ids:
            continue
        guid, seen = record.class_guid, set()
        while guid in registry and guid not in seen and guid != FEATURE_BASE_GUID:
            seen.add(guid)
            guid = registry[guid]["base_class_guid"]
        if guid != FEATURE_BASE_GUID:
            continue
        body = data[record.body:record.end]
        labels = set()
        for position in range(max(0, len(body)-4)):
            length = struct.unpack_from("<I", body, position)[0]
            if not 2 <= length <= 64:
                continue
            try:
                label, cursor = read_string(body, position)
                index = struct.unpack_from("<Q", body, cursor)[0]
                name, _ = read_string(body, cursor+8)
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9 _/-]{1,63}", label) and index < 2**32:
                    labels.add((label, index, name))
            except (ValueError, UnicodeError, struct.error):
                continue
        label, index, name = next(iter(labels)) if len(labels) == 1 else (None, None, None)
        found.append({"kind": "UnsupportedFeature", "object_id": record.object_id,
                      "native_kind_label": label, "stored_index": index, "name": name or None,
                      "record_offset": record.start, "type_code": record.type_code,
                      "class_guid": record.class_guid, "class_namespace": record.class_namespace,
                      "parameters": [], "discovery": "Explicit class ancestry includes observed feature base GUID",
                      "decode_level": "Unsupported feature class; available label and parameters only"})
    known_features.extend(found)
    known_features.sort(key=lambda f: f["record_offset"])
    return {"method": "Observed feature class ancestry from MetaStream" if registry else "Unavailable without MetaStream",
            "recognized_named_feature_count": len(known_ids), "unsupported_feature_count": len(found),
            "unsupported_features": [{k: f[k] for k in ("object_id", "class_guid", "native_kind_label", "record_offset")}
                                     for f in found],
            "scope": "Observed feature base class only; unsupported fields and unknown ancestry remain undecoded"}
