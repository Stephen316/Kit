from convert.formats.Fusion.BodyInputs.BodyInput import BodyInput, BodyInputs
from convert.formats.Fusion.BodyInputs.InputRefs import (
    KMaxBodyInputs,
    ReadInputPicks,
    ReadPickRefs,
)
from convert.formats.Fusion.HistoryRef import ReadOptRefMut
from convert.formats.Fusion.ParamBinding import KBindingWidths
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import KSelectProxy, SelectCursor

# the solid shell role list can contain either whole body or face descriptors
KShellGuid = "E8063467-BC05-4688-8196-AECB90F0EFEE"


# shell inputs preserve authored order across all proxies before body qualification
def ReadShellInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KShellGuid)
    if Cursor.TakeBytes(2) != bytes(2) or any(
        FlagValue not in (0, 1) for FlagValue in Cursor.TakeBytes(2)
    ):
        raise ValueError("Unsupported Fusion Shell input prefix")
    Thickness = tuple(
        Identity for _ in range(2) if (Identity := ReadOptRefMut(Cursor)) is not None
    )
    if (
        not Thickness
        or any(
            Identity not in Owners or Owners[Identity].ClassGuid not in KBindingWidths
            for Identity in Thickness
        )
        or Cursor.TakeBytes(12) != bytes(12)
    ):
        raise ValueError("Fusion Shell thickness or input list framing disagrees")
    Picks: list[BodyInput] = []
    for ProxyId in ReadPickRefs(Cursor, Owners, KSelectProxy):
        Picks.extend(ReadInputPicks(BulkData, Owners, FeatureId, ProxyId, "input", 4))
        if len(Picks) > KMaxBodyInputs:
            raise ValueError("Fusion Shell body inputs exceed limit")
    return BodyInputs(tuple(Picks))
