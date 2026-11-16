from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode


# the round surf operation needs a consistent construction rule so topology changes retain their native revision relationships
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
