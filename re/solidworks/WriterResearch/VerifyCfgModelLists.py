from functools import partial
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigScene.Annotation import KAnnotation
from ConfigScene.ModelLists import KMarkerClass, PartMarker, WriteModelLists
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import (
    ReadModelTagMut,
    ReadSavedAnnots,
)
from convert.adapters.solidworks.Config.Regions import ReadRegions
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the packaged reader fixes the annotation exit with its existing pointer map
def inspect_lists(config: bytes, generation: int, bodies: int) -> str:
    final, walk = ReadOrdinaryMap(config, generation)
    events = walk["pointers"]
    (index,) = (
        i
        for i, event in enumerate(events)
        if event[2:4] == (KDefinitionKind, KAnnotation)
    )
    require(index > 0, "annotation list precedes the first view")
    start, count, _, owner, _ = events[index - 1]
    require(owner == "suObList", "annotation list owner")
    inherited = PartArchiveState(
        count,
        tuple(sorted((i, n) for i, n in final.Classes.items() if i < count)),
        tuple(sorted((i, n) for i, n in final.Objects.items() if i < count)),
    )
    native = inherited.Cursor(config, start)
    read_native = partial(ReadModelTagMut, native, [])
    ReadSavedAnnots(native, read_native)
    start = native.Offset
    before = allocation_state(native)
    (mark,) = (
        event for event in events if event[2:4] == (KDefinitionKind, KMarkerClass)
    )
    fields = before.Cursor(config, mark[0] + ReadTag(config, mark[0]).size)
    marker = PartMarker(*fields.ReadInts("<2i"))
    require(marker == PartMarker(3, 1), "witnessed partition mark and atom-map mode")
    ReadModelLists(native, read_native)
    stop = native.Offset
    after = allocation_state(native)
    require(
        (stop - start, after.NextIndex - before.NextIndex) == (164, 5),
        "model lists extent and slots",
    )
    regions = ReadRegions(native)
    require(
        sum(map(len, regions)) == bodies, "model region rows follow the body history"
    )

    writer = PartArchiveWriter(before)
    WriteModelLists(writer, generation, marker)
    encoded = writer.build()
    require(encoded == config[start:stop], "exact constructed model lists")
    reread = before.Cursor(encoded + config[stop : native.Offset], 0)
    ReadModelLists(reread, partial(ReadModelTagMut, reread, []))
    require(
        reread.Offset == len(encoded)
        and writer.Snapshot() == allocation_state(reread) == after,
        "constructed lists extent and full map",
    )
    require(
        ReadRegions(reread) == regions and reread.Offset == native.Offset - start,
        "independent following region groups consume the same fields",
    )
    return sha256(encoded).hexdigest()


def report() -> dict[str, object]:
    captures: dict[str, str] = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        require(
            ContainerMo(archive.streams) == 19000, "modern model lists configuration"
        )
        captures[asset["sha256"]] = inspect_lists(
            archive.require("Contents/Config-0"), 19000, measurement["body_count"]
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
