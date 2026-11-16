from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigSavedViews import ReadSavedViewBases, WriteSavedViews
from PartArchive import PartArchiveWriter
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.Presentation import (
    ReadEnvironment,
    ReadModelTagMut,
    ReadSavedDetail,
    ReadSavedViews as ReadNormalViews,
)
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


# Generated trig values may differ by a last bit within the saved camera basis.
def verify_fields(generated, saved, ranges):
    require(len(generated) == len(saved), "same saved view range width")
    previous = 0
    for start, end in ranges:
        require(
            generated[previous:start] == saved[previous:start],
            "exact nonrotation saved view fields",
        )
        previous = end
    require(generated[previous:] == saved[previous:], "exact saved view return")


# The normal reader fixes the boundary and allocation independently of the writer.
def inspect_views(archive, construct):
    generation = ContainerMo(archive.streams)
    blob = archive.require("Contents/Config-0")
    manager, _ = ReadRelEntry(blob, LoadPartLayouts())
    at = manager.offset + ReadTag(blob, manager.offset).size
    cursor = ArchiveCursor(blob, at, manager.Counter, manager.Classes, manager.Objects)
    events = []
    take = partial(ReadModelTagMut, cursor, events)
    ReadEmptyRel(cursor)
    ReadSavedDetail(cursor, take)
    ReadEnvironment(cursor, take)
    start = cursor.Offset
    before = map_state(cursor)
    comparison = before.Cursor(blob, start)
    ReadNormalViews(comparison, partial(ReadModelTagMut, comparison, []))
    ranges = tuple(
        (first - start, last - start)
        for first, last in ReadSavedViewBases(cursor, generation)
    )
    after = map_state(cursor)
    require(
        cursor.Offset == comparison.Offset and after == map_state(comparison),
        "same saved view return and complete archive map",
    )
    require(
        ReadTag(blob, cursor.Offset).class_name == "moSketchBlockMgr_c",
        "typed sketch block follows saved views",
    )
    saved = blob[start : cursor.Offset]
    if construct:
        writer = PartArchiveWriter(before)
        WriteSavedViews(writer, generation)
        data = writer.build()
        written = before.Cursor(data, 0)
        require(
            ReadSavedViewBases(written, generation) == ranges,
            "saved and generated basis positions agree",
        )
        require(
            written.Offset == len(data)
            and writer.Snapshot() == map_state(written) == after,
            "constructed saved view archive map",
        )
        verify_fields(data, saved, ranges)
    return sha256(saved).hexdigest()


# Evidence binds each reconstructed model view range to its pinned archive digest.
def report(construct):
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_views(archive, construct)
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned saved config view group")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
