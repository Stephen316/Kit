from convert.Formats.Fusion.Sketches.Projections.ReadCapCache import KCapCacheState
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordDiagnostic import Diagnostic


# complete late recovery clears only the primitive refusals for those same native outputs
def FilterCapIssues(
    Diagnostics: tuple[Diagnostic, ...], Sketches: tuple[Sketch, ...]
) -> tuple[Diagnostic, ...]:
    Recovered = {
        Entity.provenance.native_id
        for SketchValue in Sketches
        for Entity in SketchValue.entities
        if Entity.provenance is not None
        and Entity.attributes.get("fusion.projection_mode") == "automatic_face_boundary"
        and Entity.attributes.get("fusion.cap_curve_state") == KCapCacheState
    }
    return tuple(
        Issue
        for Issue in Diagnostics
        if Issue.code != "fusion.sketch.primitive"
        or Issue.provenance is None
        or Issue.provenance.native_id not in Recovered
    )
