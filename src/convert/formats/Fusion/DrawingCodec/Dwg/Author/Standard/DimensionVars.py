from math import pi as KHalfTurn
from re import findall as FindAll

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullHard,
    HardPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KTextHeight,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderDefaults import (
    KByBlockColor,
    KDefaultWeight,
    KVarGroup,
)

from convert.formats.Fusion.DrawingCodec.Dwg.Objects.StyleSpecs import KStyleSpecs

KFieldPattern = r"\b(TU|BD|BS|B|RC|CMC|H)\s+(\w+)"
KColourParts = ("Index", "Rgb", "Flags")
KLetterSizes = (1.8, 2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 20.0)
KMillimetreInch = 25.4
KExtensionTenths = 6
KLabelTenths = 4
KRowTenths = 30
KToleranceStep = 0.1
KZeroTrim = 12
KAngleTrim = 3
KDecimalPoint = ord(".")

KDimFormatVars: KVarGroup = {
    "DimADec": 2,
    "DimDec": 2,
    "DimTDec": 2,
    "DimAltU": 2,
    "DimAltTd": 2,
    "DimAUnit": 0,
    "DimFrac": 0,
    "DimLUnit": 2,
    "DimDSep": KDecimalPoint,
    "DimTMove": 0,
    "DimJust": 0,
    "DimSdOne": 0,
    "DimSdTwo": 0,
    "DimTolJ": 0,
    "DimTZin": KZeroTrim,
    "DimAltZ": KZeroTrim,
    "DimAltTz": KZeroTrim,
    "DimUpt": 0,
    "DimAtFit": 3,
    "DimFxlOn": 0,
    "DimTxtDirection": 0,
    "DimAltMzf": 100.0,
    "DimAltMzs": "",
    "DimMzf": 100.0,
    "DimMzs": "",
}


def SmallerLetter(TextHeight: float) -> float:
    Smaller = [Lettering for Lettering in KLetterSizes if Lettering < TextHeight]
    if not Smaller:
        raise ValueError(f"Authored DWG text height {TextHeight} has no smaller size")
    return Smaller[-1]


def ColourVars(Prefix: str) -> KVarGroup:
    return {
        Prefix + "Index": 0,
        Prefix + "Rgb": KByBlockColor,
        Prefix + "Flags": 0,
    }


def DimSizeVars(TextHeight: float) -> KVarGroup:
    return {
        "DimPost": "",
        "DimAPost": "",
        "DimScale": 1.0,
        "DimAsz": TextHeight,
        "DimExo": TextHeight * KExtensionTenths / 10,
        "DimDli": TextHeight * KRowTenths / 10,
        "DimExe": TextHeight * KExtensionTenths / 10,
        "DimRnd": 0.0,
        "DimDle": 0.0,
        "DimTp": KToleranceStep,
        "DimTm": KToleranceStep,
        "DimFxl": 1.0,
        "DimJogAng": KHalfTurn / 4,
        "DimTFill": 0,
        **ColourVars("DimTFillClr"),
    }


def DimFlagVars(TextHeight: float) -> KVarGroup:
    return {
        "DimTol": 0,
        "DimLim": 0,
        "DimTih": 0,
        "DimToh": 0,
        "DimSeOne": 0,
        "DimSeTwo": 0,
        "DimTad": 1,
        "DimZin": KZeroTrim,
        "DimAZin": KAngleTrim,
        "DimArcSym": 0,
        "DimTxt": TextHeight,
        "DimCen": 0.0,
        "DimTsz": 0.0,
        "DimAltF": 1 / KMillimetreInch,
        "DimLFac": 1.0,
        "DimTvp": 0.0,
        "DimTFac": SmallerLetter(TextHeight) / TextHeight,
        "DimGap": TextHeight * KLabelTenths / 10,
    }


def DimAltVars() -> KVarGroup:
    return {
        "DimAltRnd": 0.0,
        "DimAlt": 0,
        "DimAltD": 2,
        "DimTofl": 1,
        "DimSah": 0,
        "DimTix": 0,
        "DimSoxd": 0,
        **ColourVars("DimClrD"),
        **ColourVars("DimClrE"),
        **ColourVars("DimClrT"),
    }


def DimLinkVars(StyleKey: str) -> KVarGroup:
    Blanks = (
        "DimLdrBlkHandle",
        "DimBlkHandle",
        "DimBlkOneHandle",
        "DimBlkTwoHandle",
        "DimLtypeHandle",
        "DimLtExOneHandle",
        "DimLtExTwoHandle",
    )
    return {
        "DimTxStyHandle": HardPointer(StyleKey),
        **{FieldName: KNullHard for FieldName in Blanks},
        "DimLwd": KDefaultWeight,
        "DimLwe": KDefaultWeight,
    }


def DimensionVars(TextHeight: float, StyleKey: str) -> KVarGroup:
    return {
        **DimSizeVars(TextHeight),
        **DimFlagVars(TextHeight),
        **DimAltVars(),
        **KDimFormatVars,
        **DimLinkVars(StyleKey),
    }


def StyleNames() -> tuple[str, ...]:
    Names: list[str] = []
    for SpecKind, FieldName in FindAll(KFieldPattern, KStyleSpecs["DIMSTYLE"]):
        Names.extend(
            FieldName + Suffix
            for Suffix in (KColourParts if SpecKind == "CMC" else ("",))
        )
    return tuple(Names[Names.index("DimPost") : Names.index("DimMzSuffix") + 1])


def StyleVars() -> KVarGroup:
    Values = list(DimensionVars(KTextHeight, "").values())
    Named: KVarGroup = dict(zip(StyleNames(), Values))
    Blanks = (
        "DimLeaderBlock",
        "DimBlock",
        "DimBlockOne",
        "DimBlockTwo",
        "DimLtype",
        "DimExtLtypeOne",
        "DimExtLtypeTwo",
    )
    return {
        **Named,
        "DimLineWeight": KDefaultWeight,
        "DimExtWeight": KDefaultWeight,
        "UnknownFlag": 0,
        **{FieldName: KNullHard for FieldName in Blanks},
    }
