import argparse
import collections
import hashlib
import json
import math
import struct
import zipfile
from pathlib import Path


TAG_NAMES = {
    2: "unsigned_byte", 3: "short", 4: "integer", 5: "float", 6: "double",
    7: "short_string", 8: "medium_string", 9: "long_string", 10: "true",
    11: "false", 12: "reference", 13: "identifier", 14: "subidentifier",
    15: "subtype_open", 16: "subtype_close", 17: "record_end", 18: "string",
    19: "position", 20: "vector3", 21: "enum", 22: "vector2", 23: "int64",
}


def read_stream(data):
    magic = data[:15]
    if magic not in (b"ASM BinaryFile4", b"ASM BinaryFile8"):
        raise ValueError("Not an admitted ASM binary stream")
    width = int(chr(magic[-1]))
    integer = "i" if width == 4 else "q"
    at = 15

    def take(size):
        nonlocal at
        if size < 0 or size > len(data) - at:
            raise ValueError(f"Truncated or oversized token at {at}")
        result = data[at:at + size]
        at += size
        return result

    words = struct.unpack("<4" + integer, take(4 * width))
    tokens = []
    while at < len(data):
        start = at
        tag = take(1)[0]
        if tag not in TAG_NAMES:
            raise ValueError(f"Unknown tag {tag} at {start}")
        if tag in (2, 3, 4, 5, 6, 12, 21, 23):
            shape = {2: "B", 3: "h", 4: integer, 5: "f", 6: "d", 12: integer, 21: integer, 23: "q"}[tag]
            value = struct.unpack("<" + shape, take(struct.calcsize(shape)))[0]
        elif tag in (7, 8, 9, 13, 14, 18):
            shape = "B" if tag in (7, 13, 14) else "H" if tag == 8 else integer
            size = struct.unpack("<" + shape, take(struct.calcsize(shape)))[0]
            value = take(size).decode("utf-8")
        elif tag in (19, 20, 22):
            count = 2 if tag == 22 else 3
            value = list(struct.unpack("<" + "d" * count, take(8 * count)))
        else:
            value = None
        numeric = value if isinstance(value, list) else [value]
        if any(isinstance(item, float) and not math.isfinite(item) for item in numeric):
            raise ValueError(f"Nonfinite value at {start}")
        tokens.append({"offset": start, "size": at - start, "tag": tag, "kind": TAG_NAMES[tag], "value": value})
    if tuple(token["tag"] for token in tokens[:6]) != (7, 7, 7, 6, 6, 6):
        raise ValueError("Invalid ASM tagged header")
    header = dict(zip(("save_format", "stored_records", "top_level_entity_count", "flags"), words))
    header.update({"magic": magic.decode("ascii"), "integer_width": width, "tagged_values": tokens[:6]})
    records = []
    record_tokens = []
    depth = 0
    for item in tokens[6:]:
        tag = item["tag"]
        if tag == 15:
            depth += 1
        elif tag == 16:
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unmatched subtype close at {item['offset']}")
        if tag == 17:
            if depth:
                raise ValueError(f"Record ended inside subtype at {item['offset']}")
            records.append(frame(record_tokens, item))
            record_tokens = []
        else:
            record_tokens.append(item)
    if record_tokens:
        final = frame(record_tokens, None)
        if final["name"] != "End-of-ASM-data" or final["fields"]:
            raise ValueError("Only the final ASM end marker may omit its record terminator")
        records.append(final)
    if depth:
        raise ValueError("Unclosed subtype")
    if not records or records[-1]["name"] != "End-of-ASM-data":
        raise ValueError("Missing ASM stream end marker")
    for index, record in enumerate(records):
        record["physical_record_index"] = index
    return {"header": header, "records": records, "tokens": tokens}


def frame(tokens, terminator):
    if not tokens:
        raise ValueError("Empty record")
    names = []
    boundary = 0
    for boundary, item in enumerate(tokens):
        if item["tag"] not in (13, 14):
            raise ValueError(f"Invalid record name at {item['offset']}")
        names.append(item["value"])
        if item["tag"] == 13:
            break
    else:
        raise ValueError("Unterminated name chain")
    boundary_marker = None
    name = "-".join(names)
    if name in ("Begin-of-ASM-History-Data", "End-of-ASM-History-Section"):
        boundary_marker = name
        names = []
        start = boundary + 1
        for boundary in range(start, len(tokens)):
            item = tokens[boundary]
            if item["tag"] not in (13, 14):
                raise ValueError(f"Invalid history payload name at {item['offset']}")
            names.append(item["value"])
            if item["tag"] == 13:
                break
        else:
            raise ValueError("History boundary has no payload name")
        name = "-".join(names)
    last = terminator or tokens[-1]
    return {
        "name": name,
        "boundary_marker": boundary_marker,
        "offset": tokens[0]["offset"],
        "size": last["offset"] + last["size"] - tokens[0]["offset"],
        "name_token_count": boundary + 1,
        "fields": tokens[boundary + 1:],
        "terminated": terminator is not None,
    }


def encode_token(tag, value, width=8):
    integer = "i" if width == 4 else "q"
    if tag in (2, 3, 4, 5, 6, 12, 21, 23):
        shape = {2: "B", 3: "h", 4: integer, 5: "f", 6: "d", 12: integer, 21: integer, 23: "q"}[tag]
        payload = struct.pack("<" + shape, value)
    elif tag in (7, 8, 9, 13, 14, 18):
        payload = value.encode("utf-8")
        shape = "B" if tag in (7, 13, 14) else "H" if tag == 8 else integer
        payload = struct.pack("<" + shape, len(payload)) + payload
    elif tag in (19, 20, 22):
        count = 2 if tag == 22 else 3
        if len(value) != count:
            raise ValueError("Wrong vector dimensions")
        payload = struct.pack("<" + "d" * count, *value)
    elif tag in (10, 11, 15, 16, 17) and value is None:
        payload = b""
    else:
        raise ValueError("Unsupported typed token")
    return bytes([tag]) + payload


def encode_stream(model):
    header = model["header"]
    width = header["integer_width"]
    integer = "i" if width == 4 else "q"
    words = [header[name] for name in ("save_format", "stored_records", "top_level_entity_count", "flags")]
    return header["magic"].encode("ascii") + struct.pack("<4" + integer, *words) + b"".join(encode_token(item["tag"], item["value"], width) for item in model["tokens"])


def describe(data, member):
    model = read_stream(data)
    encoded = encode_stream(model)
    history_index = next((index for index, row in enumerate(model["records"]) if row["boundary_marker"] == "Begin-of-ASM-History-Data"), None)
    initial = model["records"][:history_index] if history_index is not None else model["records"][:-1]
    return {
        "member": member,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "all_bytes_framed": sum(item["size"] for item in model["tokens"]) + 15 + 4 * model["header"]["integer_width"] == len(data),
        "typed_reencoding_sha256": hashlib.sha256(encoded).hexdigest(),
        "typed_reencoding_byte_identical": encoded == data,
        "reencoding_scope": "Wire framing only; reencoding source fields is not independent semantic authoring or native acceptance",
        "initial_record_count": len(initial),
        "history_record_index": history_index,
        "initial_types": dict(collections.Counter(row["name"] for row in initial)),
        "tag_counts": dict(collections.Counter(item["kind"] for item in model["tokens"])),
        **model,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.suffix.lower() == ".f3d":
        with zipfile.ZipFile(args.source) as archive:
            reports = [describe(archive.read(name), name) for name in archive.namelist() if name.endswith((".smb", ".smbh"))]
    else:
        reports = [describe(args.source.read_bytes(), args.source.name)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"source": str(args.source), "streams": reports}, indent=2) + "\n")
    for report in reports:
        print(json.dumps({key: report[key] for key in ("member", "bytes", "all_bytes_framed", "typed_reencoding_byte_identical", "initial_record_count", "history_record_index", "initial_types")}, indent=2))


if __name__ == "__main__":
    main()
