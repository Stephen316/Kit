from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

from VerifyResolvedPlanes import map_state

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "authoring"))

from AuthoredProfile import ReadAuthoredOpen, WriteAuthoredOpen
from HeaderLogs import ReadHeaderLogs
from OrdinaryResolved import BeginOrdinaryResolved, ReadResolvedSystem
from RectangleFields import line_fields, measured_graph, point_fields
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyOriginProxy import read_ghost, verify_proxy
from VerifyRectAnchor import verify_anchor
from VerifyRectAxes import verify_axes
from VerifyRectCorners import verify_corners
from VerifyRectDims import verify_dims
from VerifyRectLines import verify_lines
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfileSketch import ReadProfileBody
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# each archived member must match the independently measured graph and relation operands
def verify_members(stream, profile, measurement):
    corners, proxy, endpoints, tallies = measured_graph(measurement, profile.NameValue)
    points, lines = profile.Members.Points, profile.Members.Lines
    require(len(points) == len(lines) == 5, "typed rectangle member counts")
    for slot, (span, position, saved) in enumerate(
        zip(
            points,
            (*corners, proxy),
            profile.Geometry["point_relation_tallies"],
            strict=True,
        )
    ):
        point_fields(stream, span, slot, position, tallies, saved)
    roles = [
        line_fields(stream, span, line, endpoints, tallies)["role"]
        for span, line in zip(lines, profile.Geometry["lines"], strict=True)
    ]
    require(roles.count("structural_header") == 1, "single structural line")
    return corners, proxy, endpoints, tallies


# document IDs, archive allocations and geometry order must converge on the same owner
def inspect_open(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    config_blob = archive.require("Contents/Config-0")
    config, model = ReadOrdinaryMap(config_blob, generation)
    ghost = read_ghost(config_blob, model["relation_manager"])
    stream = archive.require("Contents/Config-0-ResolvedFeatures")
    cursor = OpenResolved(stream, config, 18 + model["atom_count"])
    config_state = map_state(cursor)
    system_cursor = config_state.Cursor(stream, cursor.Offset)
    system = ReadResolvedSystem(system_cursor, generation)
    ReadSysPrefix(cursor)
    origin = ReadOrigin(cursor, generation)
    require(
        system_cursor.Offset == cursor.Offset
        and map_state(system_cursor) == map_state(cursor),
        "independent complete resolved system",
    )
    start = cursor.Offset
    before = map_state(cursor)
    snapshot = before.Cursor(stream, start)
    profile = ReadProfileBody(snapshot, generation)
    fields, sketch_offset, sketch_index = ReadAuthoredOpen(
        cursor, generation, origin.SketchIndex
    )
    end = cursor.Offset
    require(
        (fields.Name, fields.TreeId, sketch_offset, sketch_index, end)
        == (
            profile.NameValue,
            profile.FeatureId,
            profile.SketchOffset,
            profile.SketchIndex,
            profile.Members.Points[0].Offset,
        ),
        "owned authored sketch and first physical point",
    )
    _, header = ReadHeaderLogs(
        archive.require("Contents/Config-0-ModelHeader"), generation
    )
    require(
        (fields.Name, fields.TreeId)
        in {(row.Name, row.TreeId) for row in header.Revisions},
        "profile identity independently logged in the model header",
    )
    (reference,) = profile.Geometry["external_point_references"]
    require(
        reference["feature_id"] == origin.FeatureId
        and reference["handle_class"] == "sgPointHandle",
        "distinct local proxy points to the previously decoded Origin",
    )
    corners, proxy_point, endpoints, tallies = verify_members(
        stream, profile, measurement
    )
    after = map_state(cursor)
    writer = origin_slots = None
    if construct:
        writer, origin_slots = BeginOrdinaryResolved(generation, config_state, system)
        require(writer.Snapshot() == before, "generated system owner map")
        WriteAuthoredOpen(
            writer, generation, origin_slots.SketchObject, fields, len(corners) + 1
        )
        require(writer.build() == stream[:end], "exact framed authored profile opening")
        require(writer.Snapshot() == after, "constructed authored sketch map")
    opening = (
        start,
        end,
        before.NextIndex,
        cursor.NextIndex,
        fields.Feature.RegenTime,
        sha256(stream[start:end]).hexdigest(),
    )
    corner_proof = verify_corners(
        cursor, profile, corners, endpoints, tallies, generation, writer
    )
    proxy_proof = verify_proxy(
        cursor, profile, origin, system.Origin, ghost, generation, writer, origin_slots
    )
    line_proof = verify_lines(cursor, profile, endpoints, tallies, generation, writer)
    dim_proof = verify_dims(cursor, profile, corners, measurement, generation, writer)
    axis_proof = verify_axes(
        cursor, profile, corners, endpoints, measurement, generation, writer
    )
    anchor_proof = verify_anchor(
        cursor,
        profile,
        (*corners, proxy_point),
        measurement,
        generation,
        PartArchiveWriter(map_state(cursor)) if construct else None,
    )
    return (
        opening,
        corner_proof,
        proxy_proof,
        line_proof,
        dim_proof,
        axis_proof,
        anchor_proof,
    )


# composition pins the exact receipt order without relying on fixed record offsets
def report(construct):
    rows = []
    corner_rows = []
    proxy_rows = []
    line_rows = []
    dim_rows = []
    axis_rows = []
    anchor_rows = []
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        opening, corners, proxy, lines, dims, axes, anchor = inspect_open(
            archive, measurement, construct
        )
        rows.append((asset["sha256"], *opening))
        corner_rows.append((asset["sha256"], *corners))
        proxy_rows.append((asset["sha256"], *proxy))
        line_rows.append((asset["sha256"], *lines))
        dim_rows.append((asset["sha256"], *dims))
        axis_rows.append((asset["sha256"], *axes))
        anchor_rows.append((asset["sha256"], *anchor))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "corner_replay_sha256": sha256(
            json.dumps(corner_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "proxy_replay_sha256": sha256(
            json.dumps(proxy_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "line_mark_orders": len({row[-2] for row in line_rows}),
        "line_replay_sha256": sha256(
            json.dumps(line_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "dim_replay_sha256": sha256(
            json.dumps(dim_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "axis_replay_sha256": sha256(
            json.dumps(axis_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "anchor_replay_sha256": sha256(
            json.dumps(anchor_rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "nonzero_regen_times": sum(row[-2] != 0.0 for row in rows),
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned authored sketch opening")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
