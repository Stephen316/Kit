from convert.formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import KSketchOwners
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def SnapshotAttrs(Value: PrismSnapshot) -> tuple[GeometryRecord, ...]:
    Solid = (
        *tuple(
            MakeFeatureTag(6 + Index, TagValue)
            for Index, TagValue in enumerate(Value.TagSet.Faces)
        ),
        *tuple(
            MakeSketchTag(Owner + 2, TagValue)
            for Owners, TagValue in zip(
                KSketchOwners, Value.TagSet.Sketches, strict=True
            )
            for Owner in Owners
        ),
    )
    Regions = tuple(
        MakeSketchTag(Start + Offset + Index, TagValue)
        for Start, Region in ((88, Value.Profile), (113, Value.Sketch))
        for Offset, TagValues in ((5, Region.CoedgeTags), (9, Region.EdgeTags))
        for Index, TagValue in enumerate(TagValues)
    )
    return (*Solid, *Regions)


def SnapshotHeads() -> tuple[tuple[int, int], ...]:
    return (
        *((6 + Index, 138 + Index) for Index in range(6)),
        *(
            (Owner + 2, 144 + 2 * Index + Offset)
            for Index, Owners in enumerate(KSketchOwners)
            for Offset, Owner in enumerate(Owners)
        ),
        *(
            (Start + Offset + Index, AttrStart + Group * 4 + Index)
            for Start, AttrStart in ((88, 152), (113, 160))
            for Group, Offset in enumerate((5, 9))
            for Index in range(4)
        ),
    )
