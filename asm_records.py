"""Bounded token inspection for the observed ASM BinaryFile8 body blobs.

Tag meanings referenced from ezdxf's MIT-licensed ACIS tag documentation:
https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/const.py
The 64-bit integer/header interpretation is observed in local Fusion samples.
Tag 23 is a signed integer only inside the validated int64 attribute schema;
other contexts retain the earlier uninterpreted finite-double representation.
This is a token reader, not a geometry kernel or complete entity schema.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct


INT64_ATTRIBUTE = "int64_attrib-name_attrib-gen-attrib"


def _int64_attribute_prefix(tokens):
    """Recognize the observed typed header before assigning tag-23 semantics."""
    if ([t["kind"] for t in tokens] !=
            ["pointer", "integer", "pointer", "pointer", "pointer",
             "enum", "enum", "enum", "enum", "string"]
            or tokens[0]["value"] != -1 or tokens[1]["value"] != -1
            or any(t["value"] < -1 for t in tokens[2:5])
            or [t["value"] for t in tokens[5:9]] != [2, 1, 1, 2]
            or not tokens[9]["value"]):
        raise ValueError("Unsupported ASM int64 attribute prefix schema")


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

    def token(self, *, int64_attribute_value=False):
        start, tag = self.cursor, self.number("B")
        if tag in (4, 12, 21):
            kind, value = {4: "integer", 12: "pointer", 21: "enum"}[tag], self.number("q")
        elif tag == 23 and int64_attribute_value:
            kind, value = "integer64", self.number("q")
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
    section = "geometry"
    markers = {"Begin-of-ASM-History-Data", "End-of-ASM-History-Section", "End-of-ASM-data"}
    token_count, last_complete = 0, reader.cursor
    failure = None
    while reader.cursor < len(data):
        try:
            int64_value = (current is not None and current["name"] == INT64_ATTRIBUTE
                           and reader.data[reader.cursor] == 23)
            if int64_value:
                if depth:
                    raise ValueError("ASM int64 attribute value inside unsupported subtype")
                _int64_attribute_prefix(current["tokens"])
            token = reader.token(int64_attribute_value=int64_value)
            if int64_value and (reader.cursor >= len(data) or data[reader.cursor] != 17):
                raise ValueError("ASM int64 attribute value lacks exact record terminator")
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
                           "offset": prefix_start if prefix_start is not None else token["offset"], "tokens": [],
                           "section": section, "record_kind": "marker" if name in markers else "entity"}
                prefix_start = None
                if name in markers:
                    current["end_offset"] = reader.cursor
                    records.append(current)
                    current, last_complete = None, reader.cursor
                    if name == "Begin-of-ASM-History-Data":
                        section = "history"
                    elif name == "End-of-ASM-History-Section":
                        section = "trailing_states"
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
                if current["name"] == INT64_ATTRIBUTE:
                    if len(current["tokens"]) != 11 or current["tokens"][-1]["kind"] != "integer64":
                        raise ValueError("Unsupported ASM int64 attribute value schema")
                    _int64_attribute_prefix(current["tokens"][:-1])
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
            "scope": "Typed tokens with explicit history markers; pointer meanings outside the initial geometry section remain uninterpreted"}


def inspect_asm_members(members, include_records=False):
    streams = []
    for member, data in members.items():
        if "/Breps.BlobParts/" not in member or not member.endswith((".smb", ".smbh")):
            continue
        try:
            result = inspect_asm(data)
            from decode_brep import decode_topology
            subtype_catalog, subtype_summary = None, None
            needs_subtypes = any(
                (t['kind'] == 'entity_name' and t['value'] == 'ref')
                or (r['name'] == 'pcurve' and len(r['tokens']) == 7 and r['tokens'][3]['value'] in (1, -1, 2, -2))
                for r in result['records'] for t in r['tokens'])
            if needs_subtypes:
                from decode_asm_subtypes import decode_asm_subtypes
                try:
                    subtype_catalog = decode_asm_subtypes(data, parsed=result)
                    subtype_summary = {
                        'definition_count': len(subtype_catalog['definitions']),
                        'qualified_reference_count': len(subtype_catalog['references']),
                        'references': subtype_catalog['references'],
                        'unresolved': subtype_catalog['unresolved'], 'scope': subtype_catalog['scope']}
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                    subtype_summary = {'references': [], 'unresolved': [{'reason': str(error)}],
                        'scope': 'Inline subtype namespace unresolved; original token framing and initial topology reported separately'}
            topology = decode_topology(result, subtype_catalog=subtype_catalog)
            if any(node.get('partial_surface_definition') for node in topology['nodes']):
                from decode_vbl_components import decode_vbl_components
                try:
                    topology['vbl_component_boundaries'] = decode_vbl_components(
                        data, parsed=result, subtype_catalog=subtype_catalog, topology=topology)
                except (ValueError, KeyError, IndexError) as error:
                    topology['vbl_component_boundaries'] = {'decoded': [], 'unresolved': [{'reason': str(error)}],
                        'scope': 'VBL boundary component links unresolved; original partial definitions and surface diagnostics retained'}
            if not include_records:
                topology.pop("nodes", None)
            topology["nodes_included"] = include_records
            counts = dict(sorted(Counter(r["name"] for r in result["records"]).items()))
            summary = {key: value for key, value in result.items() if key != "records"}
            summary.update(member=member, record_count=len(result["records"]), record_type_counts=counts,
                           blob_role="history" if member.endswith(".smbh") else "body data", topology=topology)
            if subtype_summary is not None:
                summary['inline_subtypes'] = subtype_summary
            if any(r["name"] == INT64_ATTRIBUTE for r in result["records"]):
                from decode_sculpt_tool_attributes import decode_sculpt_tool_attributes
                try:
                    summary["sculpt_tool_attributes"] = decode_sculpt_tool_attributes(data, parsed=result)
                except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
                    # Unsupported history provenance cannot invalidate separately
                    # parsed token framing or replace initial topology output.
                    summary["sculpt_tool_attributes"] = {
                        "attributes": [], "journal_states": [],
                        "unresolved": [{"reason": str(error)}],
                        "scope": "Typed sculpt face provenance unresolved; initial topology and token completeness reported separately"}
            declared = result["header"]["stored_entity_count"]
            summary["declared_root_records"] = [
                {"index": r["index"], "kind": r["name"]} for r in result["records"][:declared]
            ] if 0 <= declared <= len(result["records"]) else []
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
