from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Core.Cut.CutRuleLines import CutRuleLine
from convert.adapters.solidworks.Core.Cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


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
