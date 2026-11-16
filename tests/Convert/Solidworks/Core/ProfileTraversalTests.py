from pytest import mark as TestMark

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KEYWORDS_STREAM as KKeywordsStream,
)
from convert.adapters.solidworks.Container.Format import (
    RESOLVED_FEATURES_STREAM as KResolvedStream,
)
from convert.adapters.solidworks.Core.Native import DecodeNative
from tests.Convert.Solidworks.Core.BuildProfiles import BuildProfiles
from tests.Convert.Solidworks.Core.ProfileFrames import KPolyPoints


# scaling contour counts preserves graph ownership across paths with optional headers
@TestMark.parametrize("Count", (1, 64))
@TestMark.parametrize("Headers", (False, True))
def TestNativeGraph(Count: int, Headers: bool) -> None:
    PartBytes, InsertAt, HeaderOffsets, RectOffsets, PolyOffsets = BuildProfiles(
        Count, Headers
    )
    Archive = SldprtArchive.FromBytes(PartBytes)
    Model = DecodeNative(
        Archive.Require(KKeywordsStream), Archive.Require(KResolvedStream)
    )
    Sketch = Model.sketches[0]
    Rectangles = [
        Profile
        for Profile in Sketch.profiles
        if Profile.kind == "rectangle" and min(Profile.marker_offsets) >= InsertAt
    ]
    assert len(Rectangles) == Count
    assert all(Profile.coordinates == (0.0, 0.0, 2.0, 2.0) for Profile in Rectangles)
    assert {
        Offset for Profile in Rectangles for Offset in Profile.marker_offsets
    } == RectOffsets
    assert {
        Profile.HeaderOffset
        for Profile in Rectangles
        if Profile.HeaderOffset is not None
    } == HeaderOffsets
    if not Headers:
        assert all(Profile.HeaderOffset is None for Profile in Rectangles)
    Polylines = [
        Profile
        for Profile in Sketch.profiles
        if Profile.kind == "polyline" and min(Profile.marker_offsets) >= InsertAt
    ]
    assert len(Polylines) == 1
    assert Polylines[0].coordinates == tuple(
        Value for PointValue in KPolyPoints for Value in PointValue
    )
    assert set(Polylines[0].marker_offsets) == PolyOffsets
