import hashlib
import json
import lzma
import math
import struct
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


class Cursor:
    def __init__(self, payload):
        self.payload = payload
        self.offset = 0

    def take(self, size):
        end = self.offset + size
        if size < 0 or end > len(self.payload):
            raise ValueError("Truncated research input")
        result = self.payload[self.offset:end]
        self.offset = end
        return result

    def integer(self, size, order="little", signed=False):
        return int.from_bytes(self.take(size), order, signed=signed)

    def varint(self):
        result = 0
        for shift in range(0, 70, 7):
            value = self.integer(1)
            result |= (value & 127) << shift
            if value < 128:
                return result
        raise ValueError("Oversized protobuf varint")

    def remaining(self):
        return len(self.payload) - self.offset


def messagepack(cursor):
    code = cursor.integer(1)
    if code < 128:
        return code
    if code >= 224:
        return code - 256
    if code in (194, 195):
        return code == 195
    if 160 <= code <= 191:
        return cursor.take(code - 160).decode("utf-8")
    if code in (217, 218, 219):
        return cursor.take(cursor.integer({217: 1, 218: 2, 219: 4}[code], "big")).decode("utf-8")
    if 144 <= code <= 159 or code in (220, 221):
        count = code - 144 if code < 160 else cursor.integer(2 if code == 220 else 4, "big")
        return [messagepack(cursor) for _ in range(count)]
    if 128 <= code <= 143 or code in (222, 223):
        count = code - 128 if code < 144 else cursor.integer(2 if code == 222 else 4, "big")
        result = {}
        for _ in range(count):
            key = messagepack(cursor)
            if not isinstance(key, str):
                raise ValueError("Non-string MessagePack key")
            if key in result:
                raise ValueError("Duplicate MessagePack key")
            result[key] = messagepack(cursor)
        return result
    sizes = {204: 1, 205: 2, 206: 4, 207: 8, 208: 1, 209: 2, 210: 4, 211: 8}
    if code in sizes:
        return cursor.integer(sizes[code], "big", code >= 208)
    raise ValueError(f"Unmapped MessagePack code {code}")


def unpack_messagepack(payload):
    cursor = Cursor(payload)
    result = messagepack(cursor)
    if cursor.remaining():
        raise ValueError("Trailing MessagePack bytes")
    return result


def protobuf(payload):
    cursor = Cursor(payload)
    result = []
    while cursor.remaining():
        key = cursor.varint()
        field, wire = key >> 3, key & 7
        if wire == 0:
            value = cursor.varint()
        elif wire == 2:
            value = cursor.take(cursor.varint())
        else:
            raise ValueError(f"Unmapped protobuf wire {wire}")
        result.append((field, value))
    return result


def registry(payload):
    fields = protobuf(payload)
    result = {"channels": [], "properties": [], "feature_edges": []}
    roles = {9: "face_group_count", 12: "mesh_uuid", 21: "vertices", 22: "triangles"}
    for number, value in fields:
        if number in roles:
            result[roles[number]] = value.decode() if isinstance(value, bytes) else value
        elif number in (4, 5):
            channel = {"domain": "vertex_or_corner" if number == 4 else "triangle", "groups": []}
            for key, part in protobuf(value):
                if key == 2:
                    channel["role"] = part
                elif key == 3:
                    channel["resource_guid"] = part.decode()
                elif key == 5:
                    names = {1: "element_code", 2: "values", 3: "index"}
                    channel["streams"] = {names[k]: v.decode() if isinstance(v, bytes) else v for k, v in protobuf(part)}
                elif key == 6:
                    names = {1: "key", 2: "guid"}
                    channel["groups"].append({names[k]: v.decode() if isinstance(v, bytes) else v for k, v in protobuf(part)})
                else:
                    raise ValueError(f"Unmapped channel field {key}")
            result["channels"].append(channel)
        elif number == 7:
            result["feature_edges"].append({str(k): v.decode() if isinstance(v, bytes) else v for k, v in protobuf(value)})
        elif number == 8:
            names = {1: "key", 3: "text", 4: "stream"}
            result["properties"].append({names[k]: v.decode() for k, v in protobuf(value)})
        else:
            raise ValueError(f"Unmapped registry field {number}")
    return result


def stream(body):
    cursor = Cursor(body)
    descriptor = unpack_messagepack(cursor.take(cursor.integer(2)))
    if "S" in descriptor:
        children = [stream(cursor.take(size)) for size in descriptor["S"]]
        lengths = {len(data) for _, data in children}
        if len(lengths) != 1 or any(desc["descriptor"] != {"T": 3} for desc, _ in children):
            raise ValueError("Mismatched split components")
        count = lengths.pop()
        payload = b"".join(data[index:index + 4] for index in range(0, count, 4) for _, data in children)
        detail = {"descriptor": descriptor, "components": [desc for desc, _ in children]}
    else:
        declared = cursor.integer(4)
        if declared > 64 * 1024 * 1024:
            raise ValueError("Research stream exceeds bound")
        mode = cursor.take(2)
        encoded = cursor.take(cursor.remaining())
        if mode == b"\x5d\xfe":
            payload = encoded
        elif mode == b"\x5d\x14":
            header = b"\x5d" + max(1 << 20, declared).to_bytes(4, "little") + declared.to_bytes(8, "little")
            decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
            payload = decoder.decompress(header + encoded, max_length=declared + 1)
            if not decoder.eof or decoder.unused_data:
                raise ValueError("LZMA known-length stream did not terminate exactly")
        else:
            raise ValueError(f"Unmapped compression {mode.hex()}")
        if len(payload) != declared:
            raise ValueError(f"Decoded length {len(payload)} differs from {declared}")
        detail = {"descriptor": descriptor, "encoding": mode.hex(), "declared_bytes": declared}
    if cursor.remaining():
        raise ValueError("Trailing stream bytes")
    detail.update({"decoded_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    return detail, payload


def terminal_values(payload):
    words = [item[0] for item in struct.iter_unpack("<I", payload)]
    if not words:
        return []
    deltas = [value if value < 1 << 31 else value - (1 << 32) for value in words[:-1]]
    values = [words[-1] - sum(deltas)]
    for delta in deltas:
        values.append(values[-1] + delta)
    if any(value < 0 or value > (1 << 32) - 1 for value in values):
        raise ValueError("Terminal-delta value is outside uint32")
    return values


def attributes(metadata, by_name, points, corners):
    result = []
    for channel in metadata["channels"]:
        names = channel["streams"]
        code = names["element_code"]
        payload = by_name[names["values"]]
        detail = {"domain": channel["domain"], "element_code": code, "stream": names["values"]}
        if code == 5:
            values = list(struct.iter_unpack("<ff", payload))
            if not all(math.isfinite(value) and -1 <= value <= 1 for pair in values for value in pair):
                raise ValueError("Invalid octahedral direction")
            positions = terminal_values(by_name[names["index"]]) if "index" in names else []
            if len(values) != len(points) + len(positions) or positions != sorted(set(positions)) or any(index >= len(corners) for index in positions):
                raise ValueError("Normal corner-override addressing disagrees")
            detail.update({"normal_values": len(values), "corner_overrides": len(positions), "corner_normals": len(corners)})
        elif code == 7:
            values = terminal_values(payload)
            keys = {group["key"] for group in channel["groups"]}
            if len(values) != len(corners) // 3 or not set(values).issubset(keys):
                raise ValueError("Face-group selections disagree")
            detail.update({"triangle_values": len(values), "groups": len(keys), "membership_counts": dict(Counter(values))})
        else:
            raise ValueError(f"Unmapped attribute element {code}")
        result.append(detail)
    feature_count = 0
    triangle_edges = set()
    for offset in range(0, len(corners), 3):
        a, b, c = corners[offset:offset + 3]
        triangle_edges.update(tuple(sorted(pair)) for pair in ((a, b), (b, c), (c, a)))
    for entry in metadata["feature_edges"]:
        values = terminal_values(by_name[entry["4"]])
        if len(values) % 2:
            raise ValueError("Incomplete feature-edge pair")
        pairs = list(zip(values[::2], values[1::2]))
        if len(set(pairs)) != len(pairs) or any(a >= b or (a, b) not in triangle_edges for a, b in pairs):
            raise ValueError("Feature-edge relation disagrees with topology")
        feature_count += len(pairs)
    return {"channels": result, "feature_edges": feature_count}


def inspect(payload):
    cursor = Cursor(payload)
    if cursor.take(12) != b"\x89UDPMESH\r\n\x1a\n" or cursor.integer(4) != 2 or any(cursor.take(32)):
        raise ValueError("Unqualified mesh envelope")
    count = cursor.integer(8)
    if cursor.integer(4) != 1:
        raise ValueError("Unqualified registry chunk")
    metadata = registry(cursor.take(count))
    chunks = []
    table = None
    streams = []
    while cursor.remaining():
        offset = cursor.offset
        size = cursor.integer(8)
        kind = cursor.integer(4)
        body = cursor.take(size)
        if kind == 3 and table is None:
            table = unpack_messagepack(body)
        elif kind == 4 and table is not None:
            detail, data = stream(body)
            chunks.append({"offset": offset, "encoded_bytes": size, **detail})
            streams.append(data)
        else:
            raise ValueError("Unexpected mesh chunk ordering")
    names = sorted(table, key=table.get)
    if len(names) != len(streams):
        raise ValueError("Stream count disagrees with name table")
    by_name = dict(zip(names, streams, strict=True))
    for name, chunk in zip(names, chunks, strict=True):
        chunk["name"] = name
    points = list(struct.iter_unpack("<fff", by_name[metadata["vertices"]]))
    if not all(math.isfinite(value) for point in points for value in point):
        raise ValueError("Nonfinite mesh coordinate")
    deltas = [row[0] for row in struct.iter_unpack("<i", by_name[metadata["triangles"]])]
    if not deltas or len(deltas) % 3:
        raise ValueError("Triangle stream does not have complete triples")
    positions = [0]
    for delta in deltas[:-1]:
        positions.append(positions[-1] + delta)
    initial = -min(positions)
    if initial != len(points) - 1 - max(positions):
        raise ValueError("Ambiguous implicit first corner")
    corners = [value + initial for value in positions]
    return {"registry": metadata, "name_table": table, "streams": chunks, "vertices": len(points), "triangles": len(corners) // 3, "attributes": attributes(metadata, by_name, points, corners), "first_corner": initial, "terminal_corner_word": deltas[-1], "container_bounds": [[min(p[axis] for p in points) for axis in range(3)], [max(p[axis] for p in points) for axis in range(3)]], "consumed_bytes": cursor.offset}


inventory = json.loads((ROOT / "CorpusInventory.json").read_text())
report = {"scope": "Read-only mesh container field and stream inspection; no product execution, native acceptance or test invocation", "upstream": "https://github.com/cadmpeg/cadmpeg/tree/de2726870ff728352163f601ab4e60bbd54fbade", "attribution": "Wire-model comparison with cadmpeg, Apache-2.0 code and CC-BY-4.0 specifications; independently written Python research inspector", "containers": [], "failures": []}
for row in inventory["archives"]:
    with zipfile.ZipFile(REPO / row["archive"]) as archive:
        for member in row["members"]:
            payload = archive.read(member["name"])
            identity = {"archive": row["archive"], "member": member["name"], "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            try:
                report["containers"].append({**identity, **inspect(payload)})
            except Exception as error:
                report["failures"].append({**identity, "error": str(error)})
report["summary"] = {"decoded": len(report["containers"]), "failures": len(report["failures"]), "encoded_bytes": sum(row["bytes"] for row in report["containers"]), "vertices": sum(row["vertices"] for row in report["containers"]), "triangles": sum(row["triangles"] for row in report["containers"]), "stream_descriptors": dict(Counter(json.dumps(stream["descriptor"], sort_keys=True) for row in report["containers"] for stream in row["streams"]))}
details = lzma.compress((json.dumps(report, indent=2) + "\n").encode())
(ROOT / "ContainerFields.json.xz").write_bytes(details)
index = {key: report[key] for key in ("scope", "upstream", "attribution", "summary", "failures")}
index["details"] = {"file": "ContainerFields.json.xz", "sha256": hashlib.sha256(details).hexdigest(), "encoding": "xz-compressed UTF-8 JSON"}
index["containers"] = [{key: row[key] for key in ("archive", "member", "bytes", "sha256", "vertices", "triangles", "consumed_bytes")} for row in report["containers"]]
(ROOT / "ContainerFields.json").write_text(json.dumps(index, indent=2) + "\n")
print(json.dumps(report["summary"], indent=2))
print(json.dumps(report["failures"][:3], indent=2))
