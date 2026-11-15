from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.core.cut.CutRuleLines import CutRuleLine
from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpan
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Sketch import ConstraintRef, SketchRelation


# the saved axis constraints select configuration segment identities rather than resolved trim edges
def ProjectCutAxes(
    Source: CutRuleSource, Lines: dict[int, CutRuleLine]
) -> tuple[SketchRelation, ...]:
    Relations = Source.SketchData.Geometry["member_relations"]
    RequireArch(len(Relations), len(Lines), "one cut axis constraint per line")
    RequireArch(
        {Value["segment_native_id"] for Value in Relations},
        set(Lines),
        "all cut axes own a configuration line",
    )
    return tuple(
        SketchRelation(
            f"sldprt:constraint:{Source.ProfileId}:axis:{Relation['segment_native_id']}",
            Relation["kind"],
            (ConstraintRef(Lines[Relation["segment_native_id"]].EntityId),),
            provenance=RectSource(
                str(Relation["line_handle_object"]),
                Source.ConfigStream,
                MemberSpan(Relation["start"], Relation["end"]),
                "sketch-axis-relation",
            ),
            attributes=FreezeMapping(
                {
                    "native_code": Relation["type_code"],
                    "native_line_handle": Relation["line_handle_object"],
                    "native_segment_id": Relation["segment_native_id"],
                }
            ),
        )
        for Relation in Relations
    )
