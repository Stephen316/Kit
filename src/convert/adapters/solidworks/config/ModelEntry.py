from convert.adapters.solidworks.config.RootEntry import EntryStop, FindEntry
from convert.adapters.solidworks.config.RootFields import FindMaterial
from convert.adapters.solidworks.config.RootLayout import ExtendRoot, PartLayouts
from convert.adapters.solidworks.container.Archive import LayoutTable, ReadTag
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor


# the material fields must establish real allocation order before any model child can be read
def ReadModelEntry(
    BlobValue: bytes, Stages: PartLayouts
) -> tuple[EntryStop, LayoutTable]:
    Transform = FindEntry(BlobValue, Stages.Prefix, "moTransRefPlaneData_c")
    BodyStart = Transform.offset + ReadTag(BlobValue, Transform.offset).size
    Cursor = FieldCursor(BlobValue, BodyStart)
    _ = Cursor.ReadInts("<6i")
    MaterialPos = FindMaterial(BlobValue, Cursor.Offset)
    Layouts = ExtendRoot(
        Stages.Prefix,
        Stages.Material,
        ("moMBD3DPDFPublishCacheData_c", "gcXhatch_c", "moMaterial_c", "uoModelData_c"),
        (MaterialPos - Cursor.Offset, 0, 0, 0),
    )
    return FindEntry(BlobValue, Layouts, "uoModelData_c"), Layouts
