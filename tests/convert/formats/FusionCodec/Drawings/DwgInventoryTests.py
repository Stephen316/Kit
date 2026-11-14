from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import ReadDrawBundle
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadDwgInventory
from tests.convert.formats.FusionCodec.Drawings.DrawingSource import HistoricBundle


def HistoricDwg() -> bytes:
    Database = ReadDrawBundle(HistoricBundle()).Drawing.Database
    assert Database is not None
    return Database.Content


def TestHistoricDwg() -> None:
    Content = HistoricDwg()
    Inventory = ReadDwgInventory(Content)
    assert Inventory.FileHeader.VersionText == "AC1027"
    Names = {Section.SectionInfo.SectionName for Section in Inventory.Sections}
    assert {"AcDb:AcDbObjects", "AcDb:Classes", "AcDb:Handles"} <= Names
    ClassNames = {Entry.DxfName for Entry in Inventory.ClassTable.ClassRows}
    assert {"ACDBVIEWREP", "ACDBVIEWREPBLOCKREFERENCE"} <= ClassNames
    assert len(Inventory.ClassTable.ClassRows) == 46
    assert Inventory.HandleMap.HandleCount == 900


def TestDwgRejects() -> None:
    Content = HistoricDwg()
    with ExpectError(ValueError, match="unsupported"):
        _ = ReadDwgInventory(b"AC1015" + Content[6:])
    Damaged = bytearray(Content)
    Damaged[0x18] = 1
    with ExpectError(ValueError, match="security flags"):
        _ = ReadDwgInventory(bytes(Damaged))
    with ExpectError(ValueError, match="outside the available data"):
        _ = ReadDwgInventory(Content[:0x40])
    Truncated = Content[: len(Content) // 2]
    with ExpectError(ValueError):
        _ = ReadDwgInventory(Truncated)
