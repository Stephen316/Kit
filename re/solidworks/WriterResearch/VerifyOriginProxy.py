from dataclasses import replace
from hashlib import sha256

from LocalComponent import KComponentTail, KPartClass
from OriginProxy import KCompHandle, KPointBackup, OriginProxy, WriteOriginProxy
from OriginSketch import KPointHandle
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import SkipAtomList
from convert.adapters.solidworks.Config.RootAtoms import EndGhosts
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import KNullKind, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Members import ReadPointMut


# only a uniquely retained sketch-point ghost in the original configuration can own the proxy
def read_ghost(config, relation_offset):
    model, _ = ReadModelEntry(config, LoadPartLayouts())
    _, atom_start, atom_count = ModelAtomStart(config, model)
    start = SkipAtomList(config, atom_start, atom_count) + 4
    require(
        EndGhosts(config, start) == relation_offset, "validated ghost manager return"
    )
    cursor = FieldCursor(config, start)
    counter, packed = cursor.ReadInts("<iI")
    require(packed == 0x20000001, "one retained ghost in the populated partition")
    identity, kind, _, _, _ = cursor.ReadInts("<5i")
    require(
        identity == counter and identity > 0 and kind == 20,
        "typed local sketch-point ghost",
    )
    return identity


# use actual allocated object events to locate the inherited component's owner and time words
def proxy_state(sketch, before, origin, origin_state, ghost_id, generation):
    stream = sketch.BlobValue
    events = {
        name: (offset, obj) for offset, _, _, name, obj in sketch.PointerEvents if name
    }
    part_offset, part = events[KPartClass]
    require(part == origin.Support.PartIndex, "proxy resolves in Origin's actual part")
    component = FieldCursor(stream, part_offset + ReadTag(stream, part_offset).size)
    require(
        component.ReadInts("<B20i")
        == (0, 0, 0, 0, ghost_id, *KComponentTail, generation),
        "component ghost matches the independently decoded configuration owner",
    )
    feature, time = component.ReadInts("<iI")
    handle_offset, handle = events[KPointHandle]
    require(
        component.Offset == handle_offset,
        "feature identity directly precedes its point handle",
    )
    require(
        (feature, time, sketch.Handles[handle])
        == (origin.FeatureId, origin.Support.TimeValue, (0, -1, 0)),
        "wrapped handle resolves to the owned Origin point and its archived time",
    )
    require(
        sketch.Objects[events[KCompHandle][1]] == KCompHandle,
        "allocated component handle",
    )
    fields = FieldCursor(stream, handle_offset + ReadTag(stream, handle_offset).size)
    require(
        fields.ReadInts("<H2iIH") == (0, -1, 0, 1, 0),
        "local point handle and wrapper opening",
    )
    read_null = ReadTag(stream, fields.Offset)
    require(read_null.kind == KNullKind, "no secondary wrapped object")
    fields.Offset += read_null.size
    flags, stamp, transform, alternative = fields.ReadInts("<2i2H")
    require(
        (flags, transform, alternative) == (0, 0, 0),
        "ordinary wrapper flags and transforms",
    )
    require(
        stamp == origin_state.Feature.UpdateStamp,
        "reference access and saved Origin update",
    )
    require(
        fields.ReadInts("<11ih")
        == (0, 0, -12345, -12345, -12345, 0, generation, 0, 0, 0, -1, 0),
        "ordinary local reference return",
    )
    backup_offset, _ = events[KPointBackup]
    require(fields.Offset == backup_offset, "typed point backup follows wrapper")
    backup = FieldCursor(stream, backup_offset + ReadTag(stream, backup_offset).size)
    require(
        backup.ReadPoint(3) == (*origin.Geometry.PointValue, 0.0), "saved backup point"
    )
    require(
        sketch.NextIndex == before.NextIndex + 10,
        "proxy creates six objects and four classes",
    )
    return OriginProxy(
        origin.ObjectIndex,
        feature,
        origin.SketchIndex,
        part,
        ghost_id,
        time,
        stamp,
        origin.Geometry.PointValue,
    )


# keep the line-count boundary and shared namespace visible to the enclosing profile
def verify_proxy(
    cursor, profile, origin, origin_state, ghost_id, generation, writer, origin_slots
):
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    sketch.PointerEvents = []
    require(
        start == profile.Members.Points[-1].Offset, "distinct external Origin member"
    )
    result = ReadPointMut(sketch)
    source = proxy_state(sketch, before, origin, origin_state, ghost_id, generation)
    require(result == (5, 1, source.Position), "typed origin proxy incidence")
    end = sketch.Offset
    require(
        end == profile.Members.Points[-1].EndOffset,
        "next member count from the profile owner",
    )
    require(
        FieldCursor(cursor.BlobValue, end).ReadCount() == 5,
        "preceding the five typed lines",
    )
    if writer is not None:
        require(origin_slots is not None, "generated Origin feature and sketch slots")
        require(writer.Snapshot() == before, "generated sketch before Origin proxy")
        source = replace(
            source,
            FeatureObject=origin_slots.FeatureObject,
            SketchObject=origin_slots.SketchObject,
        )
        WriteOriginProxy(writer, generation, profile.SketchIndex, source)
        require(
            writer.build() == cursor.BlobValue[:end],
            "exact framed Origin proxy bytes",
        )
        require(
            writer.Snapshot() == map_state(sketch), "complete Origin proxy archive map"
        )
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    proof = (
        start,
        end,
        before.NextIndex,
        sketch.NextIndex,
        source.GhostBodyId,
        source.LastAccessStamp,
        sha256(cursor.BlobValue[start:end]).hexdigest(),
    )
    return proof, source
