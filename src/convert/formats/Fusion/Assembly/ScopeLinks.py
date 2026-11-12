from collections.abc import Mapping

from convert.formats.Fusion.Assembly.ScopeSelect import GetPickLinks
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# each portable record contributes only its explicit dependency links
def GetScopeLinks(
    Record: FeatureStep | Sketch | SupportPlane | Selection | Parameter,
    Sketches: Mapping[str, Sketch],
) -> tuple[tuple[str, str], ...]:
    if isinstance(Record, FeatureStep):
        return (
            *(("step", Identity) for Identity in Record.input_feature_ids),
            *(() if Record.sketch_id is None else (("sketch", Record.sketch_id),)),
            *(("selection", Identity) for Identity in Record.selection_ids),
            *(("parameter", Identity) for Identity in Record.parameter_ids),
            *(
                ("parameter", Identity)
                for State in Record.configuration_states
                for Identity in State.parameter_override_ids
            ),
        )
    if isinstance(Record, Sketch):
        return (
            ("plane", Record.support_plane_id),
            *(("parameter", Identity) for Identity in Record.parameter_ids),
            *(
                ("parameter", Relation.parameter_id)
                for Relation in Record.constraints
                if Relation.parameter_id
            ),
        )
    if isinstance(Record, SupportPlane):
        return tuple(
            (LinkKind, Identity)
            for LinkKind, Identity in (
                ("selection", Record.support_selection_id),
                ("parameter", Record.offset_parameter_id),
            )
            if Identity
        )
    if isinstance(Record, Selection):
        return GetPickLinks(Record, Sketches)
    return (
        ()
        if Record.expression is None
        else tuple(
            ("parameter", Identity) for Identity in Record.expression.parameter_ids
        )
    )
