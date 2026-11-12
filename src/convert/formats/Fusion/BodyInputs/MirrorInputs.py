from convert.formats.Fusion.BodyInputs.BodyInput import BodyInput, BodyInputs
from convert.formats.Fusion.BodyInputs.InputRefs import (
    KMaxBodyInputs,
    CheckPickPrefix,
    ReadInputPicks,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyPickContext import KBodyContext

# native body mirrors store an ordered collection independent of their plane selection
KMirrorGuid = "D1728651-3640-4CCF-8083-AF7703013978"

# the mode record repeats the exact operand list in a separate proxy
KMirrorControl = "C444E6AD-33DC-4877-B037-A3A5518856B1"

# collection records pair body descriptors with typed associations
KMirrorInputs = "8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF"


# the collection owns distinct descriptors and repeats its feature owner twice
def ReadMirrorList(
    BulkData: bytes, Owners: dict[int, RecordSpan], CollectionId: int, FeatureId: int
) -> tuple[tuple[int, int], ...]:
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KMirrorInputs)
    if Cursor.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion Mirror input collection prefix")
    Count = Cursor.ReadCount(KMaxBodyInputs)
    if not Count or len(Cursor.DataValue) != 74 + 26 * Count:
        raise ValueError("Unsupported Fusion Mirror input collection width")
    Slots: list[tuple[int, int]] = []
    for _ in range(Count):
        Descriptor = ReadNativeRef(Cursor)
        if Cursor.ReadWord() != 1:
            raise ValueError("Unsupported Fusion Mirror input association count")
        Association = ReadNativeRef(Cursor)
        _ = SelectCursor(BulkData, Owners, Association, KBodyContext)
        Slots.append((Descriptor, Association))
    FirstOwner = ReadNativeRef(Cursor)
    Cursor.Offset = len(Cursor.DataValue) - 11
    if FirstOwner != FeatureId or ReadNativeRef(Cursor) != FeatureId:
        raise ValueError("Fusion Mirror input collection owners disagree")
    if len({Association for _, Association in Slots}) != Count:
        raise ValueError("Fusion Mirror input association is repeated")
    return tuple(Slots)


# a mirror body list must agree with its owned body mode proxy in order and identity
def ReadMirrInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KMirrorGuid)
    CheckPickPrefix(Cursor)
    Control = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KMirrorControl)
    if (
        len(Control.DataValue) != 133
        or Control.TakeBytes(2) != bytes(2)
        or Control.TakeBytes(1) not in (b"\x00", b"\x01")
    ):
        raise ValueError("Unsupported Fusion Mirror input control")
    Control.Offset = 37
    if (Control.ReadWord(), Control.ReadWord()) != (2, 2):
        raise ValueError("Fusion Mirror input mode does not select bodies")
    Control.Offset = 107
    if ReadNativeRef(Control) != FeatureId:
        raise ValueError("Fusion Mirror input control owner disagrees")
    ProxyId = ReadNativeRef(Control)
    Slots = ReadMirrorList(BulkData, Owners, ReadNativeRef(Cursor), FeatureId)
    Picks = ReadInputPicks(BulkData, Owners, FeatureId, ProxyId, "input", 8)
    if tuple(PickValue.DescriptorId for PickValue in Picks) != tuple(
        Descriptor for Descriptor, _ in Slots
    ):
        raise ValueError("Fusion Mirror input collection and proxy disagree")
    return BodyInputs(
        tuple(
            BodyInput("input", ProxyId, Descriptor, Association)
            for Descriptor, Association in Slots
        )
    )
