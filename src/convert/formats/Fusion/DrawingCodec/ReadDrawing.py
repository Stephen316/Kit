from collections.abc import Callable

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DrawingCodec.Manifest.ReadAsset import ReadAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ReadRoot import ReadRoot
from convert.formats.Fusion.DrawingCodec.Model.CheckDatabase import CheckDatabase
from convert.formats.Fusion.DrawingCodec.Model.CheckJoins import CheckJoins
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.formats.Fusion.DrawingCodec.Model.DrawingFolders import (
    ActivePrefix,
    DrawingFolders,
)
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KAssetManifest,
    KDatabaseFolder,
    KImageFolders,
    KPropertiesName,
    KRedirectName,
    KReferenceName,
    KRootManifest,
    KSettingsFolder,
    KSheetName,
)
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Package.ReadPackage import ReadPackage
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.PropertyCodec import ReadProperties
from convert.formats.Fusion.DrawingCodec.Members.ReadJsonPart import ReadJsonPart
from convert.formats.Fusion.DrawingCodec.Members.RedirectCodec import ReadRedirects
from convert.formats.Fusion.DrawingCodec.Members.SheetCodec import ReadSheet
from convert.formats.Fusion.DrawingCodec.Segments.ReadSegments import ReadSegmentsMut


def ReadDrawing(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionDrawing:
    Package = ReadPackage(DataValue, InflateZstd)
    Layout = tuple(PackageSlot(Entry.Name, Entry.Layout) for Entry in Package.Entries)
    Files = {
        Entry.Name: Entry.Payload
        for Entry in Package.Entries
        if not Entry.Name.endswith("/")
    }
    RootValue = ReadRoot(TakeMemberMut(Files, KRootManifest))
    Prefix = ActivePrefix(RootValue)
    if any(
        SlotValue.Name.endswith("/") and not SlotValue.Name.startswith(Prefix)
        for SlotValue in Layout
    ):
        raise ValueError("Fusion drawing directory lies outside the active asset")
    Active = {
        NameValue.removeprefix(Prefix): Files.pop(NameValue)
        for NameValue in tuple(Files)
        if NameValue.startswith(Prefix)
    }
    Asset = ReadAsset(TakeMemberMut(Active, KAssetManifest))
    Segments = ReadSegmentsMut(Asset, DrawingFolders(Asset.Segments), Active)
    Database = TakeDatabaseMut(Active)
    CheckJoins(RootValue, Asset, Database)
    CheckDatabase(Segments, Database)
    Result = FusionDrawing(
        RootValue,
        Asset,
        Segments,
        Database,
        ReadSheet(Active.pop(KSheetName)) if KSheetName in Active else None,
        TakeSettingsMut(Active),
        TakeImagesMut(Active),
        (
            ReadProperties(Files.pop(KPropertiesName))
            if KPropertiesName in Files
            else None
        ),
        (
            ReadJsonPart(KReferenceName, Files.pop(KReferenceName))
            if KReferenceName in Files
            else None
        ),
        ReadRedirects(Files.pop(KRedirectName)) if KRedirectName in Files else None,
        Layout,
    )
    if Files or Active:
        raise ValueError("Unaccounted Fusion drawing archive members")
    return Result


def TakeMemberMut(Members: dict[str, bytes], NameValue: str) -> bytes:
    Payload = Members.pop(NameValue, None)
    if Payload is None:
        raise ValueError("Missing Fusion drawing member " + NameValue)
    return Payload


def TakeDatabaseMut(Active: dict[str, bytes]) -> DrawingDatabase | None:
    Names = tuple(
        NameValue for NameValue in Active if NameValue.startswith(KDatabaseFolder)
    )
    if len(Names) > 1:
        raise ValueError("Fusion drawings carry at most one embedded database")
    if not Names:
        return None
    return DrawingDatabase(Names[0].removeprefix(KDatabaseFolder), Active.pop(Names[0]))


def TakeSettingsMut(Active: dict[str, bytes]) -> tuple[JsonPart, ...]:
    Names = tuple(
        NameValue
        for NameValue in Active
        if NameValue.startswith(KSettingsFolder)
        and NameValue.endswith(".json")
        and NameValue.count("/") == 1
    )
    return tuple(ReadJsonPart(NameValue, Active.pop(NameValue)) for NameValue in Names)


def TakeImagesMut(Active: dict[str, bytes]) -> tuple[ContainerPart, ...]:
    Names = tuple(
        NameValue
        for NameValue in Active
        if NameValue.startswith(KImageFolders)
        and NameValue.endswith(".png")
        and NameValue.count("/") == 1
    )
    return tuple(ContainerPart(NameValue, Active.pop(NameValue)) for NameValue in Names)
