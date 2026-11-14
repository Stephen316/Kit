import math
import struct


DEPRECATED = {"texture_MapChannel", "unifiedbitmap_MapChannel"}


def schema_members(name, schemas, seen=()):
    if name in seen:
        raise ValueError("Cyclic material schema inheritance")
    result = {}
    for base in schemas[name].findall("Base"):
        result.update(schema_members(base.attrib["val"], schemas, (*seen, name)))
    for member in schemas[name]:
        if "id" in member.attrib:
            result[member.attrib["id"]] = {"kind": member.tag, "attributes": member.attrib}
    return result


def text(value):
    if type(value) is not str:
        raise ValueError("Material text must be a string")
    data = value.encode("utf-8")
    return struct.pack("<I", len(data)) + data


def boolean(value):
    if type(value) is not bool:
        raise ValueError("Material flag must be a bool")
    return bytes((value,))


def floating(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Material scalar must be finite")
    return struct.pack("<d", value)


def encode_value(value, spec):
    kind = spec["kind"]
    attrs = spec["attributes"]
    if attrs.get("allowmultiplevalues") == "true":
        if type(value) is not list:
            raise ValueError("Material list must be a list")
        child = {**spec, "attributes": {key: value for key, value in attrs.items() if key != "allowmultiplevalues"}}
        return struct.pack("<I", len(value)) + b"".join(encode_value(item, child) for item in value)
    if kind in ("String", "URL", "Uuid"):
        return text(value)
    if kind in ("Integer", "Choice"):
        if type(value) is not int:
            raise ValueError("Material integer must be an int")
        return struct.pack("<i", value)
    if kind == "Boolean":
        return boolean(value)
    if kind == "Float":
        if "unit" in attrs:
            if type(value) is not dict or set(value) != {"unit_code", "value"} or type(value["unit_code"]) is not int:
                raise ValueError("Unit scalar requires unit_code and value")
            return struct.pack("<i", value["unit_code"]) + floating(value["value"])
        return floating(value)
    if kind == "Color":
        if type(value) is not list or len(value) != 4:
            raise ValueError("Material color requires RGBA")
        return b"".join(floating(item) for item in value)
    if kind == "Reference":
        if value is not None:
            raise ValueError("Reference values are represented by connections")
        return b""
    raise ValueError("Unsupported material value " + kind)


def encode_connections(value):
    if type(value) is not dict or "present" not in value:
        raise ValueError("Connections require a presence flag")
    result = boolean(value["present"])
    if not value["present"]:
        if set(value) != {"present"}:
            raise ValueError("Absent connections cannot carry other fields")
        return result
    if set(value) != {"present", "enabled", "assets"} or type(value["assets"]) is not list or not value["assets"]:
        raise ValueError("Present connections require enabled and a nonempty asset list")
    return result + boolean(value["enabled"]) + struct.pack("<I", len(value["assets"])) + b"".join(text(item) for item in value["assets"])


def encode_properties(schema, schemas, fields, definitions):
    members = schema_members(schema, schemas)
    selected = {}
    for name, spec in sorted(members.items()):
        attrs = spec["attributes"]
        selected_kind = attrs.get("definitionIteratorData") == "true"
        if selected_kind == definitions and (definitions or (attrs.get("readonly") != "true" and name not in DEPRECATED)):
            selected[name] = spec
    values = {field["name"]: field for field in fields}
    if len(values) != len(fields) or values.keys() != selected.keys():
        raise ValueError("Material field names do not match the selected schema group")
    result = bytearray()
    for name, spec in selected.items():
        field = values[name]
        result.extend(encode_value(field["value"], spec))
        if not definitions and spec["attributes"].get("allowconnectedassets") in ("single", "multiple"):
            result.extend(encode_connections(field["connections"]))
        elif "connections" in field:
            raise ValueError("Property schema does not permit connections")
    return bytes(result)


def encode_instance(material, schemas):
    header = b"".join(text(material[key]) for key in ("schema", "instance_id", "definition_id"))
    return header + encode_properties(material["schema"], schemas, material["properties"], False)


def encode_definition(material, schemas):
    return encode_properties(material["schema"], schemas, material["definition_properties"], True)


def encode_store(payloads):
    result = bytearray(struct.pack("<IIII", 136, 0xffffffff, 0xffffffff, 0))
    roots = []
    block_index = 0
    for payload in payloads:
        if not payload:
            raise ValueError("Material record must not be empty")
        roots.append(block_index)
        for start in range(0, len(payload), 128):
            chunk = payload[start:start + 128]
            next_index = block_index + 1 if start + 128 < len(payload) else 0xffffffff
            result.extend(struct.pack("<IHH", next_index, len(chunk), int(start == 0)))
            result.extend(chunk)
            result.extend(bytes(128 - len(chunk)))
            block_index += 1
    return bytes(result), roots


def encode_material_data(materials, schemas):
    identities = {item["instance_id"] for item in materials}
    if len(identities) != len(materials):
        raise ValueError("Duplicate material instance ID")
    for material in materials:
        for field in material["properties"]:
            for identity in field.get("connections", {}).get("assets", []):
                if identity not in identities:
                    raise ValueError("Material connection target is missing")
    definitions, definition_roots = encode_store([encode_definition(item, schemas) for item in materials])
    instances, instance_roots = encode_store([encode_instance(item, schemas) for item in materials])
    toc = bytearray()
    for material, definition_root, instance_root in zip(materials, definition_roots, instance_roots):
        toc.extend(text(material["instance_id"]))
        toc.extend(text(material["role"]))
        toc.extend(struct.pack("<II", definition_root, instance_root))
        toc.extend(text(material["schema"]))
    return {"DefinitionIteratorProperties.bin": definitions, "InstanceProperties.bin": instances, "AssetTableOfContents.bin": bytes(toc)}
