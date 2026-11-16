"""Compare reconstructed field fragments with the six pinned P01 SOLIDWORKS archives."""

from collections import Counter
from math import dist, isfinite
from pathlib import Path
from struct import Struct
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT / "re/automation"),
    str(ROOT / "re/solidworks/archive"),
]

from ArchiveVersion import KApplicationBuild
from PairedCaptureIntake import (
    CAPTURES,
    SPECIFICATIONS,
    GitSnapshot,
    inspect_capture,
    require,
    sha256,
)
from RectangularConfig import read_rectangle_configuration
from RectangularPlaneEvidence import REVISION, SPECIFICATION_SHA256
from ResolvedPrelude import read_resolved_prelude
from SketchRoot import KGeneration
from convert.adapters.solidworks.Container.Archive import (
    ContainerMo,
    KNullKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ProfileSketch import ReadProfileBody

MEMBER_HEAD = Struct("<H2i")
MEMBER_VISUAL = Struct("<HHBIHhf")
MEMBER_TALLY = Struct("<i")
MEMBER_MODE = Struct("<H")
MEMBER_WIDTH = Struct("<3Hhf")
MEMBER_FLAGS = Struct("<2Hi")
MEMBER_TAIL = Struct("<Bd2I")
POINT_FLAGS = Struct("<H")
POINT_POSITION = Struct("<2d")
LINE_ENDPOINTS = Struct("<2H")
LINE_STATE = Struct("<2HdH")
FIXED_CORNERS = 4


def local_metres(point, frame):
    scale = frame[12]
    require(scale == 1.0, "expected a unit scale principal frame")
    relative = [
        coordinate / 1000 - translation
        for coordinate, translation in zip(point, frame[9:12], strict=True)
    ]
    return tuple(
        sum(relative[row] * frame[row * 3 + column] for row in range(3))
        for column in (0, 1)
    )


def matched_slot(point, ordered):
    matches = [
        index
        for index, candidate in enumerate(ordered)
        if dist(point, candidate) <= 1e-12
    ]
    require(len(matches) == 1, "endpoint has no unique corner in the measured profile")
    return matches[0]


def measured_graph(reopened, name):
    (sketch,) = [row for row in reopened["sketches"] if row["name"] == name]
    require(
        sketch["fully_defined"] and sketch["region_count"] == 1,
        "expected one fully defined rectangle",
    )
    frame = sketch["model_to_sketch_transform"]
    edges = {}
    corners = set()
    for edge in sketch["entities"]:
        require(
            edge["type"] == 0 and not edge["construction"],
            "expected authored perimeter lines",
        )
        first, last = edge["id"]
        require(
            first == last and first not in edges,
            "expected unique observed line identities",
        )
        ends = tuple(
            local_metres(edge[key], frame) for key in ("start_world_mm", "end_world_mm")
        )
        edges[first] = ends
        corners.update(ends)
    require(
        len(edges) == len(corners) == FIXED_CORNERS, "expected a four-corner perimeter"
    )
    tallies = Counter()
    known = {}
    for relation in sketch["relations"]:
        for kind, operand in zip(
            relation["entity_types"], relation["entities"], strict=True
        ):
            slot, native_id = operand["id"]
            tallies[kind, slot, native_id] += 1
            if kind == 2:
                position = tuple(
                    value / 1000 for value in operand["point_local_mm"][:2]
                )
                require(
                    known.setdefault(slot, position) == position,
                    "inconsistent measured point slot",
                )
    require(FIXED_CORNERS in known, "missing separately identified origin proxy")
    proxy = known.pop(FIXED_CORNERS)
    require(
        len(known) == FIXED_CORNERS - 1, "expected exactly one unnamed perimeter corner"
    )
    (slot,) = set(range(FIXED_CORNERS)) - known.keys()
    (opposite,) = corners - set(known.values())
    known[slot] = opposite
    ordered = tuple(known[index] for index in range(FIXED_CORNERS))
    return (
        ordered,
        proxy,
        {
            line: tuple(matched_slot(end, ordered) for end in ends)
            for line, ends in edges.items()
        },
        tallies,
    )


def member_prefix(blob, span):
    start = span.Offset
    mode, member, native_id = MEMBER_HEAD.unpack_from(blob, start)
    visual_start = start + MEMBER_HEAD.size
    tally_start = visual_start + MEMBER_VISUAL.size
    compact = tally_start + MEMBER_TALLY.size
    (compact_value,) = MEMBER_MODE.unpack_from(blob, compact)
    require(compact_value == 0, "expected the explicit-width member branch")
    pointer = compact + MEMBER_MODE.size + MEMBER_WIDTH.size
    return {
        "mode": mode,
        "member": member,
        "native_id": native_id,
        "tally": tally_start,
        "visual": [visual_start, tally_start],
        "external_pointer": pointer,
    }


def member_geometry(blob, prefix):
    external = ReadTag(blob, prefix["external_pointer"])
    require(
        external.kind == KNullKind, "local member has a non-null external reference"
    )
    start = prefix["external_pointer"] + external.size
    flags, flags_two, _ = MEMBER_FLAGS.unpack_from(blob, start)
    extra_offset = start + MEMBER_FLAGS.size
    extra = ReadTag(blob, extra_offset)
    require(
        extra.kind == KNullKind, "local member has an unexpected supplemental reference"
    )
    end = extra_offset + extra.size
    require(
        MEMBER_TAIL.unpack_from(blob, end)[0] == 0,
        "named member is outside this experiment",
    )
    return end + MEMBER_TAIL.size, flags, flags_two


def exact_field(blob, offset, expected, boundary, name):
    end = offset + len(expected)
    require(
        end <= boundary and blob[offset:end] == expected,
        f"{name} differs at byte {offset}",
    )
    return [offset, end]


def point_fields(blob, span, slot, point, tallies, archive_point):
    prefix = member_prefix(blob, span)
    require(
        archive_point["id"] == (slot, prefix["native_id"]),
        "point span does not own its local slot",
    )
    tally = tallies[2, slot, prefix["native_id"]]
    tally_span = exact_field(
        blob,
        prefix["tally"],
        MEMBER_TALLY.pack(tally),
        span.EndOffset,
        "point incidence",
    )
    require(all(isfinite(value) for value in point), "nonfinite measured point")
    if slot == FIXED_CORNERS:
        require(
            prefix["mode"] == 1
            and ReadTag(blob, prefix["external_pointer"]).kind != KNullKind,
            "expected typed external Origin proxy",
        )
        return {
            "slot": slot,
            "incidence": tally_span,
            "external_pointer": prefix["external_pointer"],
        }
    offset, _, _ = member_geometry(blob, prefix)
    require(
        prefix["mode"] == 0 and POINT_FLAGS.unpack_from(blob, offset)[0] & 0x10,
        "expected local 2D point",
    )
    coordinates = exact_field(
        blob,
        offset + POINT_FLAGS.size,
        POINT_POSITION.pack(*point),
        span.EndOffset,
        "local point coordinates",
    )
    return {
        "slot": slot,
        "incidence": tally_span,
        "coordinates": coordinates,
        "unclassified_visual": prefix["visual"],
    }


def line_fields(blob, span, line, endpoints, tallies):
    prefix = member_prefix(blob, span)
    require(
        prefix["native_id"] == line["native_id"] and prefix["mode"] == 0,
        "line span does not own its typed member",
    )
    offset, flags, flags_two = member_geometry(blob, prefix)
    require(
        flags_two & 0x200 == 0
        and LINE_STATE.size + LINE_ENDPOINTS.size == span.EndOffset - offset,
        "expected the short line and absent direction vector branch",
    )
    state = LINE_STATE.unpack_from(blob, offset + LINE_ENDPOINTS.size)
    if line["native_id"] < 0:
        return {
            "role": "structural_header",
            "span": [span.Offset, span.EndOffset],
            "flags": flags,
            "line_state": state,
            "observed_slots": line["point_indices"],
        }
    slots = endpoints[line["native_id"]]
    require(
        tuple(line["point_indices"]) == slots,
        "typed line does not match independently resolved slots",
    )
    tally = tallies[3, line["native_id"], line["native_id"]]
    tally_span = exact_field(
        blob,
        prefix["tally"],
        MEMBER_TALLY.pack(tally),
        span.EndOffset,
        "line incidence",
    )
    return {
        "role": "perimeter",
        "native_id": line["native_id"],
        "incidence": tally_span,
        "endpoints": exact_field(
            blob,
            offset,
            LINE_ENDPOINTS.pack(*slots),
            span.EndOffset,
            "ordered line point slots",
        ),
        "line_state": state,
        "unclassified_visual": prefix["visual"],
    }


def read_profile(raw, name):
    archive = SldprtArchive.from_bytes(raw, name)
    require(ContainerMo(archive.streams) == KGeneration, "unexpected saved generation")
    config, description = read_rectangle_configuration(
        archive.require("Contents/Config-0"), KApplicationBuild
    )
    require(description["atom_count"] == 0, "expected a sketch-only configuration")
    blob = archive.require("Contents/Config-0-ResolvedFeatures")
    cursor, _ = read_resolved_prelude(blob, config, 18)
    return blob, ReadProfileBody(cursor, KGeneration)


def examine_archive(raw, name, reopen):
    blob, profile = read_profile(raw, name)
    ordered, proxy, endpoints, tallies = measured_graph(reopen, profile.NameValue)
    point_spans, line_spans = profile.Members.Points, profile.Members.Lines
    require(len(point_spans) == len(line_spans) == 5, "unexpected inline member roster")
    first_count = exact_field(
        blob,
        profile.Geometry["body_start"],
        MEMBER_TALLY.pack(len(ordered) + 1),
        point_spans[0].Offset,
        "point count",
    )
    second_count = exact_field(
        blob,
        point_spans[-1].EndOffset,
        MEMBER_TALLY.pack(len(endpoints) + 1),
        line_spans[0].Offset,
        "line count",
    )
    points = [
        point_fields(blob, span, slot, point, tallies, saved)
        for slot, (span, point, saved) in enumerate(
            zip(
                point_spans,
                (*ordered, proxy),
                profile.Geometry["point_relation_tallies"],
                strict=True,
            )
        )
    ]
    lines = [
        line_fields(blob, span, line, endpoints, tallies)
        for span, line in zip(line_spans, profile.Geometry["lines"], strict=True)
    ]
    require(
        sum(line["role"] == "structural_header" for line in lines) == 1,
        "missing unique structural header",
    )
    return {
        "resolved_sha256": sha256(blob),
        "points": points,
        "lines": lines,
        "count_fields": [first_count, second_count],
    }


def pinned_captures():
    snapshot = GitSnapshot(ROOT)
    raw_specs = snapshot.blob(REVISION, SPECIFICATIONS)
    require(sha256(raw_specs) == SPECIFICATION_SHA256, "pinned specifications changed")
    specifications = snapshot.parse_document(raw_specs, SPECIFICATIONS)
    (recipe,) = [item for item in specifications["recipes"] if item["id"] == "P01"]
    capture = f"{CAPTURES}P01/solidworks-75b9308cf13e/receipt.json"
    intake = inspect_capture(
        snapshot,
        REVISION,
        capture,
        recipe,
        "solidworks",
        specifications,
        SPECIFICATION_SHA256,
    )
    require(
        intake["split"] == "discovery"
        and intake["executable_file_version"] == KApplicationBuild,
        "expected the pinned P01 discovery build",
    )
    coverage = intake["recording_coverage"]
    require(
        coverage["readback_count"] == coverage["clean_load_diagnostic_count"] == 6
        and coverage["repeat_save_used_fresh_application_process"],
        "expected six independent clean readbacks",
    )
    readbacks = snapshot.document(REVISION, intake["measurements"]["path"])[
        "observations"
    ]["reopened_files"]
    files = []
    for asset in intake["native_files"]:
        name = asset["path"].rsplit("/", 1)[-1]
        raw = snapshot.blob(REVISION, asset["path"])
        require(sha256(raw) == asset["sha256"], "pinned part digest changed")
        files.append((name, asset["sha256"], raw, readbacks[name]))
    require(len(files) == 6, "unexpected P01 discovery count")
    return intake["measurements"], files


def report():
    measurements, captures = pinned_captures()
    cases = [
        {"archive": name, "source_sha256": digest, **examine_archive(raw, name, reopen)}
        for name, digest, raw, reopen in captures
    ]
    return {
        "scope": "p01-inline-sketch-field-fragments",
        "capture_revision": REVISION,
        "application_build": KApplicationBuild,
        "measurements": measurements,
        "native_candidate_emitted": False,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True, separators=(",", ":")))
