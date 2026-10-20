"""Read the observed version-8 MetaStream class registry and object offset tables.

The registry associates file-local decimal type codes (starting at 256) with
opaque class GUIDs, a base class, namespace, stored version/flags and primary
object IDs. No readable class names or complete field schema are provided.
"""

from collections import Counter
import struct

from fusion_records import Record, record_fragments


class Reader:
    def __init__(self, data):
        self.data, self.position = data, 0

    def take(self, size):
        if size < 0 or self.position+size > len(self.data):
            raise ValueError("Truncated Fusion metadata")
        result = self.data[self.position:self.position+size]
        self.position += size
        return result

    def u32(self):
        return struct.unpack("<I", self.take(4))[0]

    def u64(self):
        return struct.unpack("<Q", self.take(8))[0]

    def count(self, maximum=1000000):
        value = self.u32()
        if value > maximum:
            raise ValueError("Fusion metadata count exceeds the supported limit")
        return value

    def string(self, wide=False):
        length = self.count(4096)
        text = self.take(length*(2 if wide else 1)).decode("utf-16le" if wide else "ascii")
        if text and not text.isprintable():
            raise ValueError("Unprintable Fusion metadata string")
        return text

    def object_list(self):
        return [self.u64() for _ in range(self.count())]

    def offset_table(self):
        return [(self.u64(), self.u64()) for _ in range(self.count())]


def parse_metadata(data):
    reader = Reader(data)
    kind = reader.string()
    segment_index, namespace = reader.u32(), reader.string(True)
    magic, version, field_one, field_two = [reader.u32() for _ in range(4)]
    repeated_kind, storage_namespace = reader.string(), reader.string()
    storage_fields = [reader.u32(), reader.u32()]
    observed_storage_fields = {"FusionDesignSegmentType": [1, 0], "FusionBrowserSegmentType": [6, 0],
                               "FusionACTSegmentType": [5, 0]}
    if (magic != 1234 or version != 8 or kind != repeated_kind
            or storage_fields != observed_storage_fields.get(kind)):
        raise ValueError("Unsupported Fusion metadata header/version")
    classes, declared, guids = {}, {}, set()
    for index in range(reader.count(100000)):
        guid, base, flags, class_namespace = reader.string(), reader.string(), reader.u32(), reader.string()
        if not guid or guid in guids:
            raise ValueError("Missing or duplicate Fusion class GUID")
        guids.add(guid)
        objects = reader.object_list()
        code = str(256+index)
        for identity in objects:
            if identity in declared:
                raise ValueError("Duplicate primary object in Fusion class registry")
            declared[identity] = code
        classes[code] = {"type_code": code, "class_guid": guid, "base_class_guid": base,
                         "namespace": class_namespace, "stored_version_or_flags": flags,
                         "primary_object_count": len(objects)}
    stored_objects = reader.object_list()
    primary, continuations = reader.offset_table(), reader.offset_table()
    next_identity, reserved = reader.u64(), reader.u32()
    properties = {}
    for _ in range(reader.count(1024)):
        name, value = reader.string(), reader.u32()
        if name in properties:
            raise ValueError("Duplicate Fusion metadata property")
        properties[name] = value
    if reader.position != len(data):
        raise ValueError("Unconsumed bytes after Fusion metadata")
    if len(primary) != len(declared) or {i for i, _ in primary} != set(declared):
        raise ValueError("Fusion primary index and class registry disagree")
    if any(i not in declared for i, _ in continuations):
        raise ValueError("Continuation refers to an undeclared Fusion object")
    if declared and next_identity <= max(declared):
        raise ValueError("Invalid next Fusion object identity")
    return {"kind": kind, "segment_index": segment_index, "namespace": namespace,
            "version": version, "uninterpreted_header_fields": [field_one, field_two],
            "uninterpreted_storage_fields": storage_fields,
            "storage_namespace": storage_namespace, "classes": classes, "declared_types": declared,
            "stored_object_list": stored_objects, "primary": primary, "continuations": continuations,
            "next_object_id": next_identity, "reserved": reserved, "properties": properties}


def indexed_records(bulk, metadata):
    meta = parse_metadata(metadata)
    by_guid = {c["class_guid"]: c for c in meta["classes"].values()}
    entries = [(offset, identity, True) for identity, offset in meta["primary"]]
    entries += [(offset, identity, False) for identity, offset in meta["continuations"]]
    entries.sort()
    if not entries or entries[0][0] != 0 or len({e[0] for e in entries}) != len(entries):
        raise ValueError("Invalid or duplicate Fusion record offsets")
    records = []
    for index, (start, identity, primary) in enumerate(entries):
        end = entries[index+1][0] if index+1 < len(entries) else len(bulk)
        if start+4 > end or end > len(bulk):
            raise ValueError("Fusion record index is outside BulkStream")
        length = struct.unpack_from("<I", bulk, start)[0]
        if not 1 <= length <= 8 or start+12+length > end:
            raise ValueError("Unsupported indexed Fusion record header")
        code = bulk[start+4:start+4+length]
        if not code.isdigit() or code.decode() not in meta["classes"]:
            raise ValueError("Indexed Fusion class code is not registered")
        code = code.decode()
        stored_identity = struct.unpack_from("<Q", bulk, start+4+length)[0]
        if stored_identity != identity or (primary and code != meta["declared_types"][identity]):
            raise ValueError("Indexed Fusion object/header identity or class mismatch")
        if not primary:
            guid = meta["classes"][meta["declared_types"][identity]]["base_class_guid"]
            ancestors = set()
            while guid and guid in by_guid and guid not in ancestors:
                ancestors.add(guid)
                guid = by_guid[guid]["base_class_guid"]
            if meta["classes"][code]["class_guid"] not in ancestors:
                raise ValueError("Continuation class is not an ancestor of its primary object class")
        payload_start = start+12+length
        # Existing observed layout readers begin four bytes after the raw
        # payload. Retain that cursor while exposing the complete payload too.
        record = Record(start, min(payload_start+4, end), end, code, identity,
                        payload_start=payload_start, class_guid=meta["classes"][code]["class_guid"],
                        class_namespace=meta["classes"][code]["namespace"], is_primary=primary)
        records.append(record)
    counts = Counter(r.type_code for r in records)
    summary = {"source": "MetaStream version-8 class registry and object-offset tables",
               "status": "Indexed headers validated against object IDs, primary classes and continuation inheritance",
               "primary_objects": len(meta["primary"]), "continuations": len(meta["continuations"]),
               "indexed_records": len(records), "next_object_id": meta["next_object_id"],
               "class_registry": [{**item, "record_count": counts[code]}
                                  for code, item in meta["classes"].items()],
               "limitations": "Class GUIDs are opaque identifiers, not decoded field schemas."}
    return records, summary


def design_records(bulk, metadata=None):
    if metadata is not None:
        return indexed_records(bulk, metadata)
    records = record_fragments(bulk)
    return records, {"source": "Heuristic header scan; MetaStream was unavailable",
                     "status": "Provisional boundaries only", "indexed_records": 0}
