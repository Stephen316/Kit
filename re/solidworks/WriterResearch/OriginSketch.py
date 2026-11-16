from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

KSketchClass = "sgSketch"
KPointHandle = "sgPointHandle"
KObjectList = "suObList"


# The Origin sketch has one inline 2D point, with a real handle to its local slot.
def WriteOriginSketch(Writer: ArchiveWriter) -> int:
    Writer.begin_object(KSketchClass, 1)
    SketchObject = Writer.next_index - 1
    Writer.i32(1)
    Writer.raw(PackFields("<Hii", 0, 1, 1))
    Writer.raw(PackFields("<HHBIHhf", 65535, 31, 3, 0xFFFFFFFF, 65535, -1, -1.0))
    Writer.raw(PackFields("<i4Hhf", 1, 0, 4, 2, 1, 0, -1.0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<HHi", 4, 0, 1))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<BdIIHddHH", 0, 1.0, 0, 0, 31, 0.0, 0.0, 1, 0))
    Writer.raw(EncodeNull())
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<Hi4dHH", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0))
    Writer.raw(PackFields("<12i5Hi", *(0,) * 12, 0, 0, 0, 0, 1, 0))
    Writer.raw(EncodeNull())
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<4i", -1, 0, 0, 0))
    Writer.raw(EncodeNull())
    Writer.raw(PackFields("<HBi5H", 0, 0, 17, 2, 0, 0, 65534, 0))
    Writer.begin_object(KPointHandle, 1)
    Writer.raw(PackFields("<Hii", 0, -1, 0))
    return SketchObject


# Each empty presentation list retains an object allocation in the inherited namespace.
def WriteOriginView(Writer: ArchiveWriter) -> None:
    Writer.raw(PackFields("<7H", *(0,) * 7))
    Writer.begin_object(KObjectList, 1)
    Writer.u16(0)
    Writer.raw(PackFields("<7HHHi", *(0,) * 7, 2, 1, 2))
    Writer.raw(PackFields("<15i", 2, *(1,) * 12, 0, 1))
    Writer.raw(PackFields("<4H", 0, 0, 0, 0))
    Writer.string("")
    Writer.raw(PackFields("<hf3i3dI2i", -1, -1.0, -1, 1, -1, 0.0, 0.0, 0.0, 1, 0, 0))
    Writer.raw(PackFields("<2H5i", *(0,) * 7))
    Writer.begin_object(KObjectList, 1)
    Writer.u16(0)
    Writer.raw(PackFields("<H7iIi", *(0,) * 10))
    Writer.raw(PackFields("<iBiH2IH", 3, 1, 0, 0, 0, 100000, 0))
