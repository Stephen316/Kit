import argparse
import hashlib
import io
import json
import runpy
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parents[1]
TOOLS = runpy.run_path(str(BASE / "ReflectedFeatures.py"))
PROTEIN = runpy.run_path(str(BASE / "DocumentEnvelope" / "ReadProtein.py"))
Reader = PROTEIN["Reader"]
DEPRECATED = {"texture_MapChannel", "unifiedbitmap_MapChannel"}


def schema_members(name, schemas, seen=()):
    if name in seen:
        raise ValueError("Cyclic material schema inheritance")
    node = schemas[name]
    result = {}
    for base in node.findall("Base"):
        result.update(schema_members(base.attrib["val"], schemas, (*seen, name)))
    for member in node:
        if "id" in member.attrib:
            result[member.attrib["id"]] = {"kind": member.tag, "attributes": member.attrib, "declaring_schema": name, "choices": [value.attrib for value in member if value.tag == "ChoiceValue"]}
    return result


def read_value(reader, spec):
    kind = spec["kind"]
    if spec["attributes"].get("allowmultiplevalues") == "true":
        child = {**spec, "attributes": {key: value for key, value in spec["attributes"].items() if key != "allowmultiplevalues"}}
        count = reader.number("I")
        if count > 10000:
            raise ValueError("Material value count exceeds research limit")
        return [read_value(reader, child) for _ in range(count)]
    if kind in ("String", "URL", "Uuid"):
        return reader.text()
    if kind in ("Integer", "Choice"):
        return reader.number("i")
    if kind == "Boolean":
        value = reader.number("B")
        if value not in (0, 1):
            raise ValueError("Invalid material boolean")
        return bool(value)
    if kind == "Float":
        if "unit" in spec["attributes"]:
            return {"unit_code": reader.number("i"), "value": reader.number("d")}
        return reader.number("d")
    if kind == "Color":
        return [reader.number("d") for _ in range(4)]
    if kind == "Reference":
        return None
    raise ValueError("Unsupported material value " + kind)


def decode_record(data, schemas):
    reader = Reader(data)
    header = {key: reader.text() for key in ("schema", "instance_id", "definition_id")}
    members = schema_members(header["schema"], schemas)
    fields = []
    skipped = []
    error = None
    for name, spec in sorted(members.items()):
        attrs = spec["attributes"]
        if attrs.get("readonly") == "true" or attrs.get("definitionIteratorData") == "true" or name in DEPRECATED:
            skipped.append(name)
            continue
        field = {"name": name, "schema": spec["declaring_schema"], "type": spec["kind"], "offset": reader.offset}
        if "unit" in attrs:
            field["schema_unit"] = attrs["unit"]
        fields.append(field)
        try:
            field["value"] = read_value(reader, spec)
            if attrs.get("allowconnectedassets") in ("single", "multiple"):
                present = reader.number("B")
                if present not in (0, 1):
                    raise ValueError("Invalid connection presence flag")
                connections = {"present": bool(present)}
                if present:
                    enabled = reader.number("B")
                    if enabled not in (0, 1):
                        raise ValueError("Invalid connection enabled flag")
                    connections["enabled"] = bool(enabled)
                    connections["assets"] = reader.strings()
                field["connections"] = connections
            field["end_offset"] = reader.offset
        except (ValueError, UnicodeError, struct.error) as failure:
            error = str(failure)
            break
    return {"header": header, "fields": fields, "schema_omitted_fields": skipped, "error": error, "consumed_bytes": reader.offset, "total_bytes": len(data), "unresolved_bytes": len(data) - reader.offset}


def decode_definition(data, schema, schemas):
    reader = Reader(data)
    fields = []
    for name, spec in sorted(schema_members(schema, schemas).items()):
        if spec["attributes"].get("definitionIteratorData") != "true":
            continue
        start = reader.offset
        value = read_value(reader, spec)
        fields.append({"name": name, "schema": spec["declaring_schema"], "type": spec["kind"], "offset": start, "value": value, "end_offset": reader.offset})
    return {"schema": schema, "fields": fields, "consumed_bytes": reader.offset, "total_bytes": len(data), "unresolved_bytes": len(data) - reader.offset}


def read_chain(data, root):
    size = struct.unpack_from("<I", data)[0]
    chunks, block_ids, index = [], [], root
    while index != 0xffffffff:
        if index in block_ids or 16 + (index + 1) * size > len(data):
            raise ValueError("Invalid property block chain")
        block_ids.append(index)
        start = 16 + index * size
        index, used, flags = struct.unpack_from("<IHH", data, start)
        if used > size - 8:
            raise ValueError("Invalid property block length")
        chunks.append(data[start + 8:start + 8 + used])
    return b"".join(chunks), block_ids


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        name = next(name for name in archive.namelist() if name.endswith(".protein"))
    data = TOOLS["archive_member"](path, name)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        candidates = {Path(name).stem: ET.fromstring(archive.read(name)) for name in archive.namelist() if "/Schemas/" in name and name.endswith(".xml")}
        schemas = {name: value for name, value in candidates.items() if value.tag == "AssetSchema"}
        instance_name = next(name for name in archive.namelist() if name.endswith("InstanceProperties.bin"))
        instances = archive.read(instance_name)
        definitions = archive.read(next(name for name in archive.namelist() if name.endswith("DefinitionIteratorProperties.bin")))
        toc = PROTEIN["table"](archive.read(next(name for name in archive.namelist() if name.endswith("AssetTableOfContents.bin"))))["records"]
    records = []
    for item in toc:
        payload, block_ids = read_chain(instances, item["instance_root"])
        definition, definition_blocks = read_chain(definitions, item["definition_root"])
        records.append({"toc": item, "blocks": block_ids, "sha256": hashlib.sha256(payload).hexdigest(), "definition_blocks": definition_blocks, "definition_sha256": hashlib.sha256(definition).hexdigest(), "definition": decode_definition(definition, item["schema"], schemas), "decoded": decode_record(payload, schemas)})
    return {"archive": str(path), "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "protein_member": name, "records": records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args()
    report = {"scope": "Read-only schema-guided material instance interpretation; no native calls or tests", "samples": [inspect(path) for path in args.archives]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    for sample in report["samples"]:
        print(sample["archive"])
        for record in sample["records"]:
            row = record["decoded"]
            print(row["header"]["schema"], row["consumed_bytes"], row["total_bytes"], row["error"])


if __name__ == "__main__":
    main()
