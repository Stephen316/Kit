from json import loads as ReadJson
from collections import Counter
from math import isclose as IsClose
from math import pi as KHalfTurn
from struct import unpack_from as UnpackFrom
from uuid import UUID

from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import AuthorDwg
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    PlanDimension,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.TextMetrics import (
    TextExtent,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import PlanBorder
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.TitlePlan import PlanTitle
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.HoleData import HoleData
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.TableVocab import (
    KLayerSpecs,
    KLinetypeSpecs,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderPlan import (
    PlanHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewRepData import (
    BodyPath,
    GuidItems,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewState import ViewState
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile
from tests.convert.formats.FusionCodec.Drawings.DwgAuthorTests import (
    FieldsOf,
    KSource,
    KViews,
    MakeDraft,
)

KGuidText = "0f0e0d0c-0b0a-4908-8706-050403020100"


def TestSheetSizes() -> None:
    Expected = {
        "A4 Portrait": (210.0, 297.0, True),
        "A4 Landscape": (297.0, 210.0, True),
        "A3 Landscape": (420.0, 297.0, True),
        "A2 Landscape": (594.0, 420.0, True),
        "A1 Landscape": (841.0, 594.0, True),
        "A0 Landscape": (1189.0, 841.0, True),
        "B Landscape": (17.0 * 25.4, 11.0 * 25.4, False),
        "A Portrait": (8.5 * 25.4, 11.0 * 25.4, False),
        "E Landscape": (44.0 * 25.4, 34.0 * 25.4, False),
    }
    for SizeName, (Across, Upward, Metric) in Expected.items():
        Paper = SheetSize(SizeName)
        assert IsClose(Paper.PaperWidth, Across) and IsClose(Paper.PaperHeight, Upward)
        assert Paper.IsMetric == Metric
    Paper = SheetSize("A3 Landscape")
    assert Paper.MediaName == "ISO_full_bleed_A3_(420.00_x_297.00_MM)"
    Paper = SheetSize("B Landscape")
    assert Paper.MediaName == "ANSI_full_bleed_B_(17.00_x_11.00_Inches)"
    assert (Paper.FrameMargin, Paper.TitleCorner) == (
        12.7,
        (Paper.PaperWidth - 12.7, 12.7),
    )
    for SizeName in ("A5 Portrait", "A3", "B Sideways"):
        with ExpectError(ValueError, match="unsupported"):
            _ = SheetSize(SizeName)


def TestBorderPlan() -> None:
    Border = PlanBorder(SheetSize("A3 Landscape"))
    assert Border.BlockName == "ISO_A3_SHEET"
    assert len(Border.FrameLines) + len(Border.TrimLines) + len(Border.MarkLines) == 36
    assert len(Border.Labels) == 28
    assert ((20.0, 10.0), (410.0, 10.0)) in Border.FrameLines
    Levels = sorted(
        {Segment[0][1] for Segment in Border.MarkLines if Segment[0][0] == 15.0}
    )
    Saved = [52.83334, 100.66667, 148.5, 196.33333, 244.16666]
    assert all(
        IsClose(Planned, Recorded, abs_tol=1e-4)
        for Planned, Recorded in zip(Levels, Saved)
    )
    Labels = {(Label.TextValue, Label.Centre[0]): Label for Label in Border.Labels}
    Corner = Labels[("A", 17.5)]
    assert IsClose(Corner.Centre[1], 268.08333, abs_tol=1e-4)
    assert IsClose(Corner.Insertion[0], 17.5 - 2.5 * 683 / 1466)
    assert IsClose(Corner.Insertion[1], Corner.Centre[1] - 1.25)
    for SizeName, LineCount, LabelCount, Letters in (
        ("A1 Landscape", 64, 56, "ABCDEFGHIJKL"),
        ("A0 Landscape", 88, 80, "ABCDEFGHIJKLMNOP"),
    ):
        Large = PlanBorder(SheetSize(SizeName))
        Total = len(Large.FrameLines) + len(Large.TrimLines) + len(Large.MarkLines)
        assert (Total, len(Large.Labels)) == (LineCount, LabelCount)
        Found = sorted(
            {Label.TextValue for Label in Large.Labels if Label.TextValue.isalpha()}
        )
        assert "".join(Found) == Letters


def TestAsmeBorder() -> None:
    Border = PlanBorder(SheetSize("B Landscape"))
    assert Border.BlockName == "ASME_B_SHEET" and Border.TrimLines == ()
    Lower = Border.FrameLines[0]
    assert IsClose(Lower[0][0], 12.7) and IsClose(Lower[1][0], 431.8 - 12.7)
    Ticks = sorted(
        {
            round(Segment[0][0], 6)
            for Segment in Border.MarkLines
            if Segment[0][0] == Segment[1][0]
        }
    )
    assert Ticks == [round(Quarter * 4.25 * 25.4, 6) for Quarter in (1, 2, 3)]
    Numbers = sorted(
        (Label.Centre[0], Label.TextValue)
        for Label in Border.Labels
        if Label.TextValue.isdigit()
    )
    assert [TextValue for _, TextValue in Numbers[::2]] == ["4", "3", "2", "1"]
    Letters = sorted(
        (Label.Centre[1], Label.TextValue)
        for Label in Border.Labels
        if Label.TextValue.isalpha()
    )
    assert [TextValue for _, TextValue in Letters[::2]] == ["A", "B"]
    assert {Label.TextHeight for Label in Border.Labels} == {0.12 * 25.4}
    for SizeName, ColumnTotal, RowTotal in (
        ("A Portrait", 2, 2),
        ("C Landscape", 4, 4),
        ("D Landscape", 8, 4),
        ("E Landscape", 8, 8),
    ):
        Large = PlanBorder(SheetSize(SizeName))
        Found = {Label.TextValue for Label in Large.Labels}
        assert len(Found) == ColumnTotal + RowTotal and len(Large.Labels) == 2 * len(
            Found
        )


def TestHeaderPlan() -> None:
    Values = dict(PlanHeader(SheetSize("A1 Landscape")).DraftFields)
    assert Values["PLimMax"] == (841.0, 594.0)
    assert Values["PExtMax"] == (841.0, 594.0, 0.0)
    assert (Values["DimExo"], Values["DimGap"], Values["DimDli"]) == (2.1, 1.4, 10.5)
    assert Values["DimTFac"] == 2.5 / 3.5
    assert Values["PackedFlags"] == 10781
    assert Values["TdCreateDay"] == 0 and Values["HandSeed"] == DwgHandleRef(0, 0)
    Model = ReadDwgFile(AuthorDwg(MakeDraft(KViews, ())))
    Header = {
        Entry.FieldName: Entry.FieldValue for Entry in Model.HeaderVars.RecordFields
    }
    assert len(Header) == len(Values)
    assert Header["PLimMax"] == (420.0, 297.0)
    assert Header["InsUnits"] == 4


def TestTableVocab() -> None:
    Layers = {Layer.EntryName: Layer.LayerValues for Layer in KLayerSpecs}
    assert (Layers["Visible"], Layers["Hidden"], Layers["TITLEBLOCK"]) == (
        368,
        240,
        304,
    )
    assert (Layers["0"], Layers["Defpoints"]) == (1008, 992)
    Strokes = {Entry.EntryName: Entry.Dashes for Entry in KLinetypeSpecs}
    Lengths = {Entry.EntryName: Entry.PatternLength for Entry in KLinetypeSpecs}
    assert (Lengths["CENTER2"], Lengths["HIDDEN2"]) == (28.575, 3.175 + 1.5875)
    for NameText, Expected in (
        ("CENTER2", (19.05, -3.175, 3.175, -3.175)),
        ("HIDDEN2", (3.175, -1.5875)),
    ):
        assert len(Strokes[NameText]) == len(Expected)
        assert Strokes[NameText] == Expected


def TestTitlePlan() -> None:
    Title = PlanTitle()
    FieldTags = [Field.Tag for Field in Title.Fields]
    assert len(FieldTags) == len(set(FieldTags)) == 15
    assert {"TITLE_1", "DRAWING_NUMBER", "SHEET", "REV"} <= set(FieldTags)
    Spans = [Segment[1][0] - Segment[0][0] for Segment in Title.Lines]
    assert -180.0 in Spans and 180.0 in Spans


def TestStandard() -> None:
    Model = ReadDwgFile(AuthorDwg(MakeDraft(KViews, ())))
    Kinds = Counter(Entry.ClassKind for Entry in Model.DwgObjects)
    for Missing in ("VISUALSTYLE", "MLEADERSTYLE", "TABLESTYLE", "DICTIONARYVAR"):
        assert Kinds[Missing] == 0
    Classes = {Entry.DxfName for Entry in Model.ClassTable.ClassRows}
    assert Classes <= set(Kinds)
    assert {"LAYOUT", "MATERIAL", "ACDBVIEWREP"} <= Classes
    assert Kinds["LAYER"] == len(KLayerSpecs)
    assert Kinds["LTYPE"] == len(KLinetypeSpecs)


def TestTextExtent() -> None:
    Height, Width = TextExtent("40", 3.5)
    assert IsClose(Height, 3.5 * 1497 / 1466)
    assert IsClose(Width, 3.5 * 2154 / 1466)
    Height, Width = TextExtent("7", 2.5)
    assert IsClose(Height, 2.5)
    assert IsClose(Width, 2.5 * 949 / 1466)
    with ExpectError(ValueError, match="metrics"):
        _ = TextExtent("40€", 3.5)
    Saved = {"10": 1957, "3.54": 3801, "R2.5": 4083, "∅5": 2567}
    for TextValue, Units in Saved.items():
        assert IsClose(TextExtent(TextValue, 3.5)[1], 3.5 * Units / 1466)
    assert TextExtent("∅5", 3.5) == TextExtent("Ø5", 3.5)


def TestBodyPath() -> None:
    PathIds = [Entry.DraftFields[0][1] for Entry in BodyPath(KSource)]
    assert PathIds == [0x1C5, 0x1C5]
    Nested = ViewSource(0x2A, "1_Component", KGuidText, (0, 0, 0), (1, 1, 1), "", (7,))
    assert [Entry.DraftFields[0][1] for Entry in BodyPath(Nested)] == [7, 0x2A, 0x2A]
    Items = dict(GuidItems(KGuidText))
    Parsed = UUID(KGuidText)
    assert Items["GuidHead"] == Parsed.fields[0]
    assert Items["GuidTail"] == Parsed.bytes[8:]


def TestViewState() -> None:
    Bodies = (
        (KGuidText, (-1.0, 0.0, 0.5), (4.0, 2.0, 1.5)),
        ("11111111-2222-4333-8444-555555555555", (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
    )
    Single = ViewState((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), Bodies[:1])
    Double = ViewState((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), Bodies)
    assert len(Single) == 219
    assert len(Double) == 306
    assert Single[90] == 1 and Double[90] == 2
    assert UnpackFrom("<q", Single, 100)[0] == 2
    assert UUID(bytes_le=Single[108:124]) == UUID(KGuidText)
    assert UnpackFrom("<3d", Single, 124) == (-1.0, 0.0, 0.5)
    assert UnpackFrom("<q", Double, 187)[0] == 3


def TestDimKinds() -> None:
    Drafts = (
        DimensionDraft((100.0, 80.0), (160.0, 80.0), 95.0),
        DimensionDraft((100.0, 80.0), (100.0, 120.0), 80.0, 1.0, "Vertical"),
        DimensionDraft((100.0, 80.0), (140.0, 110.0), 12.0, 1.0, "Aligned"),
        DimensionDraft((200.0, 100.0), (210.0, 100.0), 8.0, 2.0, "Radius"),
        DimensionDraft((200.0, 100.0), (220.0, 100.0), 8.0, 2.0, "Diameter"),
    )
    Plans = [PlanDimension(Draft) for Draft in Drafts]
    assert [EachPlan.TextValue for EachPlan in Plans] == ["60", "40", "50", "R5", "∅10"]
    assert IsClose(Plans[1].TextAngle, KHalfTurn / 2)
    assert Plans[1].TextPoint[0] < 80.0
    assert IsClose(Plans[2].Measurement, 50.0)
    Model = ReadDwgFile(AuthorDwg(MakeDraft(KViews, Drafts)))
    Counts = Counter(Entry.ClassKind for Entry in Model.DwgObjects)
    assert Counts["DIMENSION_LINEAR"] == 2
    assert Counts["DIMENSION_ALIGNED"] == 1
    assert Counts["DIMENSION_RADIUS"] == 1
    assert Counts["DIMENSION_DIAMETER"] == 1
    Styles = {
        Entry.ClassKind: [
            Member.FieldValue for Member in Entry.EedBlocks[0].EedItems.RecordFields
        ]
        for Entry in Model.DwgObjects
        if Entry.ClassKind.startswith("DIMENSION")
    }
    assert Styles["DIMENSION_RADIUS"][4:8] == [75, 1, 288, 1]
    assert Styles["DIMENSION_DIAMETER"][4:6] == [288, 1]
    assert len(Styles["DIMENSION_ALIGNED"]) == 5
    Rounds = FieldsOf(Model, "DIMENSION_RADIUS") + FieldsOf(Model, "DIMENSION_DIAMETER")
    assert {Fields["DimFlags"] for Fields in Rounds} == {10}
    assert {Fields["DimFlags"] for Fields in FieldsOf(Model, "DIMENSION_ALIGNED")} == {
        11
    }
    with ExpectError(ValueError, match="unsupported"):
        _ = PlanDimension(DimensionDraft((0.0, 0.0), (10.0, 0.0), 5.0, 1.0, "Arc"))


def IsNearPoint(Planned: tuple[float, float], Recorded: tuple[float, float]) -> bool:
    return all(
        IsClose(Value, Saved, abs_tol=1e-5) for Value, Saved in zip(Planned, Recorded)
    )


def TestShortDims() -> None:
    Saved = (
        ((92.5, 174.14), (97.5, 179.14), 10.5, 2.0, 5, (103.421803, 199.911045)),
        ((137.8, 105.5), (142.8, 110.5), 0.0, 2.0, 3, (156.146424, 123.846423)),
        ((122.975, 282.05), (115.5, 289.525), -10.5, 2.99, 4, (112.053071, 307.821171)),
        (
            (452.135, 280.35),
            (460.46, 288.675),
            -10.5,
            3.33,
            4,
            (478.756172, 292.121929),
        ),
    )
    Texts = (
        (96.969067, 197.967104),
        (149.693689, 121.902483),
        (118.505806, 305.87723),
        (472.303436, 290.177988),
    )
    for (First, Second, Height, Scale, Count, LineEnd), TextPoint in zip(Saved, Texts):
        Planned = PlanDimension(DimensionDraft(First, Second, Height, Scale, "Aligned"))
        assert Planned.TextValue == "3.54" and len(Planned.Lines) == Count
        assert any(IsNearPoint(Segment[1], LineEnd) for Segment in Planned.Lines)
        assert IsNearPoint(Planned.TextPoint, TextPoint)
    Split = PlanDimension(
        DimensionDraft((122.975, 282.05), (115.5, 289.525), -10.5, 2.99, "Aligned")
    )
    assert IsNearPoint(Split.Arrows[0][0], (128.337226, 292.361974))
    Flank = PlanDimension(
        DimensionDraft(
            (418.624995, 449.250009),
            (418.624995, 441.749991),
            408.124995,
            0.75,
            "Vertical",
        )
    )
    assert Flank.TextValue == "10" and len(Flank.Lines) == 5
    assert IsNearPoint(Flank.Lines[3][1], (408.124995, 434.749991))
    assert IsNearPoint(Flank.TextPoint, (404.93799, 445.5))
    Inside = PlanDimension(
        DimensionDraft((92.5, 174.14), (112.5, 194.14), 10.5, 2.0, "Aligned")
    )
    assert len(Inside.Lines) == 3
    with ExpectError(ValueError, match="overlaps"):
        _ = PlanDimension(
            DimensionDraft((92.5, 174.14), (97.5, 179.14), 1.0, 2.0, "Aligned")
        )


def TestViewAxes() -> None:
    Corner = 3**-0.5
    Slanted = ViewDraft((180.0, 120.0), 1.0, (-Corner, -Corner, -Corner))
    with ExpectError(ValueError, match="model axis"):
        _ = AuthorDwg(MakeDraft((Slanted,), ()))
    Sideways = ViewDraft((180.0, 120.0), 1.0, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    assert ReadDwgFile(AuthorDwg(MakeDraft((Sideways,), ())))


def TestHoleData() -> None:
    TextValue = HoleData(453)
    Parsed = ReadJson(TextValue)
    assert Parsed["BodyInfos"][0]["bodyId"] == 453
    assert Parsed["BodyInfos"][0]["ComponentOccurencePaths"] == [None]
    assert Parsed["FeatureSets"] == [{"Features": None, "LocalModifiers": None}]
    assert TextValue.startswith('{\n\t"BodyInfos" : \n\t[\n\t\t{\n')
    assert TextValue.endswith('\n\t"IdenticalFeatures" : null\n}')
