"""Bounded token inspection for the observed ASM BinaryFile8 body blobs.

Tag meanings referenced from ezdxf's MIT-licensed ACIS tag documentation:
https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/const.py
The 64-bit integer/header interpretation is observed in local Fusion samples.
This is a token reader, not a geometry kernel or complete entity schema.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct


class AsmReader:
    def __init__(self, data):
        self.data, self.cursor = data, 0

    def take(self, count):
        if count < 0 or self.cursor+count > len(self.data):
            raise ValueError("Truncated ASM payload at "+str(self.cursor))
        result = self.data[self.cursor:self.cursor+count]
        self.cursor += count
        return result

    def number(self, format):
        return struct.unpack("<"+format, self.take(struct.calcsize("<"+format)))[0]

    def string(self, size):
        if not 0 <= size <= 1048576:
            raise ValueError("ASM string exceeds the supported limit")
        return self.take(size).decode("utf-8")

    def token(self):
        start, tag = self.cursor, self.number("B")
        if tag in (4, 12, 21):
            kind, value = {4: "integer", 12: "pointer", 21: "enum"}[tag], self.number("q")
        elif tag in (6, 23):
            kind, value = ("double" if tag == 6 else "uninterpreted_double"), self.number("d")
            if not math.isfinite(value):
                raise ValueError("Non-finite ASM numeric token")
        elif tag in (7, 13, 14, 18):
            kind = {7: "string", 13: "entity_name", 14: "entity_name_prefix", 18: "literal_string"}[tag]
            value = self.string(self.number("q" if tag == 18 else "B"))
        elif tag in (10, 11):
            kind, value = "boolean_token", tag == 10
        elif tag in (19, 20):
            kind = "position_vector" if tag == 19 else "direction_vector"
            value = list(struct.unpack("<3d", self.take(24)))
            if not all(math.isfinite(v) for v in value):
                raise ValueError("Non-finite ASM vector")
        elif tag in (15, 16, 17):
            kind, value = {15: "subtype_start", 16: "subtype_end", 17: "record_end"}[tag], None
        else:
            raise ValueError("Unsupported ASM token 0x%02x at %d" % (tag, start))
        return {"tag": tag, "kind": kind, "value": value, "offset": start}


def inspect_asm(data):
    reader = AsmReader(data)
    if reader.take(15) != b"ASM BinaryFile8":
        raise ValueError("Unsupported ASM signature")
    version, stored_records, stored_entities, flags = [reader.number("q") for _ in range(4)]
    strings = [reader.token() for _ in range(3)]
    quantities = [reader.token() for _ in range(3)]
    if any(t["tag"] != 7 for t in strings) or any(t["tag"] != 6 for t in quantities):
        raise ValueError("Unsupported ASM tagged header")
    header = {"signature": "ASM BinaryFile8", "version": version,
              "stored_record_count": stored_records, "stored_entity_count": stored_entities,
              "stored_flags": flags, "product": strings[0]["value"], "kernel_version": strings[1]["value"],
              "creation_date_text": strings[2]["value"], "units_in_mm": quantities[0]["value"],
              "resolution_tolerance": quantities[1]["value"], "normal_tolerance": quantities[2]["value"]}
    records, prefixes, current, depth = [], [], None, 0
    prefix_start = None
    token_count, last_complete = 0, reader.cursor
    failure = None
    while reader.cursor < len(data):
        try:
            token = reader.token()
            token_count += 1
            if token_count > 1000000 or len(records) > 100000:
                raise ValueError("ASM inspection exceeds supported record/token limits")
            if current is None:
                if token["tag"] == 14:
                    if not prefixes:
                        prefix_start = token["offset"]
                    prefixes.append(token["value"])
                    continue
                if token["tag"] != 13:
                    raise ValueError("Expected ASM entity name at "+str(token["offset"]))
                name = "-".join(prefixes+[token["value"]])
                prefixes.clear()
                current = {"index": len(records), "name": name,
                           "offset": prefix_start if prefix_start is not None else token["offset"], "tokens": []}
                prefix_start = None
                if name == "End-of-ASM-data":
                    current["end_offset"] = reader.cursor
                    records.append(current)
                    current, last_complete = None, reader.cursor
                continue
            if token["tag"] == 15:
                depth += 1
            elif token["tag"] == 16:
                depth -= 1
                if depth < 0:
                    raise ValueError("Unbalanced ASM subtype end")
            elif token["tag"] == 17:
                if depth:
                    raise ValueError("ASM record ends inside a subtype")
                current["end_offset"] = reader.cursor
                records.append(current)
                current, last_complete = None, reader.cursor
                continue
            current["tokens"].append(token)
        except (ValueError, UnicodeError, struct.error) as error:
            failure = str(error)
            break
    if failure is None and (current is not None or prefixes or depth):
        failure = "Incomplete final ASM record or subtype"
    if failure is None and (not records or records[-1]["name"] != "End-of-ASM-data"):
        failure = "Missing final ASM end marker"
    return {"header": header, "records": records, "token_count": token_count,
            "complete_token_stream": failure is None, "unresolved_reason": failure,
            "last_complete_offset": last_complete, "total_bytes": len(data),
            "scope": "Typed token records only; entity fields/topology remain uninterpreted"}


def inspect_asm_members(members, include_records=False):
    streams = []
    for member, data in members.items():
        if "/Breps.BlobParts/" not in member or not member.endswith((".smb", ".smbh")):
            continue
        try:
            result = inspect_asm(data)
            from decode_brep import decode_topology
            topology = decode_topology(result)
            if not include_records:
                topology.pop("nodes", None)
            topology["nodes_included"] = include_records
            counts = dict(sorted(Counter(r["name"] for r in result["records"]).items()))
            summary = {key: value for key, value in result.items() if key != "records"}
            summary.update(member=member, record_count=len(result["records"]), record_type_counts=counts,
                           blob_role="history" if member.endswith(".smbh") else "body data", topology=topology)
            summary["scope"] = "Typed token framing with separately reported partial topology; final visible-body identity unresolved"
            if include_records:
                summary["records"] = result["records"]
            streams.append(summary)
        except (ValueError, UnicodeError, struct.error) as error:
            streams.append({"member": member, "complete_token_stream": False, "unresolved_reason": str(error)})
    return {"streams": streams, "scope": "Observed ASM tokens and reciprocal topology; final visible-body identity unresolved"}


if __name__ == "__main__":
    from fusion_archive import read_members

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    parser.add_argument("--records", action="store_true", help="Include full typed records; output can be large")
    args = parser.parse_args()
    print(json.dumps([{"file": str(p), **inspect_asm_members(read_members(p, args.zstd_library), args.records)}
                      for p in args.files], indent=2))
