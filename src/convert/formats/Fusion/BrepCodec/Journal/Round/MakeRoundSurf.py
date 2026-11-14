from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode


def MakeRoundSurf(Model: SphereBody | TorusBody) -> SphereNode | TorusNode:
    Center = (Model.CenterMm[0] / 10, Model.CenterMm[1] / 10, Model.CenterMm[2] / 10)
    Prefix = EntityPrefix(-1, -1)
    if isinstance(Model, SphereBody):
        return SphereNode(
            Prefix,
            Center,
            Model.RadiusMm / 10,
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            False,
            None,
            None,
            None,
            None,
        )
    return TorusNode(
        Prefix,
        Center,
        Model.AxisVector,
        Model.MajorRadiusMm / 10,
        Model.MinorRadiusMm / 10,
        Model.ReferenceAxis,
        False,
        None,
        None,
        None,
        None,
    )
