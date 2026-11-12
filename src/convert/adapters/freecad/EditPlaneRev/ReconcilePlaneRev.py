from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditBinding import HasLegacyEdit, ReadEditBinding
from convert.adapters.freecad.EditPlaneRev.ApplyPlaneRev import ApplyPlaneRev
from convert.adapters.freecad.EditPlaneRev.PlaneRevBinding import KPlaneRevBinding
from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import ReadPlaneRev
from convert.adapters.freecad.EditRead.PlaneRev.ReadPlaneRevFields import (
    ReadPlaneRevFields,
)
from convert.adapters.freecad.EditRev.RevCacheProof import CheckRevSolid, CheckRevWire
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneRev import PlaneRevolve


# native controls and both shape caches must agree before replacing source plane data
def ReconcilePlane(
    DocValue: CadDocument,
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KPlaneRevBinding)
    Feature = DocValue.feature_timeline[-1] if DocValue.feature_timeline else None
    if Binding is None:
        if (
            Feature is not None
            and isinstance(Feature.definition, PlaneRevolve)
            and HasLegacyEdit(RootValue)
            and RootValue.find("./Objects/Object[@type='Part::Revolution']") is not None
        ):
            raise ValueError("FreeCAD editable plane Revolve binding is missing")
        return DocValue
    if Feature is None or Binding != Feature.id:
        raise ValueError(
            "FreeCAD editable plane Revolve binding disagrees with its source"
        )
    PlanValue = ReadPlaneRev(DocValue, Feature)
    if PlanValue is None:
        raise ValueError(
            "FreeCAD editable plane Revolve binding has no qualified source"
        )
    Fields = ReadPlaneRevFields(RootValue, DocValue, PlanValue)
    CheckRevWire(
        Archive,
        Members,
        Fields.SketchEntry,
        Fields.EmptyEntries,
        DocValue.sketches[0],
        Fields.ProfileSketch,
        PlanValue.SketchFrame,
    )
    Rebuilt = ApplyPlaneRev(
        DocValue, PlanValue, Fields.ProfileSketch, Fields.AngleEdits
    )
    CheckRevSolid(Archive, Members, Fields.ShapeEntry, Rebuilt)
    return Rebuilt
