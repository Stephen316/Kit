import argparse
import collections
import hashlib
import io
import json
import re
import runpy
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


sys.dont_write_bytecode = True
RESEARCH = Path(__file__).resolve().parents[1]
GRAPH = runpy.run_path(str(RESEARCH / "EntityGraph" / "DecodeGraph.py"))
PROTEIN = runpy.run_path(str(Path(__file__).with_name("ReadProtein.py")))
TOOLS = GRAPH["TOOLS"]
Reader = TOOLS["Reader"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest(data, root):
    reader = Reader(data)
    fields = {}

    def item(name, kind, callback):
        fields[name] = reader.field(name, kind, callback)
        return fields[name]

    text = lambda name, wide=False: item(name, "utf16le" if wide else "ascii", lambda: reader.text(wide))
    word = lambda name: item(name, "u32", lambda: reader.number("I"))
    byte = lambda name: item(name, "u8", lambda: reader.number("B"))
    if root:
        text("format")
        text("document_type")
        for name in ("extension", "title", "description", "document_id_a", "document_id_b"):
            text(name, True)
        word("magic")
        word("schema_version")
        word("header_word_a")
        word("header_word_b")
    else:
        for name in ("asset_name", "asset_id", "snapshot_id"):
            text(name, True)
        text("asset_type")
        word("schema_version")
    for index in range(word("version_count")):
        text(f"versions[{index}].key")
        word(f"versions[{index}].value")
    if root:
        word("asset_header_word")
        byte("asset_header_flag")
        text("active_asset_id", True)
        for index in range(word("asset_count")):
            text(f"assets[{index}].name", True)
            word(f"assets[{index}].word")
            byte(f"assets[{index}].active")
            text(f"assets[{index}].export_label", True)
    else:
        text("asset_kind")
        word("property_header_word")
        byte("property_header_flag")
        for index in range(word("property_count")):
            text(f"properties[{index}].key")
            text(f"properties[{index}].value", True)
        word("segment_header_word")
        word("segment_opaque_word")
        for index in range(word("segment_count")):
            word(f"segments[{index}].id")
            text(f"segments[{index}].type")
            text(f"segments[{index}].storage_name")
    return {"values": fields, "fields": reader.evidence, "consumed_bytes": reader.offset, "unresolved_bytes": len(data) - reader.offset}


def segment(meta, bulk):
    reader = Reader(meta)
    header = {"kind": reader.text(), "segment_id": reader.number("I"), "namespace": reader.text(True), "magic": reader.number("I"), "version": reader.number("I"), "header_words": [reader.number("I"), reader.number("I")], "repeated_kind": reader.text(), "storage_space": reader.text(), "storage_words": [reader.number("I"), reader.number("I")]}
    classes = {}
    for code in range(256, 256 + reader.count()):
        row = {"identifier": reader.text(), "baseIdentifier": reader.text(), "schemaVersion": reader.number("I"), "namespace": reader.text()}
        row["owner_ids"] = [reader.number("Q") for _ in range(reader.count())]
        classes[code] = row
    additional_ids = [reader.number("Q") for _ in range(reader.count())]
    entries = []
    tables = []
    for primary in (True, False):
        table = [{"identity": reader.number("Q"), "offset": reader.number("Q"), "primary": primary} for _ in range(reader.count())]
        entries.extend(table)
        tables.append(table)
    tail = {"long": reader.number("Q"), "word": reader.number("I"), "properties": [{"name": reader.text(), "value": reader.number("I")} for _ in range(reader.count())]}
    codec = GRAPH["GraphCodec"]({"classes": classes})
    ordered = sorted(entries, key=lambda row: row["offset"])
    records = []
    for index, row in enumerate(ordered):
        start = row["offset"]
        end = ordered[index + 1]["offset"] if index + 1 < len(ordered) else len(bulk)
        cursor = Reader(bulk[start:end])
        code, identity = int(cursor.text()), cursor.number("Q")
        payload = cursor.take(end - start - cursor.offset)
        records.append({**row, "class_code": code, "class": classes[code], "physical_identity": identity, "payload_offset": end - len(payload), "payload_size": len(payload), "payload_sha256": sha(payload), "payload": payload})
    for record in records:
        payload = record.pop("payload")
        cursor = Reader(payload)
        identity = record["class"]["identifier"]
        record["class_name"] = codec.schema.get(identity.upper(), {}).get("name")
        try:
            stops = {other["class"]["identifier"].upper() for other in records if other["identity"] == record["identity"] and not other["primary"] and other is not record}
            groups = codec.groups(identity, stops)
            record["value"] = {"frame": codec.read_frame(cursor, record["primary"]), "groups": codec.read_groups(cursor, groups)}
            record["status"] = "decoded" if cursor.offset == len(payload) else "partial"
        except (ValueError, KeyError, UnicodeError, struct.error) as error:
            record["status"] = "unresolved"
            record["error"] = str(error)
        record["decoded_fields"] = cursor.evidence
        record["consumed_bytes"] = cursor.offset
        record["unresolved_bytes"] = len(payload) - cursor.offset
        if record["unresolved_bytes"]:
            record["remaining_prefix_hex"] = payload[cursor.offset:cursor.offset + 32].hex()
    return {"header": header, "classes": classes, "additional_ids": additional_ids, "primary_index": tables[0], "continuation_index": tables[1], "tail": tail, "metadata_unresolved_bytes": len(meta) - reader.offset, "records": records, "status_counts": dict(collections.Counter(record["status"] for record in records))}


def xml_value(node):
    return {"tag": node.tag, "attributes": node.attrib, "text": node.text, "tail": node.tail, "children": [xml_value(child) for child in node]}


def protein(data):
    records = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            payload = archive.read(entry)
            row = {"name": entry.filename, "size": len(payload), "sha256": sha(payload), "compression": entry.compress_type}
            if entry.filename.endswith(".xml"):
                row.update({"format": "xml", "tree": xml_value(ET.fromstring(payload)), "unresolved_bytes": 0, "semantic_status": "xml syntax decoded; material schema meanings require separate modeling"})
            elif entry.filename.endswith("StreamVersionTable"):
                row.update({"format": "ascii version table", "value": payload.decode("ascii"), "unresolved_bytes": 0})
            elif entry.filename.endswith("AssetTableOfContents.bin"):
                row.update({"format": "material table of contents", "decoded": PROTEIN["table"](payload)})
            elif entry.filename.endswith("Properties.bin"):
                row.update({"format": "material linked property block stream", "decoded": PROTEIN["block_stream"](payload, entry.filename.endswith("DefinitionIteratorProperties.bin"))})
            else:
                row.update({"format": "material property binary", "unresolved_bytes": len(payload), "prefix_hex": payload[:32].hex()})
            records.append(row)
    return records


def png(data):
    offset = 8
    chunks = []
    while offset < len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8].decode("ascii")
        payload = data[offset + 8:offset + 8 + size]
        row = {"kind": kind, "offset": offset, "size": size}
        if kind == "IHDR":
            row["fields"] = dict(zip(("width", "height", "bit_depth", "color_type", "compression", "filter", "interlace"), struct.unpack(">IIBBBBB", payload)))
        chunks.append(row)
        offset += 12 + size
    return {"format": "png", "chunks": chunks, "role": "preview raster; generate from authored geometry or prove optional omission"}


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
    members = []
    segments = {}
    for entry in entries:
        name = entry.filename
        row = {"name": name, "size": entry.file_size, "compression": entry.compress_type, "directory": entry.is_dir()}
        if entry.is_dir():
            row["recipe"] = "ZIP directory entry; no member payload"
        elif "FusionDesignSegmentType" in name or name.endswith((".smb", ".smbh")):
            row["scope"] = "Design or BRep; separate research ownership"
        else:
            data = TOOLS["archive_member"](path, name)
            row["sha256"] = sha(data)
            if name.endswith("Manifest.dat"):
                row["decoded"] = manifest(data, name == "Manifest.dat")
            elif name == "Properties.dat":
                reader = Reader(data)
                row["decoded"] = {"json_text": reader.text(), "unresolved_bytes": len(data) - reader.offset}
            elif "SegmentType" in name:
                prefix = name.rsplit("/", 1)[0]
                segments.setdefault(prefix, {})[name.rsplit("/", 1)[1]] = data
                row["format"] = "indexed native segment"
            elif name.endswith(".protein"):
                row["nested_members"] = protein(data)
            elif name.endswith((".dsgcfg", ".dsgcfgrule")):
                row["decoded"] = {"json": json.loads(data), "unresolved_bytes": 0}
            elif name.endswith(".png"):
                row["decoded"] = png(data)
            elif name.endswith("/world"):
                reader = Reader(data)
                row["decoded_prefix"] = {"render_list": reader.text(True), "version": reader.number("I"), "root_count": reader.number("I"), "root_class": reader.text(True), "root_handle": reader.text(True), "word_after_root_handle": reader.number("I")}
                row["unresolved_bytes"] = len(data) - reader.offset
                row["format"] = "OGS typed scene graph and attribute registry; no protobuf evidence"
            elif "/stream_mesh_" in name:
                row["format"] = "OGS packed vertex/index buffers with layout supplied by world"
                row["unresolved_bytes"] = len(data)
            else:
                row["format"] = "unresolved"
                row["unresolved_bytes"] = len(data)
        members.append(row)
    return {"archive": str(path), "sha256": sha(path.read_bytes()), "members": members, "segments": {name: segment(streams["MetaStream.dat"], streams["BulkStream.dat"]) for name, streams in segments.items()}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("archives", nargs="+", type=Path)
    arguments = parser.parse_args()
    report = {"scope": "Read-only corpus interpretation; no native CAD calls, production code execution, reencoding comparison or local tests", "samples": [inspect(path) for path in arguments.archives]}
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    for sample in report["samples"]:
        print(sample["archive"], {name: value["status_counts"] for name, value in sample["segments"].items()})


if __name__ == "__main__":
    main()
