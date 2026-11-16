from dataclasses import dataclass as Dataclass
from math import dist as Distance

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectBindings import (
    KPointToleranceMm,
    RectBindings,
)
from convert.adapters.solidworks.Resolved.RectanglePart import RectanglePart
from convert.adapters.solidworks.Sketch.GeometryTypes import Coincidence, PointReference


# an origin rule must connect an actual typed proxy and an actual perimeter vertex
@Dataclass(frozen=True, slots=True)
class RectOrigin:
    Proxy: PointReference
    Vertex: int
    Relation: Coincidence


# the archive point and plane must locate the same world origin as the proxy
def CheckOriginLoc(
    Parsed: RectanglePart, Binding: RectBindings, ProxySlot: int
) -> None:
    RequireArch(
        Parsed.Origin.Geometry.PointValue, (0, 0), "typed document origin point"
    )
    RequireArch(
        Parsed.Origin.Support.ShiftScale, (0, 0, 0, 1), "typed origin placement"
    )
    LocalX, LocalY = Binding.Points[ProxySlot]
    XShift, YShift, ZShift, Scale = Parsed.Reference.ShiftScale
    UAxis, VAxis, _ = Parsed.Directions
    World = tuple(
        (LocalX * UValue + LocalY * VValue) * Scale + Shift * 1000
        for UValue, VValue, Shift in zip(
            UAxis, VAxis, (XShift, YShift, ZShift), strict=True
        )
    )
    RequireArch(
        Distance(World, (0, 0, 0)) <= KPointToleranceMm,
        True,
        "proxy reaches the owned origin in world coordinates",
    )


# the saved coincidence is usable only once its foreign handle resolves the parsed origin
def BindRectOrigin(Parsed: RectanglePart, Binding: RectBindings) -> RectOrigin:
    Profile = Parsed.Profile
    RequireArch(
        len(Profile.Geometry["external_point_references"]), 1, "one typed origin proxy"
    )
    (Proxy,) = Profile.Geometry["external_point_references"]
    RequireArch(
        (Proxy["feature_id"], Proxy["handle_class"], Proxy["handle_fields"]),
        (Parsed.Origin.FeatureId, "sgPointHandle", (0, -1, 0)),
        "proxy handle identifies the owned Origin point",
    )
    RequireArch(len(Profile.Coincidences), 1, "one saved rectangle origin coincidence")
    (Relation,) = Profile.Coincidences
    RequireArch(
        (Relation["suppressed"], Relation["deleted"]),
        (False, False),
        "active rectangle origin coincidence",
    )
    Participants = Relation["point_native_ids"]
    RequireArch(
        Proxy["local_id"] in Participants,
        True,
        "coincidence owns the referenced origin proxy",
    )
    Vertices = [
        SlotValue
        for SlotValue, Identity in Participants
        if (SlotValue, Identity) != Proxy["local_id"]
    ]
    RequireArch(len(Vertices), 1, "one perimeter vertex in origin coincidence")
    (Vertex,) = Vertices
    ProxySlot = Proxy["local_id"][0]
    CheckOriginLoc(Parsed, Binding, ProxySlot)
    RequireArch(
        Distance(Binding.Points[Vertex], Binding.Points[ProxySlot])
        <= KPointToleranceMm,
        True,
        "coincident perimeter and origin points",
    )
    return RectOrigin(Proxy, Vertex, Relation)
