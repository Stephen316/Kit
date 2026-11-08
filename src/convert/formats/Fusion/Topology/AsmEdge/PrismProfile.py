# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import SketchEntity


# neutral prism rim order derives from authored profile winding and exact curve tags
def ReadProfileTags(Profile: tuple[SketchEntity, ...]) -> tuple[int, ...]:
    Lines = []
    CurveTags = {}
    for Entity in Profile:
        Geometry = Entity.geometry
        TagValue = Entity.attributes.get("fusion.entity_tag")
        if (
            not isinstance(Geometry, LineGeometry)
            or Entity.construction
            or type(TagValue) is not int
            or TagValue <= 0
        ):
            raise ValueError("Fusion edge source requires whole tagged profile lines")
        Lines.append(Geometry)
        CurveTags[frozenset((Geometry.start, Geometry.end))] = TagValue
    if not 3 <= len(CurveTags) == len(Lines) <= 64 or len(
        set(CurveTags.values())
    ) != len(CurveTags):
        raise ValueError("Fusion edge source profile tags are ambiguous")
    Points, _, _ = MeasureRing(ReadPrismRing(tuple(Lines)))
    return tuple(
        CurveTags[frozenset((Start, Finish))]
        for Start, Finish in zip(Points, Points[1:] + Points[:1], strict=True)
    )
