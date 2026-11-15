from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot


# drawing bundle needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingBundle:
    Description: BundleModel
    Drawing: FusionDrawing
    Documents: tuple[BundleFile, ...]
    Layout: tuple[PackageSlot, ...]
