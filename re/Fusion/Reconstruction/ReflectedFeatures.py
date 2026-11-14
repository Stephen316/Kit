import argparse
import ctypes
import hashlib
import json
import math
import re
import struct
import subprocess
import uuid
import zipfile
import zlib
from functools import cache
from pathlib import Path


ROOT_ENTITY = "98542EB9-A4F2-4137-A808-DBB5B3CD6159"
MANAGED_ENTITY = "CB844AB6-240D-4FC9-9C9F-3679DC896D6F"
TARGETS = {"8DA771B7-52ED-42FC-94E2-2353FE141373", "DD405BC2-D673-44F0-8833-5CB2A1C186C7"}
FORMATS = {
    "IntrinsicMetaTypebool": "B",
    "IntrinsicMetaTypeuint32": "I",
    "IntrinsicMetaTypeint32": "i",
    "IntrinsicMetaTypeuint64": "Q",
    "IntrinsicMetaTypedouble": "d",
}


@cache
def demangle(value):
    return subprocess.check_output(["c++filt", "-t", value], text=True).strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0
        self.evidence = []

    def take(self, count):
        if count < 0 or self.offset + count > len(self.data):
            raise ValueError(f"Truncated field at payload offset {self.offset}, requested {count}")
        start = self.offset
        self.offset += count
        return self.data[start:self.offset]

    def number(self, code):
        return struct.unpack("<" + code, self.take(struct.calcsize("<" + code)))[0]

    def count(self):
        value = self.number("I")
        if value > 1000000:
            raise ValueError(f"Excessive count {value} at {self.offset - 4}")
        return value

    def text(self, wide=False):
        return self.take(self.count() * (2 if wide else 1)).decode("utf-16le" if wide else "ascii")

    def boolean(self):
        value = self.number("B")
        if value not in (0, 1):
            raise ValueError(f"Invalid boolean {value} at {self.offset - 1}")
        return bool(value)

    def field(self, name, wire_type, read):
        start = self.offset
        value = read()
        self.evidence.append({"name": name, "wireType": wire_type, "offset": start, "length": self.offset - start, "value": value})
        return value


def encode_text(value, wide=False):
    if type(value) is not str:
        raise ValueError("Text value must be a string")
    encoded = value.encode("utf-16le" if wide else "ascii")
    count = len(encoded) // (2 if wide else 1)
    if count > 1000000:
        raise ValueError("Oversized text")
    return struct.pack("<I", count) + encoded


def read_reference(reader):
    tag = reader.number("B")
    if tag == 0:
        return None
    if tag != 1:
        raise ValueError(f"Unsupported reference tag {tag}")
    identity = reader.number("Q")
    if reader.take(2) != bytes(2):
        raise ValueError("Only local numeric references are supported")
    return {"entityId": identity}


def encode_reference(value):
    if value is None:
        return b"\0"
    if type(value) is not dict or set(value) != {"entityId"} or type(value["entityId"]) is not int:
        raise ValueError("Expected a typed local numeric reference")
    return struct.pack("<BQH", 1, value["entityId"], 0)


def collection_reference_kind(member):
    cpp_type = demangle(member["debug_type_name"])
    match = re.match(r"std::__1::(?:vector|list|set)<Ns::(StrongRef|PassiveRef)<", cpp_type)
    if not match:
        raise ValueError(f"Unsupported typed collection {cpp_type}")
    return match[1]


def read_member(reader, member):
    kind = member["metatype"]["name"]
    if kind in FORMATS:
        if kind == "IntrinsicMetaTypebool":
            return reader.boolean()
        value = reader.number(FORMATS[kind])
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Nonfinite numeric field is outside this profile")
        return value
    if kind == "IntrinsicMetaTypeIString":
        return reader.text(True)
    if kind == "IntrinsicMetaTypeUuid":
        value = reader.text(True)
        if str(uuid.UUID(value)) != value:
            raise ValueError("UUID is not canonical lowercase text")
        return value
    if kind == "AcGeVector3dValueMetaType":
        values = [reader.number("d") for _ in range(3)]
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Nonfinite vector coordinate")
        return dict(zip(("x", "y", "z"), values))
    if kind in ("StrongRefMetaType", "PassiveRefMetaType"):
        return read_reference(reader)
    if kind in ("Vector", "List", "Set"):
        collection_reference_kind(member)
        return [read_reference(reader) for _ in range(reader.count())]
    raise ValueError(f"Unsupported reflected member metatype {kind}")


def encode_member(member, value):
    kind = member["metatype"]["name"]
    if kind in FORMATS:
        if kind == "IntrinsicMetaTypebool":
            if type(value) is not bool:
                raise ValueError("Boolean field requires bool")
        elif kind == "IntrinsicMetaTypedouble":
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Double field requires a finite number")
        elif type(value) is not int:
            raise ValueError("Integer field requires int")
        return struct.pack("<" + FORMATS[kind], value)
    if kind == "IntrinsicMetaTypeIString":
        return encode_text(value, True)
    if kind == "IntrinsicMetaTypeUuid":
        if type(value) is not str or str(uuid.UUID(value)) != value:
            raise ValueError("UUID field requires canonical text")
        return encode_text(value, True)
    if kind == "AcGeVector3dValueMetaType":
        if type(value) is not dict or set(value) != {"x", "y", "z"}:
            raise ValueError("Vector requires x, y and z")
        if not all(type(value[key]) in (int, float) and math.isfinite(value[key]) for key in ("x", "y", "z")):
            raise ValueError("Vector coordinates must be finite numbers")
        return struct.pack("<ddd", value["x"], value["y"], value["z"])
    if kind in ("StrongRefMetaType", "PassiveRefMetaType"):
        return encode_reference(value)
    if kind in ("Vector", "List", "Set"):
        collection_reference_kind(member)
        if type(value) is not list or len(value) > 1000000:
            raise ValueError("Invalid collection")
        return struct.pack("<I", len(value)) + b"".join(encode_reference(item) for item in value)
    raise ValueError(f"Unsupported reflected member metatype {kind}")


def read_frame(reader, primary):
    result = {"rootId": reader.field("Entity.rootId", "u32 byte count + ASCII", reader.text)}
    if not primary:
        return result
    result["hasSubjects"] = reader.field("Entity.hasEntitySubjects", "bool", reader.boolean)
    result["subjects"] = []
    if result["hasSubjects"]:
        count = reader.field("Entity.subjectCount", "u32", reader.count)
        for index in range(count):
            subject = reader.field(f"Entity.subjects[{index}].subject", "PassiveRef", lambda: read_reference(reader))
            position = reader.field(f"Entity.subjects[{index}].indexInObserverVec", "i32", lambda: reader.number("i"))
            result["subjects"].append({"subject": subject, "indexInObserverVec": position})
    result["hasNamedMetadata"] = reader.field("Entity.hasNameValuePair", "bool", reader.boolean)
    result["namedMetadata"] = []
    if result["hasNamedMetadata"]:
        count = reader.field("Entity.nameValuePairCount", "u32", reader.count)
        if count:
            raise ValueError("Nonempty name/value metadata is unsupported")
    return result


def encode_frame(frame, primary):
    result = bytearray(encode_text(frame["rootId"]))
    if not primary:
        if set(frame) != {"rootId"}:
            raise ValueError("Unexpected continuation frame fields")
        return bytes(result)
    if set(frame) != {"rootId", "hasSubjects", "subjects", "hasNamedMetadata", "namedMetadata"}:
        raise ValueError("Unexpected primary frame fields")
    if type(frame["hasSubjects"]) is not bool or type(frame["hasNamedMetadata"]) is not bool:
        raise ValueError("Frame presence flags require bool")
    result.extend(struct.pack("<B", frame["hasSubjects"]))
    if frame["hasSubjects"]:
        result.extend(struct.pack("<I", len(frame["subjects"])))
        for subject in frame["subjects"]:
            result.extend(encode_reference(subject["subject"]))
            result.extend(struct.pack("<i", subject["indexInObserverVec"]))
    elif frame["subjects"]:
        raise ValueError("Subject list contradicts its presence flag")
    result.extend(struct.pack("<B", frame["hasNamedMetadata"]))
    if frame["namedMetadata"]:
        raise ValueError("Nonempty name/value metadata is unsupported")
    if frame["hasNamedMetadata"]:
        result.extend(struct.pack("<I", 0))
    return bytes(result)


def archive_member(path, name):
    data = path.read_bytes()
    with zipfile.ZipFile(path) as archive:
        entry = archive.getinfo(name)
        if entry.file_size > 100000000:
            raise ValueError("Oversized archive member")
        if entry.compress_type != 93:
            result = archive.read(entry)
        else:
            local = struct.unpack_from("<IHHHHHIIIHH", data, entry.header_offset)
            if local[0] != 0x04034B50:
                raise ValueError("Invalid ZIP local header")
            start = entry.header_offset + 30 + local[-2] + local[-1]
            compressed = data[start:start + entry.compress_size]
            library = ctypes.CDLL("/opt/homebrew/lib/libzstd.dylib")
            library.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
            library.ZSTD_decompress.restype = ctypes.c_size_t
            output = ctypes.create_string_buffer(entry.file_size)
            written = library.ZSTD_decompress(output, entry.file_size, compressed, len(compressed))
            if written != entry.file_size:
                raise ValueError("Zstandard output size mismatch")
            result = output.raw
        if len(result) != entry.file_size or zlib.crc32(result) != entry.CRC:
            raise ValueError("ZIP length or CRC mismatch")
        return result


def read_archive(path):
    prefix = "FusionAssetName[Active]/FusionDesignSegmentType1/"
    metadata = archive_member(path, prefix + "MetaStream.dat")
    bulk = archive_member(path, prefix + "BulkStream.dat")
    reader = Reader(metadata)
    kind = reader.text()
    segment_id = reader.number("I")
    reader.text(True)
    magic, version = reader.number("I"), reader.number("I")
    reader.take(8)
    repeated, namespace = reader.text(), reader.text()
    storage = reader.number("I"), reader.number("I")
    if kind != "FusionDesignSegmentType" or repeated != kind or magic != 1234 or version != 8 or storage != (1, 0):
        raise ValueError("Unsupported Design MetaStream header")
    classes = {}
    owner_classes = {}
    for code in range(256, 256 + reader.count()):
        identifier, base = reader.text(), reader.text()
        schema_version, space = reader.number("I"), reader.text()
        identities = [reader.number("Q") for _ in range(reader.count())]
        classes[code] = {"identifier": identifier, "baseIdentifier": base, "schemaVersion": schema_version, "namespace": space}
        for identity in identities:
            if identity in owner_classes:
                raise ValueError("Duplicate object ownership")
            owner_classes[identity] = code
    reader.take(8 * reader.count())
    entries = []
    for primary in (True, False):
        for _ in range(reader.count()):
            identity, offset = reader.number("Q"), reader.number("Q")
            entries.append({"identity": identity, "offset": offset, "primary": primary})
    reader.number("Q")
    reader.number("I")
    for _ in range(reader.count()):
        reader.text()
        reader.number("I")
    if reader.offset != len(metadata):
        raise ValueError("Trailing metadata")
    ordered = sorted(entries, key=lambda item: item["offset"])
    for index, entry in enumerate(ordered):
        start = entry["offset"]
        end = ordered[index + 1]["offset"] if index + 1 < len(ordered) else len(bulk)
        if not 0 <= start < end <= len(bulk):
            raise ValueError("Invalid bulk record bounds")
        record = Reader(bulk[start:end])
        code, identity = int(record.text()), record.number("Q")
        if identity != entry["identity"] or code not in classes:
            raise ValueError("Bulk record disagrees with metadata index")
        if entry["primary"] and owner_classes.get(identity) != code:
            raise ValueError("Primary record disagrees with metadata ownership")
        entry.update({"classCode": code, "class": classes[code], "payloadBulkOffset": start + record.offset, "payload": record.take(end - start - record.offset)})
    return {"metadataSha256": digest(metadata), "bulkSha256": digest(bulk), "segmentId": segment_id, "namespace": namespace, "records": ordered, "classes": classes}


def selected_sets(schema, record, records):
    identity = record["identity"]
    own_id = record["class"]["identifier"].upper()
    if not record["primary"]:
        if own_id != MANAGED_ENTITY:
            raise ValueError("Only ManagedEntity continuations are supported")
        return [schema[own_id]["member_sets"][0]]
    sets = []
    continuation_ids = {item["class"]["identifier"].upper() for item in records if item["identity"] == identity and not item["primary"]}
    for member_set in schema[own_id]["member_sets"]:
        identifier = member_set["metatype_identifier"].upper()
        if identifier in continuation_ids or identifier == ROOT_ENTITY:
            break
        if not member_set["initialized"]:
            raise ValueError("Uninitialized reflected member set")
        sets.append(member_set)
    return sets


def decode_record(record, member_sets, schema):
    reader = Reader(record["payload"])
    result = {"frame": read_frame(reader, record["primary"]), "sets": []}
    for member_set in member_sets:
        identifier = member_set["metatype_identifier"].upper()
        values = {}
        for member in sorted(member_set["members"], key=lambda value: value["name"]):
            if member["option_mask"] & 1:
                values[member["name"]] = reader.field(schema[identifier]["name"] + "." + member["name"], member["metatype"]["name"], lambda member=member: read_member(reader, member))
        result["sets"].append({"identifier": member_set["metatype_identifier"], "values": values})
    if reader.offset != len(reader.data):
        raise ValueError(f"Unexplained payload bytes: consumed {reader.offset} of {len(reader.data)}")
    return result, reader.evidence


def encode_record(value, member_sets, primary):
    if set(value) != {"frame", "sets"} or len(value["sets"]) != len(member_sets):
        raise ValueError("Record value disagrees with typed member sets")
    output = bytearray(encode_frame(value["frame"], primary))
    for values, member_set in zip(value["sets"], member_sets):
        members = sorted((member for member in member_set["members"] if member["option_mask"] & 1), key=lambda member: member["name"])
        if values["identifier"].upper() != member_set["metatype_identifier"].upper() or set(values["values"]) != {member["name"] for member in members}:
            raise ValueError("Record values disagree with reflected schema")
        for member in members:
            output.extend(encode_member(member, values["values"][member["name"]]))
    return bytes(output)


def native_value(value, reader_segment):
    if isinstance(value, list):
        return [native_value(item, reader_segment) for item in value]
    if isinstance(value, dict):
        if not value:
            return None
        if set(value) == {"segId", "entityId", "rootId"}:
            if value["segId"] != reader_segment or value["rootId"]:
                raise ValueError("Native graph contains a nonlocal reference")
            return {"entityId": value["entityId"]}
        return {key: native_value(item, reader_segment) for key, item in value.items()}
    return value


def inspect_archive(path, schema):
    archive = read_archive(path)
    native_path = path.with_suffix(".entities.json")
    native_raw = native_path.read_bytes()
    native = {item["identity"]["entityId"]: item for item in json.loads(native_raw) if "properties" in item}
    selected_ids = {record["identity"] for record in archive["records"] if record["primary"] and record["class"]["identifier"].upper() in TARGETS}
    results = []
    class_versions = {value["identifier"].upper(): value["schemaVersion"] for value in archive["classes"].values()}
    for record in archive["records"]:
        if record["identity"] not in selected_ids:
            continue
        result = {"identity": record["identity"], "primary": record["primary"], "classIdentifier": record["class"]["identifier"], "recordBulkOffset": record["offset"], "payloadBulkOffset": record["payloadBulkOffset"], "payloadLength": len(record["payload"]), "payloadSha256": digest(record["payload"])}
        try:
            sets = selected_sets(schema, record, archive["records"])
            for member_set in sets:
                identity = member_set["metatype_identifier"].upper()
                if class_versions.get(identity) != schema[identity]["version"]:
                    raise ValueError("Archive class version differs from native reflected schema")
            value, evidence = decode_record(record, sets, schema)
            encoded = encode_record(json.loads(json.dumps(value, allow_nan=False)), sets, record["primary"])
            properties = native[record["identity"]]["properties"]
            differences = []
            comparison_count = 0
            for member_set in value["sets"]:
                for name, decoded in member_set["values"].items():
                    comparison_count += 1
                    expected = native_value(properties[name], properties["segment"])
                    if decoded != expected:
                        differences.append({"member": name, "decoded": decoded, "native": expected})
            result.update({"status": "decoded", "byteIdenticalReencoding": encoded == record["payload"], "encodedSha256": digest(encoded), "semanticFieldsCompared": comparison_count, "nativeSemanticDifferences": differences, "value": value, "fields": evidence, "unexplainedBytes": 0})
        except (ValueError, KeyError, struct.error, UnicodeError) as error:
            result.update({"status": "unresolved", "reason": str(error)})
        results.append(result)
    return {"file": path.name, "archiveSha256": digest(path.read_bytes()), "metadataSha256": archive["metadataSha256"], "bulkSha256": archive["bulkSha256"], "nativeGraphPath": str(native_path.resolve()), "nativeGraphSha256": digest(native_raw), "records": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, default=Path(__file__).parents[1] / "LocalOracle" / "Features")
    parser.add_argument("--reflection", type=Path, default=Path(__file__).parents[1] / "LocalOracle" / "Reflection" / "Schema.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("ReflectedFeaturePayloads.json"))
    args = parser.parse_args()
    raw = args.reflection.read_bytes()
    reflection = json.loads(raw)
    schema = {item["identifier"].upper(): item for item in reflection["metatypes"] if item["category"] == "entity"}
    samples = [inspect_archive(args.features / name, schema) for name in ("circle_sketch.f3d", "extrude_07mm.f3d", "extrude_13mm.f3d")]
    records = [record for sample in samples for record in sample["records"]]
    output = {
        "schema": "FusionReflectedFeaturePayloads/1",
        "extractorSha256": digest(Path(__file__).read_bytes()),
        "reflectionSha256": digest(raw),
        "applicationVersion": reflection["expected_fusion_build"],
        "coverage": {"archiveCount": len(samples), "primaryRecords": sum(record["primary"] for record in records), "continuationRecords": sum(not record["primary"] for record in records), "decodedRecords": sum(record["status"] == "decoded" for record in records), "byteIdenticalRecords": sum(record.get("byteIdenticalReencoding", False) for record in records), "payloadBytes": sum(record["payloadLength"] for record in records), "semanticFieldsCompared": sum(record.get("semanticFieldsCompared", 0) for record in records), "semanticDifferences": sum(len(record.get("nativeSemanticDifferences", [])) for record in records)},
        "typedValueEvidence": [
            {"metatype": "IntrinsicMetaTypeUuid", "wireEncoding": "u32 UTF-16 code-unit count followed by canonical UUID string in UTF-16LE", "controlledObservation": "associationId consumes 76 bytes: 4-byte length 36 and 72 UTF-16LE bytes, matching native UUID text"},
            {"metatype": "AcGeVector3dValueMetaType", "wireEncoding": "three little-endian IEEE754 binary64 coordinates x, y, z", "controlledObservation": "profileNormal consumes 24 bytes at offset31 and equals the native x0,y0,z1 vector"},
        ],
        "method": "Read bounded indexed payloads, decode reflected persisted members lexically per inherited member set, JSON-serialize typed values, and independently re-encode them with no original payload or residual byte argument. Compare all decoded members against native entity properties.",
        "limitations": ["Research codec for controlled current-version sketch and extrusion records", "Only null or same-segment numeric references are supported", "Nonempty name/value metadata, unknown member types and unexplained bytes are rejected", "Continuation splitting is derived from indexed class identities", "No vendor import acceptance or complete archive writer is established"],
        "samples": samples,
    }
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    for sample in samples:
        print(sample["file"], [(row["identity"], row["primary"], row["payloadLength"], row["status"], row.get("reason"), row.get("byteIdenticalReencoding"), len(row.get("nativeSemanticDifferences", []))) for row in sample["records"]])


if __name__ == "__main__":
    main()
