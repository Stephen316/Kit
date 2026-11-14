from convert.formats.Fusion.DrawingCodec.Dwg.Image.EncodeMaps import EncodePageMap
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PackSections import PackOrPlan
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KPageMapType,
    KSectionMapType,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile

KSizeRounds = 8


def FitSize(Declared: int, Needed: int) -> int:
    Minimum = (Needed + 31) // 32 * 32
    return Declared if Declared >= Minimum else Minimum


def SizePages(
    DwgModel: DwgFile, Packed: dict[int, bytes], SectionMap: bytes
) -> tuple[dict[int, int], dict[int, tuple[bytes, bytes]]]:
    Sizes: dict[int, int] = {}
    Systems: dict[int, tuple[bytes, bytes]] = {}
    for PageImage in DwgModel.PageImages:
        Number = PageImage.PageNumber
        if PageImage.PageType == KDataPageType:
            Sizes[Number] = FitSize(PageImage.PageSize, len(Packed[Number]) + 32)
        elif PageImage.PageType == KSectionMapType:
            SystemPacked = PackOrPlan(SectionMap, PageImage.PackPlan)
            Systems[Number] = (SectionMap, SystemPacked)
            Sizes[Number] = FitSize(PageImage.PageSize, len(SystemPacked) + 40)
    MapImage = DwgModel.PageImages[-1]
    if MapImage.PageType != KPageMapType or len(Systems) != 1:
        raise ValueError("DWG pages need one section map and a final page map")
    Sizes[MapImage.PageNumber] = MapImage.PageSize
    for _ in range(KSizeRounds):
        MapRaw = EncodePageMap(DwgModel, Sizes)
        MapPacked = PackOrPlan(MapRaw, MapImage.PackPlan)
        Wanted = FitSize(Sizes[MapImage.PageNumber], len(MapPacked) + 40)
        if Wanted == Sizes[MapImage.PageNumber]:
            Systems[MapImage.PageNumber] = (MapRaw, MapPacked)
            return Sizes, Systems
        Sizes[MapImage.PageNumber] = Wanted
    raise ValueError("DWG page map size did not converge")
