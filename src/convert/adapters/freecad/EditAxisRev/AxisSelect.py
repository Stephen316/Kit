from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Revolves.SketchAxis import KLineGuid
from convert.formats.Fusion.SelectionProxy import KSelectProxy
from convert.formats.Fusion.SelectionRef import KSelectDesc
from convert.formats.Fusion.Sketches.SketchPick import KSketchLeaf
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch


# the typed source path and line span identify the same selected sketch geometry
def ReadAxisPick(
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    PickValue: Selection,
    SketchValue: Sketch,
) -> str:
    Attrs = FeatureValue.attributes
    SelectId = Attrs.get("fusion.revolve.axis_selection_id")
    NativeId = Attrs.get("fusion.revolve.axis_object_id")
    Origin = PickValue.provenance
    FeatureOrigin = FeatureValue.provenance
    if (
        type(SelectId) is not int
        or SelectId <= 0
        or type(NativeId) is not int
        or NativeId <= 0
        or PickValue.id != f"fusion-selection-{SelectId}-axis"
        or PickValue.id != Definition.AxisSelectionId
        or FeatureValue.selection_ids != (PickValue.id,)
        or PickValue.query
        or PickValue.point is not None
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(SelectId)
        or FeatureOrigin is None
        or tuple(SpanValue.record_kind for SpanValue in Origin.spans)
        != (KSelectProxy, KSelectDesc, KSketchLeaf, KLineGuid)
        or any(
            SpanValue.stream != KDesignPrefix + "BulkStream.dat"
            or SpanValue.offset < 0
            or SpanValue.length <= 0
            or SpanValue not in FeatureOrigin.spans
            for SpanValue in Origin.spans
        )
    ):
        raise ValueError("FreeCAD editable sketch axis selection provenance disagrees")
    LineId = f"fusion-sketch-entity-{NativeId}"
    if Attrs.get("fusion.revolve.axis_entity_id") != LineId or PickValue.path != (
        SelectPathElem("sketch", SketchValue.id),
        SelectPathElem("sketch_entity", LineId),
    ):
        raise ValueError("FreeCAD editable sketch axis selection path changed")
    Matches = tuple(Value for Value in SketchValue.entities if Value.id == LineId)
    if (
        len(Matches) != 1
        or Matches[0].provenance is None
        or Matches[0].provenance.spans != (Origin.spans[-1],)
    ):
        raise ValueError("FreeCAD editable sketch axis line evidence disagrees")
    return LineId
