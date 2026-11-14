from re import fullmatch as MatchText
from typing import cast as CastValue
from uuid import UUID as ParseUuid

from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingIdentity import (
    DrawingIdentity,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase

KTokenPattern = r"[A-Za-z0-9_-]{22}"

KDatabasePattern = r"ExtFile\.(.+)\.dwg"


def CheckSpec(SpecValue: DrawingSpec, Database: DrawingDatabase) -> None:
    if not isinstance(CastValue(object, SpecValue), DrawingSpec) or not isinstance(
        CastValue(object, Database), DrawingDatabase
    ):
        raise ValueError("Expected a typed drawing spec and drawing database")
    CheckSheet(SpecValue.Sheet, SpecValue.LayoutHandle)
    CheckIdentity(SpecValue.Identity)
    CheckDesign(SpecValue.Design)
    Found = MatchText(KDatabasePattern, Database.FileName)
    if Found is None or not IsGuid(Found.group(1)):
        raise ValueError("Drawing database name must be ExtFile.<guid>.dwg")
    if not IsName(SpecValue.DrawingName) or type(SpecValue.AutoDimension) is not bool:
        raise ValueError("Invalid drawing name or dimension switch")
    if SpecValue.History is not None:
        CheckHistory(SpecValue.History)


def CheckSheet(Sheet: SheetSpec, LayoutHandle: int) -> None:
    if not isinstance(CastValue(object, Sheet), SheetSpec) or not IsName(
        Sheet.SheetName
    ):
        raise ValueError("Invalid drawing sheet")
    if type(Sheet.SheetSize) is not str:
        raise ValueError("Unsupported drawing sheet size " + repr(Sheet.SheetSize))
    if Sheet.Standard != SheetSize(Sheet.SheetSize).StandardName:
        raise ValueError("Unsupported drawing standard " + repr(Sheet.Standard))
    if type(LayoutHandle) is not int or not 0 < LayoutHandle <= 0xFFFFFFFF:
        raise ValueError("Invalid drawing layout handle")


def CheckIdentity(Identity: DrawingIdentity) -> None:
    if not isinstance(CastValue(object, Identity), DrawingIdentity):
        raise ValueError("Expected a typed drawing identity")
    Guids = (
        Identity.DocumentId,
        Identity.VersionId,
        Identity.AssetId,
        Identity.RevisionId,
        Identity.LinkRole,
        Identity.ComponentGuid,
        Identity.ComponentRevision,
        Identity.InstanceGuid,
        Identity.DrawingFile,
        Identity.DesignFile,
    )
    if not all(IsGuid(TextValue) for TextValue in Guids):
        raise ValueError("Drawing identities must be canonical lowercase GUIDs")
    if not all(
        IsToken(TextValue)
        for TextValue in (Identity.DrawingToken, Identity.DesignToken)
    ):
        raise ValueError("Drawing lineage tokens must be 22 urlsafe characters")


def CheckDesign(Design: DesignTarget) -> None:
    if not isinstance(CastValue(object, Design), DesignTarget):
        raise ValueError("Expected a typed design target")
    Guids = (
        Design.AssetId,
        Design.SnapshotId,
        Design.ChangeGuid,
        Design.ComponentGuid,
        Design.BodyPersistentId,
    )
    Numbers = (
        Design.InstanceId,
        Design.ComponentId,
        Design.BodiesId,
        Design.SketchesId,
        Design.BodyVersion,
        Design.DesignVersion,
    )
    if not all(IsGuid(TextValue) for TextValue in Guids):
        raise ValueError("Design identities must be canonical lowercase GUIDs")
    if not IsName(Design.DisplayName) or not all(
        type(Number) is int and Number > 0 for Number in Numbers
    ):
        raise ValueError("Invalid design name or object identity")


def CheckHistory(History: SaveState) -> None:
    if not isinstance(CastValue(object, History), SaveState):
        raise ValueError("Expected a typed drawing save state")
    if not all(IsGuid(TextValue) for TextValue in History.PriorVersions):
        raise ValueError("Prior drawing versions must be canonical lowercase GUIDs")
    if not all(
        type(Channel) is float and 0.0 <= Channel <= 1.0
        for Channel in History.CycleColor
    ):
        raise ValueError("Drawing component colour channels must lie in [0, 1]")
    if type(History.CacheFolder) is not str or type(History.SaveLabel) is not str:
        raise ValueError("Invalid drawing save label or cache folder")


def IsGuid(TextValue: str) -> bool:
    if type(TextValue) is not str:
        return False
    try:
        return str(ParseUuid(TextValue)) == TextValue
    except ValueError:
        return False


def IsToken(TextValue: str) -> bool:
    return type(TextValue) is str and MatchText(KTokenPattern, TextValue) is not None


def IsName(TextValue: str) -> bool:
    return type(TextValue) is str and bool(TextValue) and "/" not in TextValue
