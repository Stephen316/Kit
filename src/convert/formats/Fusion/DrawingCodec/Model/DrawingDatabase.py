from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Header.EmitHeaderVars import (
    EmitHeaderVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import (
    FrameParts,
    KHeaderName,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile


# the loadable gate needs one place so no caller emits a database fusion rejects
def CheckLoadable(Database: "DrawingDatabase") -> None:
    Frame = dict(Database.Model.SectionVars).get(KHeaderName)
    if Frame is None or FrameParts(Frame)[0] < 72:
        raise ValueError(
            "Drawing databases need a header tail, so the database is refused"
        )
    Model = Database.Model
    if Model.HeaderBytes and (
        EmitHeaderVars(Model.HeaderVars, Frame, Model.FileHeader) != Model.HeaderBytes
    ):
        raise ValueError(
            "Drawing databases need a header that matches its tail, so the database is refused"
        )
    AppInfo = Database.Model.AppInfo
    if AppInfo is None:
        raise ValueError(
            "Drawing databases need an application entry, so the database is refused"
        )
    if any('name ="Kit"' in Entry.TextValue for Entry in AppInfo.AppEntries):
        raise ValueError(
            "Authored drawing databases cannot be made loadable, so the database is refused"
        )


# drawing database needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingDatabase:
    FileName: str
    Model: DwgFile

    # the database content needs a single derivation so a drawing never carries a second copy of the dwg bytes
    @property
    def Content(self) -> bytes:
        CheckLoadable(self)
        return EmitDwgFile(self.Model)
