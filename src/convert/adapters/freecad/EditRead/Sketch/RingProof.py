from convert.adapters.freecad.Archive import ConstraintsProp, ParamCatalog
from convert.adapters.freecad.EditExtRing import GetRingPoints
from convert.adapters.freecad.EditRead.Sketch.ProfileProof import CheckProfileIds
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckStaticRow
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import (
    CheckExtensions,
    CheckSketchOpts,
)
from convert.adapters.freecad.EditRing.RingChange import SyncRingEdit
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Sketch import Sketch
from interchange.serialization.EncodeData import ToData


# the saved solver graph must still connect each ring edge to its two source points
def ReadRingProfile(
    Native: NativeObject, Original: Sketch, AllowProfile: bool
) -> Sketch:
    SketchData = ToData(Original)
    if not isinstance(SketchData, dict) or GetRingPoints(Original) is None:
        raise ValueError("FreeCAD editable line profile has an invalid source ring")
    CheckProfileIds(Native, Original, SketchData)
    CheckExtensions(Native)
    CheckSketchOpts(Native)
    Indices = {Value.id: Index for Index, Value in enumerate(Original.entities)}
    Template, Expressions, Dependencies, Diagnostics = ConstraintsProp(
        SketchData, Indices, ParamCatalog([]), IncludeIncidence=AllowProfile
    )
    ExpectedCount = (
        2 * len(Original.closed_profile_entity_ids[0]) if AllowProfile else 0
    )
    if (
        Expressions
        or Dependencies
        or Diagnostics
        or len(Template) != 1
        or len(Template[0]) != ExpectedCount
    ):
        raise ValueError(
            "FreeCAD editable line profile has an invalid source constraint graph"
        )
    for RowValue in ReadRuleRows(Native, Template):
        CheckStaticRow(RowValue)
    Edited = ReadSketchGeom(Native, Original)
    if Edited is Original:
        return Original
    if not AllowProfile:
        raise ValueError(
            "FreeCAD editable line profile geometry changed without a binding"
        )
    return SyncRingEdit(Original, Edited)
