from dataclasses import dataclass as Dataclass

from DefinitionFragment import EncodeDefinitionFragment
from DefinitionOptions import KDefinitionOptionsGeneration
from JournalAttach import JournalAttach
from convert.adapters.solidworks.Container.Archive import KLongStringLimit
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import (
    KJournalClass,
    KLineFontBindings,
    KViewBlockDoubles,
    ArchiveWriter,
    EncodePreamble,
    LineFontBinding,
    ViewRecord,
    WriteBomManager,
    WriteDrafting,
    WriteLineFonts,
    WriteLineStyles,
    WriteUserModel,
)

# the measured modern user environment has its own session and window fields
KSessionWords = (1, 1, 792, 10, 1520, 10, 0, 0)

# the primary window has two coordinates six short fields and a signed sentinel
KPrimaryPlacement = (1519, 227, 2, 1, 0, 764, 227, 10, -1)

# the modern environment tail carries the build stamp of the supported profile
KBuildStamp = 90165


# the document supplies the independently owned view and environment settings
@Dataclass(frozen=True, slots=True)
class DefinitionFields:
    UserName: str
    PreambleView: tuple[float, ...] | None
    Camera: tuple[float, float, float, float]
    Views: tuple[ViewRecord, ViewRecord, ViewRecord]
    Attachment: JournalAttach
    AppearanceCounter: int
    TerminalValue: float
    Bindings: tuple[LineFontBinding, ...]


def EncodePartDefinition(Fields: DefinitionFields) -> bytes:
    return EncodeModernPartDefinition(
        UserName=Fields.UserName,
        PreambleView=Fields.PreambleView,
        Camera=Fields.Camera,
        Views=Fields.Views,
        Attachment=Fields.Attachment,
        AppearanceCounter=Fields.AppearanceCounter,
        TerminalValue=Fields.TerminalValue,
        Bindings=Fields.Bindings,
    )


# untagged window placement and fixed view widths determine the next archive class
def RequireViews(Views: tuple[ViewRecord, ViewRecord, ViewRecord]) -> None:
    RequireArch(
        tuple(View.has_window_placement for View in Views),
        (True, False, False),
        "Definition view placement ownership",
    )
    RequireArch(
        all(
            len(View.rotation) in (0, KViewBlockDoubles)
            and len(View.translation) == len(View.centre) == 3
            for View in Views
        ),
        True,
        "Definition view field widths",
    )


# explicit user settings compose with the shared archive writer and modern journal
def EncodeModernPartDefinition(
    *,
    UserName: str,
    PreambleView: tuple[float, ...] | None,
    Camera: tuple[float, float, float, float],
    Views: tuple[ViewRecord, ViewRecord, ViewRecord],
    Attachment: JournalAttach,
    AppearanceCounter: int,
    TerminalValue: float,
    Bindings: tuple[LineFontBinding, ...] = KLineFontBindings,
) -> bytes:
    RequireViews(Views)
    RequireArch(
        (len(Bindings), set(Bindings)),
        (len(KLineFontBindings), set(KLineFontBindings)),
        "Definition line font bindings",
    )
    RequireArch(
        all(
            len(Text.encode("utf-16-le")) // 2 < KLongStringLimit
            for Text in (UserName, *(View.name for View in Views))
        ),
        True,
        "Definition environment string length fits the archive writer",
    )
    Writer = ArchiveWriter()
    WriteDrafting(Writer, "moBS_c")
    WriteLineStyles(Writer)
    WriteLineFonts(Writer, Bindings=Bindings)
    WriteUserModel(
        Writer,
        UserName,
        SessionWords=KSessionWords,
        ViewValues=Views,
        PlacementFields=KPrimaryPlacement,
        BuildStamp=KBuildStamp,
    )
    WriteBomManager(Writer)
    RequireArch(
        KJournalClass in Writer.classes, False, "first Definition journal class"
    )
    return (
        EncodePreamble(ViewValue=PreambleView, CameraValue=Camera)
        + Writer.build()
        + EncodeDefinitionFragment(
            KDefinitionOptionsGeneration, Attachment, AppearanceCounter, TerminalValue
        )
    )
