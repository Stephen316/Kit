from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyResolvedPlanes import map_state

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "authoring"))

from CmgrExternal import ReadExtRecord
from PartArchive import PartArchiveState, PartArchiveWriter
from RectangleFields import measured_graph
from RectangleRegion import CheckRectOutline
from RectangleTrim import RectTrimState, TrimMember, WriteRectTrim
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd, ReadRectTrim
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.Resolved.ProfileSketch import ReadProfileBody
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


# preserve the live config-to-resolved namespace through the normal principal support read
def open_trim(archive, generation):
    config, model = ReadOrdinaryMap(archive.require("Contents/Config-0"), generation)
    stream = archive.require("Contents/Config-0-ResolvedFeatures")
    cursor = OpenResolved(stream, config, 18 + model["atom_count"])
    ReadSysPrefix(cursor)
    ReadOrigin(cursor, generation)
    profile = ReadProfileBody(cursor, generation)
    edges = tuple(
        edge["native_id"]
        for edge in profile.Geometry["lines"]
        if edge["native_id"] >= 0
    )
    has_atom = bool(model["atom_count"])
    ReadChainState(cursor, has_atom, edges)
    reference = ReadProfileRef(cursor, generation)
    return cursor, profile, edges, int(has_atom), reference


# the production read established the unique file allocation and its enclosing surface map
def read_file(stream, file_ref, after, generation):
    slot = file_ref["object_index"] - 1
    saved = PartArchiveState(
        slot,
        tuple(row for row in after.Classes if row[0] < slot),
        tuple(row for row in after.Objects if row[0] < slot),
    )
    cursor = saved.Cursor(stream, file_ref["offset"])
    file, modification = ReadExtRecord(cursor, generation, SelfReference=False)
    require(
        cursor.Offset == file_ref["end"]
        and file.SavedTime == file_ref["shared_time_word"]
        and modification == 0,
        "same typed standalone document reference",
    )
    return file


# every trim edge must attach to the independently measured perimeter in native order
def inspect_trim(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    cursor, profile, edges, mode, reference = open_trim(archive, generation)
    start, before = cursor.Offset, map_state(cursor)
    owner = {
        "profile_object": profile.ObjectIndex,
        "native_feature_id": profile.FeatureId,
    }
    trim = ReadRectTrim(cursor, owner, edges, mode)
    end, after = cursor.Offset, map_state(cursor)
    surface = trim["trim_surface"]
    file_ref = surface["file_reference"]
    file = read_file(cursor.BlobValue, file_ref, after, generation)
    members = tuple(
        TrimMember(edge["class"], edge["edge_id"]) for edge in trim["trim_edges"]
    )
    _, _, measured, _ = measured_graph(measurement, profile.NameValue)
    CheckRectOutline(measured, tuple(member.EdgeId for member in members))
    state = RectTrimState(trim["state_word"], surface["time_word"], file, members)
    require(
        after.NextIndex - before.NextIndex == 19
        and len(after.Classes) - len(before.Classes) == 6
        and len(after.Objects) - len(before.Objects) == 13,
        "surface, file, string handles, segment sides and feature reference allocations",
    )
    continuation = ReadRectEnd(cursor, bool(mode))
    raw = cursor.BlobValue[start:end]
    if construct:
        writer = PartArchiveWriter(before)
        file_index = WriteRectTrim(writer, generation, owner, edges, mode, state)
        require(file_index == file_ref["object_index"], "trim file object for reuse")
        require(writer.build() == raw, "exact owned rectangle trim bytes")
        require(writer.Snapshot() == after, "exact contour classes and objects")
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        file_ref["object_index"],
        reference.AxisCode,
        file.Flags,
        state.DerivedStamp,
        tuple((member.ClassName, member.EdgeId) for member in members),
        continuation,
        sha256(raw).hexdigest(),
    )


# source digests bind the complete ordered boundary and allocation replay
def report(construct):
    rows = []
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        rows.append((asset["sha256"], *inspect_trim(archive, measurement, construct)))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "trim_replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "path_forms": len({row[7] for row in rows}),
        "side_orders": len({row[9] for row in rows}),
        "extrusion_returns": sum(row[10] == "moExtrusion_c" for row in rows),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the pinned rectangle contour trim")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
