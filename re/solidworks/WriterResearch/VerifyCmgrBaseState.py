from hashlib import sha256

from CmgrBaseHeader import ReadCmgrHeader, WriteCmgrHeader
from CmgrBossMass import ReadBossMass
from CmgrCollectionFront import ReadCmgrFront, WriteCmgrFront
from CmgrMass import ReadEmptyMass
from CmgrOpening import ReadCmgrFeature
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# The pinned mass boundary carries the same typed archive map as the visual return.
def verify_base_state(
    visual: ArchiveCursor, generation: int, body_count: int
) -> tuple[str, str]:
    RequireArch((visual.Offset, visual.NextIndex), (1095, 9), "CMgr visual return map")
    cursor = ArchiveCursor(
        visual.BlobValue,
        visual.Offset,
        visual.NextIndex,
        visual.Classes.copy(),
        visual.Objects.copy(),
    )
    writer = ArchiveWriter()
    writer.SetNextIndex(cursor.NextIndex)
    writer.classes.update((name, index) for index, name in cursor.Classes.items())
    ReadCmgrFeature(cursor, generation)
    start = cursor.Offset
    fields = ReadCmgrHeader(cursor, generation)
    RequireArch((start, cursor.Offset), (1206, 1234), "CMgr base header span")
    header = cursor.BlobValue[start:cursor.Offset]
    WriteCmgrHeader(writer, generation, fields)
    RequireArch(writer.build(), header, "CMgr base header state reconstruction")
    if body_count == 0:
        cursor.Offset = ReadEmptyMass(cursor.BlobValue, cursor.Offset, generation, body_count)
    else:
        ReadBossMass(cursor, generation, body_count)
    start = cursor.Offset
    ReadCmgrFront(cursor, generation, BodyCount=body_count, SaveMode=1)
    RequireArch((start, cursor.Offset), (1488, 1514), "CMgr default collection span")
    WriteCmgrFront(writer, generation, BodyCount=body_count, SaveMode=1)
    saved = cursor.BlobValue[start:cursor.Offset]
    RequireArch(writer.build(), header + saved, "CMgr default collection reconstruction")
    RequireArch(
        (writer.next_index, writer.classes),
        (cursor.NextIndex, {name: index for index, name in cursor.Classes.items()}),
        "CMgr default collection allocator",
    )
    RequireArch(
        (cursor.NextIndex, cursor.Classes, cursor.Objects),
        (visual.NextIndex, visual.Classes, visual.Objects),
        "CMgr default collections retain native map",
    )
    return sha256(header).hexdigest(), sha256(saved).hexdigest()
