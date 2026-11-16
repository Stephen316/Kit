from argparse import ArgumentParser
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from HeaderLogs import ReadHeaderLogs
from HeaderTail import KFrameTolerance
from PartArchive import PartArchiveState, PartArchiveWriter
from PrincipalPlaneView import BuildPlaneView, KPrincipalFrames
from ResolvedCabinet import ReadCabinetRec
from ResolvedFolderTail import ReadLateFolders
from ResolvedFolders import ReadSysFolders
from ResolvedPrincipal import ReadResolvedPlanes, WriteResolvedPlanes
from VerifyModelHeader import measured_bounds
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# map comparisons include each differently ordered configuration seed without shifting aliases
def map_state(cursor):
    return PartArchiveState(
        cursor.NextIndex,
        tuple(sorted(cursor.Classes.items())),
        tuple(sorted(cursor.Objects.items())),
    )


# each independent datum view must follow the measured world extent and feature tree
def verify_inspection(planes, normal, archive, generation, measurement):
    _, header = ReadHeaderLogs(
        archive.require("Contents/Config-0-ModelHeader"), generation
    )
    logged = {(log.Name, log.TreeId) for log in header.Revisions}
    measured = {
        row["name"] for row in measurement["feature_tree"] if row["type"] == "RefPlane"
    }
    bounds = measured_bounds(measurement)
    for plane, datum, frame in zip(
        planes, normal.Planes, KPrincipalFrames, strict=True
    ):
        identity = plane.Name, plane.TreeId
        require(
            identity == (datum.NameValue, datum.FeatureId), "same typed datum identity"
        )
        require(
            identity in logged and plane.Name in measured,
            "licensed principal datum identity",
        )
        require(datum.Geometry.NormalWorld == frame.Normal, "same datum orientation")
        view = plane.View
        derived = BuildPlaneView(frame, bounds)
        require(
            all(
                abs(saved - expected) <= KFrameTolerance
                for saved, expected in zip(
                    (*view.NamePoint, *view.Border, *view.DisplayRoot),
                    (*derived.NamePoint, *derived.Border, *derived.DisplayRoot),
                    strict=True,
                )
            ),
            f"{plane.Name} presentation matches licensed model extents",
        )


# the independent system reader supplies the complete datum return boundary and map
def inspect_planes(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    config, model = ReadOrdinaryMap(archive.require("Contents/Config-0"), generation)
    stream = archive.require("Contents/Config-0-ResolvedFeatures")
    cursor = OpenResolved(stream, config, 18 + model["atom_count"])
    normal_cursor = map_state(cursor).Cursor(stream, cursor.Offset)
    normal = ReadSysPrefix(normal_cursor)
    ReadSysFolders(cursor, generation)
    ReadCabinetRec(cursor, generation)
    ReadLateFolders(cursor, generation)
    start = cursor.Offset
    before = map_state(cursor)
    require(
        (start, before.NextIndex)
        == (normal.Planes[0].Offset, normal.LaterFolders[-1].NextIndex),
        "package plane start",
    )
    planes = ReadResolvedPlanes(cursor, generation)
    end = cursor.Offset
    require(
        end == normal_cursor.Offset and map_state(cursor) == map_state(normal_cursor),
        "package plane return map",
    )
    verify_inspection(planes, normal, archive, generation, measurement)
    if construct:
        writer = PartArchiveWriter(before)
        WriteResolvedPlanes(writer, generation, planes)
        require(
            writer.build() == stream[start:end], "exact typed principal plane bytes"
        )
        require(
            writer.Snapshot() == map_state(cursor), "constructed principal plane map"
        )
    return (
        start,
        end,
        before.NextIndex,
        cursor.NextIndex,
        sha256(stream[start:end]).hexdigest(),
    )


# each evidence row binds native plane coverage to an independently pinned asset
def report(construct):
    rows = []
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        rows.append((asset["sha256"], *inspect_planes(archive, measurement, construct)))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned principal datum records")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
