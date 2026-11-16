from collections import Counter
from collections.abc import Mapping, Sequence
from math import isfinite as IsFinite
from re import compile as CompileRegex
from typing import cast as CastValue

from convert.adapters.freecad.Archive import IsPayloadMap
from convert.Geometry.Formula.FormulaUnits import GetQuantity, KFormulaUnits
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.document.Models.DocumentModel import CadDocument

# alias recovery stays bounded independently from the larger native archive inventory
KMaxCells = 4096

# object and alias spelling remains explicit rather than trusting labels or generated metadata
KAliasName = CompileRegex(r"[A-Za-z][A-Za-z_0-9]{0,127}")

# bounded cell addresses produce stable native identities without row order inference
KCellAddress = CompileRegex(r"[A-Z]{1,3}[1-9][0-9]{0,6}")

# finite decimal literals exclude formulas and cap exponent work before numeric conversion
KLiteral = CompileRegex(
    r"(?P<number>[+-]?(?:[0-9]{1,64}(?:\.[0-9]{0,64})?|\.[0-9]{1,64})"
    + r"(?:[eE](?P<exponent>[+-]?[0-9]{1,3}))?)[ \t]*(?P<unit>[A-Za-z]{0,8})"
)


# native metadata lists must be complete bounded records before aliases acquire authority
def ReadNodes(Value: object, Limit: int) -> tuple[Mapping[str, object], ...]:
    if not isinstance(Value, (list, tuple)):
        raise ValueError("record_shape")
    Nodes = CastValue(Sequence[object], Value)
    if len(Nodes) > Limit:
        raise OverflowError("record_limit")
    if any(not IsPayloadMap(NodeValue) for NodeValue in Nodes):
        raise ValueError("record_shape")
    return tuple(CastValue(Mapping[str, object], NodeValue) for NodeValue in Nodes)


# typed cells retain authored units while rejecting nonfinite or unsupported quantities
def ReadLiteral(Source: str) -> ParameterValue | None:
    if len(Source) > 256:
        return None
    LiteralText = Source.strip()
    if LiteralText.startswith("="):
        LiteralText = LiteralText[1:].strip()
    Match = KLiteral.fullmatch(LiteralText)
    if Match is None or Match["unit"] not in KFormulaUnits:
        return None
    if Match["exponent"] is not None and abs(int(Match["exponent"])) > 308:
        return None
    Number = float(Match["number"])
    if not IsFinite(Number) or (
        Number == 0.0
        and any(
            DigitValue in "123456789"
            for DigitValue in Match["number"].lower().partition("e")[0]
        )
    ):
        return None
    Value = ParameterValue(
        Number,
        {
            (1, 0): ValueKind.KLength,
            (0, 1): ValueKind.KAngle,
            (0, 0): ValueKind.KNumber,
        }[KFormulaUnits[Match["unit"]][1]],
        Match["unit"],
    )
    Quantity = GetQuantity(Value)
    return (
        Value
        if Quantity is not None and (Number == 0.0 or Quantity[0] != 0.0)
        else None
    )


# only actual spreadsheet cell records can define aliases for native property expressions
def ReadCells(Sheet: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    Properties = Sheet.get("properties")
    Property = Properties.get("cells") if IsPayloadMap(Properties) else None
    if not IsPayloadMap(Property):
        raise ValueError("cells_missing")
    Attributes = Property.get("attributes")
    if (
        not IsPayloadMap(Attributes)
        or Attributes.get("type") != "Spreadsheet::PropertySheet"
    ):
        raise ValueError("cells_type")
    Groups = tuple(
        NodeValue
        for NodeValue in ReadNodes(Property.get("children", ()), KMaxCells)
        if NodeValue.get("tag") == "Cells"
    )
    if len(Groups) != 1:
        raise ValueError("cells_shape")
    return ReadCellGroup(Groups[0])


# external sheet references cannot acquire local literal alias authority
def ReadCellGroup(Group: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    Children = ReadNodes(Group.get("children", ()), KMaxCells + 1)
    Links = tuple(
        NodeValue for NodeValue in Children if NodeValue.get("tag") == "XLinks"
    )
    if len(Links) > 1 or any(
        NodeValue.get("tag") not in {"Cell", "XLinks"} for NodeValue in Children
    ):
        raise ValueError("cell_group_scope")
    if Links:
        Fields = Links[0].get("attributes")
        if (
            not IsPayloadMap(Fields)
            or Fields.get("count") != "0"
            or Links[0].get("children")
            or Links[0].get("text")
        ):
            raise ValueError("external_links")
    Cells = tuple(NodeValue for NodeValue in Children if NodeValue.get("tag") == "Cell")
    Fields = Group.get("attributes")
    Count = Fields.get("Count") if IsPayloadMap(Fields) else None
    if (
        not isinstance(Count, str)
        or not 1 <= len(Count) <= 4
        or not Count.isascii()
        or not Count.isdigit()
        or int(Count) != len(Cells)
    ):
        raise ValueError("cells_count")
    return Cells


# duplicate native addresses or aliases invalidate the whole sheet rather than selecting one row
def ReadOneSheet(
    SheetName: str, Cells: tuple[Mapping[str, object], ...]
) -> tuple[dict[tuple[str, str], Parameter], tuple[str, ...]]:
    Fields = tuple(CellValue.get("attributes") for CellValue in Cells)
    if any(not IsPayloadMap(Field) for Field in Fields):
        raise ValueError("cell_shape")
    CellRows = tuple(CastValue(Mapping[str, object], Field) for Field in Fields)
    Addresses = tuple(CellRow.get("address") for CellRow in CellRows)
    Aliases = tuple(
        CellRow.get("alias") for CellRow in CellRows if CellRow.get("alias")
    )
    if (
        any(
            not isinstance(Address, str) or not KCellAddress.fullmatch(Address)
            for Address in Addresses
        )
        or len(set(Addresses)) != len(Addresses)
        or any(
            not isinstance(Alias, str)
            or not KAliasName.fullmatch(Alias)
            or KCellAddress.fullmatch(Alias)
            or Alias in KFormulaUnits
            or Alias.casefold() in {"pi", "e", "true", "false"}
            for Alias in Aliases
        )
        or len(set(Aliases)) != len(Aliases)
    ):
        raise ValueError("ambiguous_cells")
    Result: dict[tuple[str, str], Parameter] = {}
    Issues: list[str] = []
    for CellRow in CellRows:
        Alias, Address, Content = (
            CellRow.get("alias"),
            CellRow.get("address"),
            CellRow.get("content"),
        )
        if not isinstance(Alias, str) or not Alias:
            continue
        Value = ReadLiteral(Content) if isinstance(Content, str) else None
        if Value is None:
            Issues.append("unsupported_literal")
            continue
        Result[SheetName, Alias] = Parameter(
            f"freecad:parameter:{SheetName}:cell:{Address}",
            f"{SheetName}.{Alias}",
            Value,
            owner_id=f"freecad:object:{SheetName}",
            attributes={
                "freecad_sheet": SheetName,
                "freecad_cell": Address,
                "freecad_alias": Alias,
            },
        )
    return Result, tuple(Issues)


# actual native sheet objects supply bounded alias scope independently from embedded kit snapshots
def ReadSheet(
    Document: CadDocument,
) -> tuple[dict[tuple[str, str], Parameter], tuple[str, ...]]:
    Native = Document.metadata.get("freecad")
    if not IsPayloadMap(Native):
        return {}, ()
    Objects = ReadNodes(Native.get("objects", ()), 16384)
    Sheets = tuple(
        Value for Value in Objects if Value.get("type_id") == "Spreadsheet::Sheet"
    )
    if len(Sheets) > 64:
        raise OverflowError("sheet_limit")
    Names = Counter(
        SheetName
        for Value in Objects
        if isinstance(SheetName := Value.get("name"), str)
    )
    Aliases: dict[tuple[str, str], Parameter] = {}
    Issues: list[str] = []
    CellCount = 0
    for Sheet in Sheets:
        SheetName = Sheet.get("name")
        if (
            not isinstance(SheetName, str)
            or not KAliasName.fullmatch(SheetName)
            or Names[SheetName] != 1
        ):
            Issues.append("ambiguous_sheet")
            continue
        try:
            Cells = ReadCells(Sheet)
            CellCount += len(Cells)
            if CellCount > KMaxCells:
                raise OverflowError("cell_limit")
            Values, Findings = ReadOneSheet(SheetName, Cells)
        except ValueError as Problem:
            Issues.append(str(Problem))
            continue
        Aliases.update(Values)
        Issues.extend(Findings)
    return Aliases, tuple(Issues)
