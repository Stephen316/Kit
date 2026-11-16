from dataclasses import replace as Replace

from convert.Formats.Fusion.ConstructionPlane.OriginDatum import ReadOriginDatum
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.OriginAxis import KComponentGuid
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.PrincipalRoute import PrincipalRoute
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.SupportPlane import SupportPlane


# the sketch keeps its own basis when the datum has a different alignment in the plane
def AttachPrincipal(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Feature: RecordSpan,
    ComponentId: int,
    PlaneValue: SupportPlane,
) -> SupportPlane:
    Origin = PlaneValue.provenance
    if Origin is None:
        return PlaneValue
    try:
        Route = PrincipalRoute(BulkData, Owners, Feature)
        PlaneId = Route[-1]
        NameValue, DatumFrame, ContainerId = ReadOriginDatum(
            BulkData, Owners, PlaneId, ComponentId
        )
        Component = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
        Component.Offset = 66
        if (
            ReadNativeRef(Component) != ContainerId
            or NameValue not in ("XY", "YZ")
            or PlaneValue.transform.origin != DatumFrame.origin
            or PlaneValue.transform.z_axis != DatumFrame.z_axis
        ):
            return PlaneValue
    except ValueError:
        return PlaneValue
    Spans = Origin.spans + tuple(
        SpanValue
        for Identity in (Feature.ObjectId, *Route, ContainerId, ComponentId)
        for SpanValue in RecordOrigin(Owners[Identity]).spans
    )
    return Replace(
        PlaneValue,
        provenance=Replace(Origin, spans=Spans),
        attributes=FreezeMapping(
            {
                **PlaneValue.attributes,
                "fusion.native_support_resolved": True,
                "fusion.native_support_object_id": PlaneId,
                "fusion.native_support_name": NameValue,
            }
        ),
    )
