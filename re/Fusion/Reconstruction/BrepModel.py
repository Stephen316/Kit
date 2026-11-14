import argparse
import collections
import json
from pathlib import Path


BASE = ("attribute", "history_or_identity", "reserved_reference")
LAYOUTS = {
    "asmheader": ("attribute", "history_or_identity", "kernel_version"),
    "body": BASE + ("first_lump", "first_wire", "transform"),
    "lump": BASE + ("next_lump", "first_shell", "owner_body"),
    "shell": BASE + ("next_shell", "first_subshell", "first_face", "wire", "owner_lump"),
    "face": BASE + ("next_face", "first_loop", "owner_shell", "reserved_face_reference", "surface", "sense", "sidedness", "conditional_containment"),
    "loop": BASE + ("next_loop", "first_coedge", "owner_face"),
    "coedge": BASE + ("next_coedge", "previous_coedge", "partner_coedge", "edge", "sense", "owner_loop", "reserved_integer", "pcurve"),
    "edge": BASE + ("start_vertex", "start_parameter", "end_vertex", "end_parameter", "owner_coedge", "curve", "sense", "convexity"),
    "vertex": BASE + ("owner_edge", "edge_index", "point"),
    "point": BASE + ("position_cm",),
    "plane-surface": BASE + ("origin_cm", "normal", "reference_axis", "v_sense", "u_start", "u_end", "v_start", "v_end"),
    "cone-surface": BASE + ("origin_cm", "axis", "major_axis_cm", "ellipse_ratio", "ellipse_start", "ellipse_end", "sine_angle", "cosine_angle", "u_scale_cm", "sense", "u_start", "u_end", "v_start", "v_end"),
    "ellipse-curve": BASE + ("center_cm", "normal", "major_axis_cm", "ellipse_ratio", "parameter_start", "parameter_end"),
}


def semantic_value(token):
    return True if token["tag"] == 10 else False if token["tag"] == 11 else token["value"]


def attribute(record, records):
    tokens = record["fields"]
    values = [semantic_value(item) for item in tokens]
    owner = values[4]
    result = {"reserved": values[0], "marker": values[1], "next": values[2], "previous": values[3], "owner": owner, "family": values[5]}
    family = result["family"]
    if family == "Timestamp_attrib_def":
        result.update({"schema_marker": values[6], "authoring_unix_microseconds": values[7]})
        result["unmapped_values"] = values[8:]
    elif family == "sketch_attrib_def":
        result.update({"markers": values[6:8], "form": values[8]})
        if values[8] == 3:
            members = list(map(int, values[9].split()))
            result["source_link"] = dict(zip(("sketch_curve_id", "secondary_id", "sense", "reserved_zero", "enum_a", "enum_b"), members))
            result["unmapped_values"] = values[10:]
        else:
            result["unmapped_values"] = values[9:]
    elif family == "generic_tag_attrib_def":
        result.update({"schema_markers": values[6:9], "repeated_family": values[9], "group_count": values[10], "groups": []})
        at = 11
        owner_type = records[owner]["name"]
        for _ in range(values[10]):
            if owner_type == "body" and values[at] == 3:
                group = dict(zip(("entity_class", "persistent_design_id", "design_reference", "zero_a", "zero_b"), values[at:at + 5]))
                at += 5
            else:
                selector, text, zero, count = values[at:at + 4]
                group = {"selector": selector, "token": text, "zero_a": zero, "reference_count": count, "design_references": values[at + 4:at + 4 + count], "zero_b": values[at + 4 + count]}
                at += 5 + count
            result["groups"].append(group)
        result["unmapped_values"] = values[at:]
    else:
        result["unmapped_values"] = values[6:]
    return result


def history(stream):
    start = stream["history_record_index"]
    if start is None:
        return None
    records = stream["records"]
    preamble = [semantic_value(item) for item in records[start]["fields"]]
    states = []
    live = set(range(start))
    for row in records[start + 1:]:
        if row["name"] != "delta_state":
            continue
        values = [semantic_value(item) for item in row["fields"]]
        state = dict(zip(("state_id", "marker_one", "marker_zero", "previous_node", "next_node", "node_index", "reserved_null", "reserved_zero", "boolean_sentinel"), values[:9]))
        state["live_slots_before_reversing"] = sorted(live)
        state["boards"] = []
        at = 9
        while values[at] != 0:
            board = {"present_marker": values[at], "owner": values[at + 1], "number": values[at + 2], "changes": []}
            at += 3
            while values[at] != 0:
                marker, old, new = values[at:at + 3]
                kind = "insert" if old == -1 else "delete" if new == -1 else "update"
                board["changes"].append({"present_marker": marker, "old_revision": old, "new_revision": new, "kind": kind})
                if kind == "insert":
                    if new not in live:
                        raise ValueError("History insertion refers to an absent active slot")
                    live.remove(new)
                elif kind == "delete":
                    live.add(old)
                at += 3
            at += 1
            state["boards"].append(board)
        at += 1
        state["tail_values"] = values[at:]
        state["live_slots_after_reversing"] = sorted(live)
        states.append(state)
    return {"preamble": dict(zip(("stream_size", "stream_size_duplicate", "reserved_zero", "entry_count", "reference_a", "reference_b", "reference_c", "reference_d"), preamble)), "states": states, "initial_singleton_asmheader": live == {0}, "scope": "Insertion-only membership reversal is interpreted; update and deletion revision materialization require archived record namespace handling"}


def describe(stream):
    records = stream["records"][:stream["initial_record_count"]]
    output = []
    for row in records:
        name = row["name"]
        if name == "ATTRIB_CUSTOM-attrib":
            fields = attribute(row, records)
        elif name in LAYOUTS:
            names = LAYOUTS[name]
            if len(row["fields"]) > len(names):
                raise ValueError(f"Extra fields in {name}")
            fields = dict(zip(names, (semantic_value(item) for item in row["fields"])))
        else:
            fields = {"unmapped_tokens": row["fields"]}
        output.append({"index": row["physical_record_index"], "name": name, "offset": row["offset"], "size": row["size"], "fields": fields})
    referenced = [item["value"] for row in records for item in row["fields"] if item["tag"] == 12 and item["value"] >= 0]
    return {
        "member": stream["member"],
        "sha256": stream["sha256"],
        "header": stream["header"],
        "initial_record_count": len(records),
        "initial_references_in_range": all(value < len(records) for value in referenced),
        "records": output,
        "history": history(stream),
        "unresolved_semantics": ["Meaning of reserved non-null entity references", "Vertex edge_index=2 on top closed-circle vertex", "Generic tag selector and token construction rules across arbitrary modeling operations", "History stream_size and entry_count interpretation outside this native control"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tokens", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    inputs = json.loads(args.tokens.read_text())
    result = {"source": inputs["source"], "streams": [describe(stream) for stream in inputs["streams"]]}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for stream in result["streams"]:
        print(json.dumps({"member": stream["member"], "records": stream["initial_record_count"], "references_in_range": stream["initial_references_in_range"], "history_states": len(stream["history"]["states"]) if stream["history"] else 0}, indent=2))


if __name__ == "__main__":
    main()
