from convert.adapters.solidworks.config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor


# the resolved feature identity must come from its owned name and concept fields
def ReadNamedNode(
    Cursor: ArchiveCursor, ExpectedFlags: tuple[int, ...]
) -> tuple[str, int]:
    NameValue = Cursor.ReadText()
    NodeState, FlagValue, FeatureId, TailValue = Cursor.ReadInts("<iIii")
    RequireArch((NodeState, TailValue), (0, 0), "ordinary typed node")
    RequireArch(FlagValue in ExpectedFlags, True, "witnessed typed node flags")
    RequireArch(Cursor.ReadText(), "", "empty feature label")
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty lightweight child list")
    Cursor.ReadNull()
    return NameValue, FeatureId


# ordinary named features proceed from a checked empty node list to their feature fields
def ReadNamedFeat(
    Cursor: ArchiveCursor, ExpectedFlags: tuple[int, ...] = (0x40000000,)
) -> tuple[str, int]:
    Identity = ReadNamedNode(Cursor, ExpectedFlags)
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty resolved node list and tail")
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    return Identity
