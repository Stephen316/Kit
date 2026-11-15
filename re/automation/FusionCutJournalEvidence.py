import calendar
import io
import json
import math
import runpy
import struct
import time
import zipfile

from FusionCutExtentEvidence import (
    MEMBER_LIMIT,
    REVISION,
    ROOT,
    design_members,
    p04_capture,
    record_site,
)
from FusionCutFaceEvidence import body_members, inspect_face
from FusionCutSketchEvidence import historical_observations
from PairedCaptureIntake import require, sha256

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_basics import named_features
from decode_sketch import reference
from decode_timeline import decode_timeline
from decode_timeline_state_details import BOOKKEEPING, decode_feature_bookkeeping
from fusion_metadata import design_records
from materialize_asm_literal_view import materialize_asm_literal_view


# actor clocks need the native owner and matching copies before the kernel join
def feature_clocks(data, records, observation):
    features = named_features(data, records)
    timeline = decode_timeline(data, records, features)
    (sequence,) = timeline["sequences"]
    expected = [
        (row["index"], row["name"], row["type"]) for row in observation["feature_tree"]
    ]
    observed = [
        (
            row["timeline_index"],
            row["name"],
            "ExtrudeFeature" if row["kind"] == "Extrude" else row["kind"],
        )
        for row in sequence["visible_entries"]
    ]
    require(
        len(observed) == 4 and observed == expected and not sequence["groups"],
        "P04 native and historical feature order disagree",
    )
    primary = {row.object_id: row for row in records if row.is_primary}
    require(
        len(primary) == sum(row.is_primary for row in records),
        "ambiguous P04 primary record",
    )
    clocks = []
    for feature in sequence["visible_entries"]:
        actor = primary[feature["object_id"]]
        payload = data[actor.body : actor.end]
        require(payload[-2:] == bytes(2), "unexpected P04 feature bookkeeping suffix")
        bookkeeping = primary[reference(payload, len(payload) - 13)]
        require(
            bookkeeping.class_guid == BOOKKEEPING, "wrong P04 feature bookkeeping class"
        )
        entries, value = decode_feature_bookkeeping(
            data[bookkeeping.body : bookkeeping.end], actor.object_id, primary
        )
        copies = [
            entry["stored_u64"]
            for entry in entries
            if entry["object_id"] == actor.object_id
        ]
        require(
            copies == [value] and 0 < value < 2**53,
            "P04 feature owner clock disagrees with its unique self entry",
        )
        clocks.append(
            {
                "feature": feature,
                "actor_record": record_site(data, actor),
                "bookkeeping_record": record_site(data, bookkeeping),
                "stored_clock_u64": value,
            }
        )
    values = [row["stored_clock_u64"] for row in clocks]
    require(
        all(a < b for a, b in zip(values, values[1:])),
        "P04 ordered actors lack increasing stored clocks",
    )
    return {
        "sequence": sequence,
        "sequence_record": record_site(
            data, primary[sequence["history_record_object_id"]]
        ),
        "unresolved_timeline_fields": timeline["unresolved"],
        "actors": clocks,
    }


# raw timestamp framing belongs to an independently validated body owner chain
def timestamp(blob, parsed, body_index, *, origins=None):
    attributes = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
    require(not attributes["unresolved"], "P04 timestamp owner chains are unresolved")
    (attribute,) = [
        row
        for row in attributes["ignored_validated_other_definition_attributes"]
        if row["definition_name"] == "Timestamp_attrib_def"
        and row["owner_record_index"] == body_index
    ]
    index = attribute["attribute_record_index"]
    record = parsed["records"][index]
    token = record["tokens"][7]
    offset = token["offset"]
    value = token["value"]
    require(
        math.isfinite(value)
        and value.is_integer()
        and 0 < value < 2**53
        and blob[offset : offset + 9] == b"\x06" + struct.pack("<d", value),
        "unexpected P04 timestamp encoding",
    )
    original_index = (
        index if origins is None else origins[index]["inspection_record_index"]
    )
    return {
        **attribute,
        "original_attribute_record_index": original_index,
        "timestamp_token_offset": offset,
        "timestamp_float64_hex": blob[offset + 1 : offset + 9].hex(),
        "exact_integral_timestamp_value": int(value),
    }


# archive clocks corroborate the timestamp scale without adding a timezone to wall time strings
def archive_context(content, parse_manifest, blob_member, kernel_text, actor_value):
    paths = ("Manifest.dat", "FusionAssetName[Active]/Manifest.dat")
    members, manifests = {}, []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for path in (*paths, blob_member):
            (info,) = [row for row in archive.infolist() if row.filename == path]
            members[path] = list(info.date_time)
            if path in paths:
                require(
                    0 < info.file_size <= MEMBER_LIMIT,
                    "unsupported P04 archive manifest size",
                )
                data = archive.read(info)
                manifest = parse_manifest(data, path == paths[0])
                require(
                    not manifest["unresolved_bytes"],
                    "P04 archive manifest has unresolved fields",
                )
                manifests.append(
                    {"path": path, "sha256": sha256(data), "fields": manifest["values"]}
                )
    root, active = (row["fields"] for row in manifests)
    require(
        root["active_asset_id"] == active["asset_id"],
        "P04 manifest asset scope differs",
    )
    utc_projection = time.gmtime(actor_value // 1_000_000)
    require(
        time.asctime(utc_projection) == kernel_text,
        "P04 kernel text and clock scale disagree",
    )
    (dos_seconds,) = set(tuple(parts) for parts in members.values())
    zip_difference = calendar.timegm((*dos_seconds, 0, 0, 0)) * 1_000_000 - actor_value
    require(
        abs(zip_difference) < 2_000_000,
        "P04 clock projection differs by a full DOS time interval",
    )
    return {
        "manifests": manifests,
        "zip_wall_times": members,
        "kernel_creation_date_text": kernel_text,
        "microsecond_epoch_projection_matches_second_text": True,
        "zip_wall_time_minus_cut_clock_projection_us": zip_difference,
        "scope": "ZIP and kernel text have no stored timezone and do not identify a feature actor",
    }


# only the slot with both qualified endpoint actors receives a chronological comparison
def kernel_actor_join(blob, cap, native):
    parsed = inspect_asm(blob)
    history = decode_asm_history(blob, parsed=parsed)
    require(
        history["neighbor_chain"] == [0, 2, 1] and len(history["journal_states"]) == 3,
        "unexpected P04 journal slot chain",
    )
    slot_zero, slot_one, slot_two = history["journal_states"]
    literal = materialize_asm_literal_view(
        blob, parsed=parsed, state_slot=0, pointer_side=0
    )
    origins = {row["view_record_index"]: row for row in literal["origin_map"]}
    initial_body = cap["literal_body_alias"]["side1_inspection_record_index"]
    literal_body = cap["literal_body_origin"]["view_record_index"]
    literal_original = cap["literal_body_origin"]["inspection_record_index"]
    left = timestamp(blob, literal["view_parsed"], literal_body, origins=origins)
    right = timestamp(blob, parsed, initial_body)
    left_clock = left["exact_integral_timestamp_value"]
    right_clock = right["exact_integral_timestamp_value"]
    actors = {row["stored_clock_u64"]: row["feature"] for row in native["actors"]}
    require(
        actors[left_clock]["name"] == "BlindBoss"
        and actors[right_clock]["name"] in ("BlindCut", "ThroughAllCut")
        and left_clock < right_clock,
        "P04 body timestamps do not identify the expected distinct endpoint actors",
    )

    left_attr = left["original_attribute_record_index"]
    right_attr = right["original_attribute_record_index"]
    pairs = [
        [side["inspection_record_index"] for side in row["pointer_sides"]]
        for row in slot_zero["entries"]
    ]
    require(
        pairs.count([literal_original, initial_body])
        == pairs.count([left_attr, None])
        == pairs.count([None, right_attr])
        == 1,
        "P04 slot zero body and timestamp mentions differ",
    )
    require(not slot_one["entries"], "P04 empty neighbor gained entries")
    slot_two_pairs = [
        [side["inspection_record_index"] for side in row["pointer_sides"]]
        for row in slot_two["entries"]
    ]
    require(
        slot_two_pairs.count([None, initial_body])
        == slot_two_pairs.count([None, left_attr])
        == 1
        and all(a is None and b != right_attr for a, b in slot_two_pairs),
        "P04 slot two no longer supplies only the mixed right side",
    )
    return {
        "payloads": history["journal_states"],
        "neighbor_chain": history["neighbor_chain"],
        "history_stream": history["history_stream"],
        "initial_body_record_index": initial_body,
        "literal_body_original_record_index": literal_original,
        "slot_zero_side_zero": {"actor": actors[left_clock], "timestamp": left},
        "slot_zero_side_one": {"actor": actors[right_clock], "timestamp": right},
        "slot_zero_endpoint_clock_difference": right_clock - left_clock,
        "slot_zero_unique_event_actor": None,
        "slot_one_actor": None,
        "slot_two_actor": None,
        "scope": "Slot zero endpoint actor clocks establish P04 source then result order; journal traversal and state ids remain uninterpreted",
    }


# the original pinned capture owns both the archive byte identity and the historical API order
def report():
    git, capture = p04_capture()
    measurement = capture["measurements"]
    data = git.blob(REVISION, measurement["path"])
    require(sha256(data) == measurement["sha256"], "P04 measurement digest differs")
    observations = historical_observations(
        capture, git.parse_document(data, measurement["path"])
    )
    parse_manifest = runpy.run_path(
        str(ROOT / "re/Fusion/Reconstruction/DocumentEnvelope/ReadEnvelope.py")
    )["manifest"]
    archives = []
    for source in capture["native_files"]:
        phase, observation = observations[source["variant"]]
        content = git.blob(REVISION, source["path"])
        cap = inspect_face(content, observation)
        member = cap["native_body_mapping"]["history_blob_member"]
        blob = body_members(content)[member]
        streams, design = design_members(content)
        records, _ = design_records(
            streams["BulkStream.dat"], streams["MetaStream.dat"]
        )
        native = feature_clocks(streams["BulkStream.dat"], records, observation)
        joined = kernel_actor_join(blob, cap, native)
        final_value = joined["slot_zero_side_one"]["timestamp"][
            "exact_integral_timestamp_value"
        ]
        archive = archive_context(
            content,
            parse_manifest,
            member,
            inspect_asm(blob)["header"]["creation_date_text"],
            final_value,
        )
        archives.append(
            {
                "source": source,
                "observation": phase,
                "design_members": design,
                "asm_history_member": {"path": member, "sha256": sha256(blob)},
                "archive_context": archive,
                "body_mapping": cap["native_body_mapping"],
                "native_timeline": native,
                "kernel_journal": joined,
            }
        )
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "receipt": capture["receipt"],
        "measurements": measurement,
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
