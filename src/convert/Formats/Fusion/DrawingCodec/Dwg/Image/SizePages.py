from convert.Formats.Fusion.DrawingCodec.Dwg.Image.EncodeMaps import EncodePageMap
from convert.Formats.Fusion.DrawingCodec.Dwg.Image.PackSections import PackOrPlan
from convert.Formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KPageMapType,
    KSectionMapType,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile

# size rounds needs one explicit bound so native drawing reconstruction cannot accept inconsistent resource or layout limits
KSizeRounds = 8


# the fit size contract needs a shared interpretation so section boundaries and object references remain consistent
def FitSize(Declared: int, Needed: int) -> int:
    Minimum = (Needed + 31) // 32 * 32
    return Declared if Declared >= Minimum else Minimum


# size pages needs an explicit validity boundary so section boundaries and object references remain consistent
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
