"""Replay the bounded scope array in exact provisional SOLIDWORKS archives."""

from argparse import ArgumentParser
import json
from pathlib import Path
import struct
import sys

from PairedCaptureIntake import GitSnapshot, require, sha256

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.config.CutConfig import ReadCutConfig
from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.Archive import (
    ArchiveError,
    ContainerMo,
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.resolved.FaceIdentity import ReadFaceReturn
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedNode
from convert.adapters.solidworks.resolved.cut.CutLinks import ReadCutLinks
from convert.adapters.solidworks.resolved.cut.CutProof import ReadCutProof
from SolidWorksScopePrefix import read_scope_prefix

GENERATION = 19000
BUILD = "34.4.1.1011"
SOURCE_REVISION = "c996f65f1745aad9aa7a82f89537eeb2f14303ee"
SOURCE_FOLDER = "re/automation/PairedCaptures/ScopeControl"
SOURCE_SHA256 = {
    "ScopeControlSpec.json": "298cf204b0e4329186b35d9cc46e36525e3ef2119dc7ddb870e73a5f86289d52",
    "RunSolidWorksScope.ps1": "d52e952b7d74b4111a4438a867ed0253e27e93e32332b0a153a6404cdfabef21",
    "SolidWorksScopeControl.cs": "715029d6d56168c70464a700c5160d283bfe6f7413eb9d36439b3c04a8a1efbc",
}
PROVISIONAL_SIZE = 59790
PROVISIONAL_SHA256 = "82141d768d1190bbc0193c0e30fdc06049a93ffdda88866b514c8d504213adfe"
PROVISIONAL_STREAM = "fb38482b123c2ffcf28e5dfdfb2691ce03822dd4049e71f3719ef102fa48949a"
REPEAT_REVISION = "12e4936ed6db1fb935249ba53c5c311fdc65fa66"
REPEAT_SIZE = 60152
REPEAT_SHA256 = "9a40bae98367deb569d0cf2662cadb8421807dee49470af12233390b8f6bfdd6"
REPEAT_STREAM = "1e67e1aeccdb7a856f65175486d42c062100ad147c2a6c18108b7a138df04a46"
REPEAT_SOURCE_SHA256 = {
    **SOURCE_SHA256,
    "SolidWorksScopeControl.cs": "04e6dbc92277c3121157a19f0db225f3162b6e6f16c92e2e4721cea33aaf15da",
}
CONTROL_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
CONTROL_FOLDER = "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
CONTROL_FILE = "P04-solidworks-termination-through-all.SLDPRT"
CONTROL_RECEIPT = "7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5"
CONTROL_ARCHIVE = "e1f431f1f21ae294fbd3711503ce386bec4fb4916c3cc83b57c876f1ae283149"
CONTROL_STREAM = "26341c83246d7a3088bb4ea44ecc978f56ebad2d4ceb6ee72942b090c1c506e4"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
SURFACES = {
    225: ("moEndFaceSurfIdRep_c", (0,)),
    234: ("moFromSktEntSurfIdRep_c", ()),
    307: ("moEndFace3IntSurfIdRep_c", (0, 0)),
    310: ("moFromSktEnt3IntSurfIdRep_c", (-1, 0)),
}


def slot(cursor, kind, *, index=None, class_name=None):
    address = cursor.Offset
    tag = ReadTag(cursor.BlobValue, address)
    require(not tag.wide and tag.kind == kind, f"unexpected compact pointer kind at {address}")
    if index is not None:
        require(tag.index == index, f"unexpected compact pointer slot at {address}")
    if class_name is not None:
        require(
            (tag.class_name, tag.schema) == (class_name, 1),
            f"incorrect class definition at {address}",
        )
    cursor.Offset += tag.size
    return tag


def unique_location(blob, marker, label):
    first = blob.find(marker)
    require(first >= 0 and blob.find(marker, first + 1) < 0, f"missing or repeated {label}")
    return first


def definition(blob, name):
    text = name.encode("ascii")
    position = unique_location(blob, struct.pack("<3H", 65535, 1, len(text)) + text, name)
    tag = ReadTag(blob, position)
    require(
        (tag.kind, tag.schema, tag.class_name) == (KDefinitionKind, 1, name),
        f"unexpected archive definition for {name}",
    )
    return position, tag.size


def named_node(blob, name, flags, *, class_name=None, class_index=None):
    marker = b"\xff\xfe\xff" + bytes((len(name),)) + name.encode("utf-16-le")
    name_offset = unique_location(blob, marker, f"framed name {name}")
    tag_offset = name_offset - 4
    if class_name is not None:
        tag_offset, width = definition(blob, class_name)
        require(tag_offset + width == name_offset - 2, f"{name} does not follow its declared class")
    cursor = ArchiveCursor(blob, tag_offset, 1, {}, {})
    if class_name is None:
        slot(cursor, KClassRefKind, index=class_index)
    else:
        slot(cursor, KDefinitionKind, class_name=class_name)
    slot(cursor, KClassRefKind, index=4)
    require(cursor.Offset == name_offset, f"incorrect name payload position for {name}")
    actual, feature = ReadNamedNode(cursor, flags)
    require(actual == name and feature > 0, f"invalid native identity for {name}")
    row = {
        "name": name,
        "feature_id": feature,
        "record_offset": tag_offset,
        "name_offset": name_offset,
    }
    return row, cursor


def read_transfer(cursor):
    address = cursor.Offset
    require(cursor.ReadInts("<iH") == (1, 2), "unsupported two-item atom-reference array")
    identities = [slot(cursor, KObjectRefKind).index for _ in range(2)]
    require(len(set(identities)) == 2, "repeated atom reference in transfer array")
    return {"offset": address, "object_slots": identities}


def read_local_part(cursor):
    slot(cursor, KClassRefKind, index=43)
    slot(cursor, KObjectRefKind, index=2)
    require(cursor.ReadInts("<B") == (0,), "external unit-component layout is unsupported")
    values = cursor.ReadInts("<20I")
    require(
        values[-1] == GENERATION and all(values[i] == 0 for i in (6, 14, 15, 16, 17, 18)),
        "unsupported scope component reference",
    )


def read_surface(cursor):
    address = cursor.Offset
    surface = slot(cursor, KClassRefKind)
    require(surface.index in SURFACES, f"unknown scope surface class slot at {address}")
    class_name, selectors = SURFACES[surface.index]
    slot(cursor, KNullKind, index=0)
    slot(cursor, KClassRefKind, index=227)
    target_file = slot(cursor, KObjectRefKind, index=230)
    owner, clock, occurrence = cursor.ReadInts("<iIi")
    if selectors:
        require(
            cursor.ReadInts(f"<{len(selectors)}i") == selectors,
            "unexpected scope surface selectors",
        )
    return {
        "offset": address,
        "class_slot": surface.index,
        "class_candidate": class_name,
        "feature_id": owner,
        "clock_word": clock,
        "occurrence": occurrence,
        "file_reference_slot": target_file.index,
    }


def read_scope_body(cursor, first):
    address = cursor.Offset
    if first:
        slot(cursor, KDefinitionKind, class_name="moCompSolidBody_c")
    else:
        slot(cursor, KClassRefKind, index=432)
    read_local_part(cursor)
    face_offset = cursor.Offset
    slot(cursor, KClassRefKind, index=223)
    version, state, count, flags, classifier = cursor.ReadInts("<5I")
    require(
        (version, state, count, flags) == (1, 0, 6, 512) and classifier > 0,
        f"unsupported scoped face at {face_offset}",
    )
    require(cursor.ReadPoint(2) == (1e100, 1e100), "unsupported scoped face scalar envelope")
    slot(cursor, KNullKind, index=0)
    surfaces = [read_surface(cursor) for _ in range(count - 1)]
    require(
        len({(row["class_slot"], row["occurrence"]) for row in surfaces}) == len(surfaces)
        and len({row["clock_word"] for row in surfaces}) == 1,
        "duplicate or inconsistent scope-face identity",
    )
    ReadFaceReturn(cursor)
    tail = cursor.Offset
    count, body, owner, atom, face_id = cursor.ReadInts("<5i")
    require(
        count == 1
        and min(body, owner, atom, face_id) > 0
        and {row["feature_id"] for row in surfaces} == {owner},
        "scope body has no unique local feature owner",
    )
    return {
        "offset": address,
        "end": cursor.Offset,
        "tail_offset": tail,
        "body_id": body,
        "feature_id": owner,
        "recent_atom_id": atom,
        "face_node_id": face_id,
        "face": {
            "offset": face_offset,
            "flags": flags,
            "classifier": classifier,
            "surfaces": surfaces,
        },
    }


def read_provisional(data, spec, stream_sha256, *, inspect_map=False):
    archive = SldprtArchive.from_bytes(data, "provisional-automatic.SLDPRT")
    blob = archive.require(RESOLVED)
    require(
        ContainerMo(archive.streams) == GENERATION and sha256(blob) == stream_sha256,
        "provisional ResolvedFeatures stream differs from its pin",
    )
    producers = {
        body: named_node(
            blob, spec["bodies"][body]["producer"], (0x40000140,), class_name=class_name
        )[0]
        for body, class_name in (("A", "moExtrusion_c"), ("B", "moICE_c"))
    }
    profile, _ = named_node(blob, spec["cut"]["sketch"], (0x40000000, 0xC0000000), class_index=176)
    cut, cursor = named_node(blob, spec["cut"]["feature"], (0x400201CA,), class_index=302)
    declarations = {
        name: definition(blob, name)[0]
        for name in (
            "moFaceRef_c",
            "moFR_c",
            *(name for name, _ in SURFACES.values()),
        )
    }
    require(
        all(position < cut["record_offset"] for position in declarations.values()),
        "scope-face class declarations must precede their named Cut",
    )
    require(
        producers["A"]["record_offset"]
        < producers["B"]["record_offset"]
        < profile["record_offset"]
        < cut["record_offset"],
        "named producers and Cut are not in the preserved archive order",
    )
    require(
        len({row["feature_id"] for row in (*producers.values(), profile, cut)}) == 4,
        "duplicate native identity among producers, profile and Cut",
    )
    require(cursor.ReadInts("<H") == (1,), "Cut must keep a single profile reference")
    cut["profile_reference_slot"] = slot(cursor, KObjectRefKind).index
    require(cursor.ReadInts("<i") == (0,), "unsupported Cut node trailer")
    ReadFeatBase(cursor.ReadValue, cursor.ReadPoint, cursor.ReadNull, cursor.ReadText)
    require(cursor.ReadInts("<i3H") == (0, 0, 0, 0), "unsupported Cut feature framing")
    transfers = [read_transfer(cursor), read_transfer(cursor)]
    require(
        len({index for group in transfers for index in group["object_slots"]}) == 4,
        "transfer arrays reuse an atom reference",
    )
    cursor.ReadNull()
    require(cursor.ReadInts("<i") == (2,), "Cut does not own two atom IDs")
    atom_ids = cursor.ReadInts("<2i")
    require(len(set(atom_ids)) == 2 and min(atom_ids) > 0, "Cut atom IDs are invalid or repeated")
    body_type_offset = cursor.Offset
    require(cursor.ReadInts("<i") == (3,), "unsupported atom-body type")
    array_offset = cursor.Offset
    require(cursor.ReadInts("<iH") == (1, 2), "local scope array is absent or lacks two items")
    body_records = [read_scope_body(cursor, first) for first in (True, False)]
    owners = {row["feature_id"]: label for label, row in producers.items()}
    require(
        len({row["body_id"] for row in body_records}) == len(owners) == 2
        and {row["feature_id"] for row in body_records} == owners.keys()
        and {row["recent_atom_id"] for row in body_records} == set(atom_ids),
        "scope array does not identify two distinct earlier Boss producers and atom IDs",
    )
    for row in body_records:
        row["producer_candidate"] = owners[row["feature_id"]]
    scope_offset = cursor.Offset
    (scope,) = cursor.ReadInts("<i")
    require(scope == 1, "unsupported saved feature-scope value")
    require(
        cursor.ReadInts("<2H") == (1, 2),
        "subsequent chooser lead disagrees with the scope-array return",
    )
    result = {
        "stream_sha256": stream_sha256,
        "stream_size_bytes": len(blob),
        "cut": cut,
        "named_profile_candidate": profile,
        "boss_producers": producers,
        "transfer_arrays": transfers,
        "earlier_scope_face_class_declarations": declarations,
        "atom_ids": atom_ids,
        "atom_body_type": 3,
        "atom_body_type_offset": body_type_offset,
        "scope_array_offset": array_offset,
        "scope_array_count": len(body_records),
        "scope_bodies": body_records,
        "scope_word_offset": scope_offset,
        "scope_word": scope,
        "observed_auto_select": None,
    }
    if inspect_map:
        prefix = read_scope_prefix(archive, blob, spec, GENERATION)
        first_boss = prefix["first_boss"]
        require(
            (first_boss["name"], first_boss["feature_id"], first_boss["start"])
            == (producers["A"]["name"], producers["A"]["feature_id"], producers["A"]["record_offset"]),
            "typed boss does not match the scope array's earlier owner",
        )
        scope_file_slots = {
            surface["file_reference_slot"]
            for body in body_records for surface in body["face"]["surfaces"]
        }
        require(
            scope_file_slots == {prefix["first_cap"]["file_reference"]["object_index"]},
            "scope surface reference differs from the typed file object allocated by the first boss",
        )
        result["resolved_prefix"] = prefix
    return result


def read_control(snapshot):
    receipt_path = f"{CONTROL_FOLDER}/receipt.json"
    raw = snapshot.blob(CONTROL_REVISION, receipt_path)
    require(sha256(raw) == CONTROL_RECEIPT, "P04 discovery receipt digest differs")
    receipt = snapshot.parse_document(raw, "P04 discovery receipt")
    cases = [item for item in receipt["native_files"] if item["file"] == CONTROL_FILE]
    require(
        len(cases) == 1 and cases[0]["sha256"] == CONTROL_ARCHIVE,
        "P04 through-all capture pin differs",
    )
    data = snapshot.blob(CONTROL_REVISION, f"{CONTROL_FOLDER}/{CONTROL_FILE}")
    require(
        len(data) == cases[0]["size_bytes"] and sha256(data) == CONTROL_ARCHIVE,
        "P04 native archive digest differs",
    )
    archive = SldprtArchive.from_bytes(data, CONTROL_FILE)
    blob = archive.require(RESOLVED)
    require(
        ContainerMo(archive.streams) == GENERATION and sha256(blob) == CONTROL_STREAM,
        "P04 ResolvedFeatures differs from its pin",
    )
    config = ReadCutConfig(archive.require("Contents/Config-0"), GENERATION)
    proof = ReadCutProof(ReadCutLinks(blob, config), config)
    operation = proof.Operation
    body = operation["solid_body"]
    scope = ArchiveCursor(blob, body["offset"] - 10, 1, {}, {})
    require(scope.ReadInts("<2iH") == (3, 1, 1), "P04 control atom type or scope count differs")
    scope.Offset = body["end"]
    require(scope.ReadInts("<i") == (1,), "P04 control feature-scope word differs")
    end = operation["end_specification"]
    require(
        end["conditions"] == (1, 0) and end["depth_display"] is None,
        "P04 control is not depthless through-all",
    )
    return {
        "archive_sha256": CONTROL_ARCHIVE,
        "capture_revision": CONTROL_REVISION,
        "receipt_sha256": CONTROL_RECEIPT,
        "stream_sha256": CONTROL_STREAM,
        "cut_feature_id": operation["native_feature_id"],
        "cut_record_offset": operation["offset"],
        "atom_body_type": 3,
        "scope_array_count": 1,
        "scope_word": 1,
        "scope_word_offset": body["end"],
        "scope_body_id": body["body_id"],
        "boss_feature_id": proof.Links.BossValue["native_feature_id"],
        "through_all_depth_selector_offset": end["depth_selector_offset"],
    }


def read_sample(path, snapshot, revision, source_sha256, size, archive_sha256, stream_sha256, *, inspect_map=False):
    with path.open("rb") as stream:
        data = stream.read(size + 1)
    require(
        len(data) == size and sha256(data) == archive_sha256,
        "provisional input must match the exact retained automatic archive",
    )
    sources = {}
    spec = None
    for name, digest in source_sha256.items():
        relative = f"{SOURCE_FOLDER}/{name}"
        raw = snapshot.blob(revision, relative)
        require(sha256(raw) == digest, f"committed authoring source differs for {name}")
        sources[name] = {
            "path": relative,
            "sha256": digest,
            "size_bytes": len(raw),
            "git_blob": snapshot.tree(revision)[relative],
        }
        if name == "ScopeControlSpec.json":
            spec = snapshot.parse_document(raw, name)
    require(spec is not None, "scope-control specification is missing")
    return {
        "archive_sha256": archive_sha256,
        "size_bytes": size,
        "source_revision": revision,
        "source_pins": sources,
        "input_case": "automatic",
        "campaign_completed": False,
        "full_incoming_class_map_verified": False,
        **read_provisional(data, spec, stream_sha256, inspect_map=inspect_map),
    }


def compare_repeats(primary, repeat):
    fields = ("cut", "boss_producers", "atom_ids", "atom_body_type", "scope_array_count", "scope_word")
    require(
        all(primary[field] == repeat[field] for field in fields),
        "the two retained saves disagree on their cut or scope inventory",
    )
    body_fields = ("body_id", "feature_id", "recent_atom_id", "face_node_id", "producer_candidate")
    bodies = []
    for first, second in zip(primary["scope_bodies"], repeat["scope_bodies"], strict=True):
        identity = {key: first[key] for key in body_fields}
        require(identity == {key: second[key] for key in body_fields}, "scope body identity differs across saves")
        bodies.append({
            **identity,
            "surface_clock_words": [
                sorted({surface["clock_word"] for surface in row["face"]["surfaces"]})
                for row in (first, second)
            ],
        })
    return {"matched_scope_fields": list(fields), "matched_bodies": bodies}


def report(path, repeat_path=None, *, inspect_map=False):
    snapshot = GitSnapshot(ROOT)
    primary = read_sample(
        path, snapshot, SOURCE_REVISION, SOURCE_SHA256, PROVISIONAL_SIZE, PROVISIONAL_SHA256, PROVISIONAL_STREAM,
        inspect_map=inspect_map,
    )
    control = read_control(snapshot)
    require(
        primary["scope_word"] == control["scope_word"]
        and primary["scope_array_count"] > control["scope_array_count"],
        "pinned body contrast does not preserve its scope word",
    )
    result = {
        "schema": 1,
        "claim": "provisional_archive_scope_body_candidates",
        "qualification": False,
        "application_build": BUILD,
        "model_generation": GENERATION,
        "provisional": primary,
        "discovery_control": control,
    }
    if repeat_path is not None:
        repeat = read_sample(
            repeat_path, snapshot, REPEAT_REVISION, REPEAT_SOURCE_SHA256, REPEAT_SIZE, REPEAT_SHA256, REPEAT_STREAM,
            inspect_map=inspect_map,
        )
        result["repeat"] = repeat
        result["repeat_comparison"] = compare_repeats(primary, repeat)
        if inspect_map:
            left, right = primary["resolved_prefix"], repeat["resolved_prefix"]
            require(
                all(left[field] == right[field] for field in ("first_profile", "first_boss", "first_operation")),
                "typed first profile or boss differs across saves",
            )
            result["repeat_comparison"]["resolved_prefix_matched"] = True
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--compare-repeat", type=Path)
    parser.add_argument("--inspect-map", action="store_true")
    arguments = parser.parse_args()
    try:
        value = report(arguments.archive, arguments.compare_repeat, inspect_map=arguments.inspect_map)
    except (ArchiveError, LookupError, OSError, ValueError) as error:
        parser.exit(1, f"scope archive refused: {error}\n")
    sys.stdout.buffer.write(
        (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    )


if __name__ == "__main__":
    main()
