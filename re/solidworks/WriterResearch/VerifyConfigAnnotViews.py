from functools import partial
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigScene.Annotation import KAnnotation, WriteAnnotViews
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import (
    ReadModelTagMut,
    ReadSavedAnnots,
)
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ContainerMo,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the real archive walk identifies the list at the allocation before its first view
def inspect_annos(
    config: bytes, generation: int, name: str, include_top: bool
) -> tuple[int, str]:
    final, walk = ReadOrdinaryMap(config, generation)
    events = walk["pointers"]
    (index,) = (
        i
        for i, event in enumerate(events)
        if event[2:4] == (KDefinitionKind, KAnnotation)
    )
    require(index > 0, "annotation list precedes the first view")
    start, count, kind, owner, _ = events[index - 1]
    require((kind, owner) == (KClassRefKind, "suObList"), "typed annotation list")
    inherited = PartArchiveState(
        count,
        tuple(sorted((i, n) for i, n in final.Classes.items() if i < count)),
        tuple(sorted((i, n) for i, n in final.Objects.items() if i < count)),
    )
    native = inherited.Cursor(config, start)
    read_native = partial(ReadModelTagMut, native, [])
    ReadSavedAnnots(native, read_native)
    stop = native.Offset
    after = allocation_state(native)
    require(
        after.NextIndex == count + 3 + int(include_top), "annotation allocation count"
    )
    ReadModelLists(native, read_native)

    writer = PartArchiveWriter(inherited)
    WriteAnnotViews(writer, generation, name, include_top)
    encoded = writer.build()
    require(encoded == config[start:stop], "exact constructed annotation views")
    reread = inherited.Cursor(encoded + config[stop : native.Offset], 0)
    read_back = partial(ReadModelTagMut, reread, [])
    ReadSavedAnnots(reread, read_back)
    require(
        reread.Offset == len(encoded)
        and writer.Snapshot() == allocation_state(reread) == after,
        "constructed annotation view extent and full map",
    )
    ReadModelLists(reread, read_back)
    require(
        reread.Offset == native.Offset - start
        and allocation_state(reread) == allocation_state(native),
        "independent following model lists consume the same archive span and map",
    )
    return len(encoded), sha256(encoded).hexdigest()


def report() -> dict[str, object]:
    captures: dict[str, str] = {}
    spans: dict[int, int] = {}
    for recipe, asset, data, _, measurement in principal_captures():
        (normal,) = (
            tuple(sketch["model_to_sketch_transform"][6:9])
            for sketch in measurement["sketches"]
            if sketch["name"] == "RectangleSketch"
        )
        require(normal in ((0, 0, 1), (-1, 0, 0)), "measured principal sketch pose")
        name = "*Front" if normal == (0, 0, 1) else "*Right"
        archive = SldprtArchive.from_bytes(data, asset["path"])
        generation = ContainerMo(archive.streams)
        require(generation == 19000, "modern annotation configuration")
        width, digest = inspect_annos(
            archive.require("Contents/Config-0"), 19000, name, recipe == "P03"
        )
        spans[width] = spans.get(width, 0) + 1
        captures[asset["sha256"]] = digest
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "span_counts": spans,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
