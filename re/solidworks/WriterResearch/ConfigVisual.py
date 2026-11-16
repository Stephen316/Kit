from CmgrVisualPrefix import CmgrVisualFields, WriteCmgrVisualPrefix
from ColorAppearance import EncodeColorDspbr
from convert.adapters.solidworks.Config.RootLayout import KRootClass
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KNodeNameClass, KVisualClass
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# Both inline objects have independently selected presence in this visual profile.
def WriteConfigVisual(
    Writer: ArchiveWriter,
    Generation: int,
    Fields: CmgrVisualFields,
    *,
    RealViewPresent: bool,
    DspbrPresent: bool,
) -> None:
    RequireArch(
        (Writer.next_index, Writer.classes),
        (6, {KRootClass: 1, KNodeNameClass: 4}),
        "Config-0 visual allocation after the owned name",
    )
    RequireArch(
        RealViewPresent is True and DspbrPresent is True,
        True,
        "Config-0 populated RealView and DSPBR objects",
    )
    Body = ArchiveWriter()
    WriteCmgrVisualPrefix(Body, Generation, Fields)
    Body.raw(EncodeColorDspbr(Generation, Fields.SurfaceColor))
    Writer.BeginObject(KVisualClass, 1)
    Writer.raw(Body.build())
