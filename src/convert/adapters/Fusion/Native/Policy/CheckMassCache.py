from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, PointCoords
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory


def CheckMassCache(Context: ExtrudeContext, History: PrismHistory) -> None:
    Model = History.Model
    Lengths = (Model.Width / 10, Model.Depth / 10, Model.Height / 10)
    Center = tuple(
        Model.BasePoint[Index] / 10 + Lengths[Index] / 2 for Index in range(3)
    )
    Volume = Lengths[0] * Lengths[1] * Lengths[2]
    Inertia = tuple(
        Volume
        * sum(
            Lengths[Other] ** 2 / 12 + Center[Other] ** 2
            for Other in range(3)
            if Other != Index
        )
        for Index in range(3)
    )
    CrossTerms = tuple(
        -Volume * Center[First] * Center[Second]
        for First, Second in ((0, 1), (0, 2), (1, 2))
    )
    Cache = ObjectFields(Context.BodyNode.Fields["cache"])
    SameNumbers(PointCoords(Cache["moi"]), Inertia)
    SameNumbers(PointCoords(Cache["moiOffDiag"]), CrossTerms)
