from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

from VerifyResolvedPlanes import map_state

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "authoring"))

from AuthoredProfile import ReadAuthoredOpen, WriteAuthoredOpen
from HeaderLogs import ReadHeaderLogs
from PartArchive import PartArchiveWriter
from RectangleFields import line_fields, measured_graph, point_fields
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyRectCorners import verify_corners
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
    return corners, endpoints, tallies


# document IDs, archive allocations and geometry order must converge on the same owner
def inspect_open(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    config, model = ReadOrdinaryMap(archive.require("Contents/Config-0"), generation)
    stream = archive.require("Contents/Config-0-ResolvedFeatures")
    cursor = OpenResolved(stream, config, 18 + model["atom_count"])
    ReadSysPrefix(cursor)
    origin = ReadOrigin(cursor, generation)
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
    corners, endpoints, tallies = verify_members(stream, profile, measurement)
    after = map_state(cursor)
    if construct:
        writer = PartArchiveWriter(before)
        WriteAuthoredOpen(
            writer, generation, origin.SketchIndex, fields, len(corners) + 1
        )
        require(
            writer.build() == stream[start:end], "exact typed authored profile opening"
        )
        require(writer.Snapshot() == after, "constructed authored sketch map")
    opening = (
        start,
        end,
        before.NextIndex,
        cursor.NextIndex,
        fields.Feature.RegenTime,
        sha256(stream[start:end]).hexdigest(),
    )
    return opening, verify_corners(
        cursor, profile, corners, endpoints, tallies, generation, construct
    )


# composition pins the exact receipt order without relying on fixed record offsets
def report(construct):
    rows = []
    corner_rows = []
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        opening, corners = inspect_open(archive, measurement, construct)
        rows.append((asset["sha256"], *opening))
        corner_rows.append((asset["sha256"], *corners))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "corner_replay_sha256": sha256(
            json.dumps(corner_rows, separators=(",", ":")).encode()
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
