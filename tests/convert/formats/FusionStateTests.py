from convert.formats.Fusion.FeatureState import ReadFeatState
from tests.convert.formats.FusionHistoryTests import NativeRef


# a newer footer uses paired version markers while retaining the state fields
def TestStateFooter() -> None:
    TailValue = bytearray(66)
    for Offset in (7, 39, 53):
        TailValue[Offset : Offset + 11] = NativeRef(100)
    TailValue[50] = 1
    TailValue[23:27] = TailValue[35:39] = b"\1\1\0\0"
    TailValue[5] = TailValue[51] = 1
    TailValue[52] = 1
    assert ReadFeatState(bytes(TailValue)) == (True, True)
    TailValue[5] = TailValue[51] = TailValue[52] = 0
    TailValue[23] = 4
    assert ReadFeatState(bytes(TailValue)) is None
    TailValue[35] = 4
    assert ReadFeatState(bytes(TailValue)) == (False, False)
