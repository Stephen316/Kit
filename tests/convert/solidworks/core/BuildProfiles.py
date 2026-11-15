from pathlib import Path as FilePath

from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.container.Format import (
    KEYWORDS_STREAM as KKeywordsStream,
)
from convert.adapters.solidworks.container.Format import (
    RESOLVED_FEATURES_STREAM as KResolvedStream,
)
from convert.adapters.solidworks.core.Native import DecodeNative
from tests.convert.solidworks.core.MarkerFrame import KMarkerSize, MarkerFrame
from tests.convert.solidworks.core.ProfileFrames import ProfileFrames

# a measured rectangle supplies an anchored native profile for traversal scenarios
KProfilePart = (
    FilePath(__file__).parents[4]
    / "re/automation/PairedCaptures/P01/solidworks-75b9308cf13e/P01-solidworks-baseline-a.SLDPRT"
)


# bounded synthetic profiles exercise traversal scale without additional vendor authored files
def BuildProfiles(
    Count: int, Headers: bool
) -> tuple[bytes, int, set[int], set[int], set[int]]:
    Original = KProfilePart.read_bytes()
    Archive = SldprtArchive.FromBytes(Original)
    Streams = Archive.Streams
    Model = DecodeNative(Streams[KKeywordsStream], Streams[KResolvedStream])
    Sketch = Model.sketches[0]
    InsertAt = Sketch.native_end
    Padding = max(0, 31 - len(Sketch.markers))
    Frames, HeaderOffsets, RectOffsets, PolyOffsets = ProfileFrames(
        len(Sketch.markers) + Padding, InsertAt + Padding * KMarkerSize, Count, Headers
    )
    Resolved = Streams[KResolvedStream]
    Streams[KResolvedStream] = (
        Resolved[:InsertAt] + MarkerFrame(3) * Padding + Frames + Resolved[InsertAt:]
    )
    Generated = BuildSldprt(Streams, Template=Original)
    return Generated, InsertAt, HeaderOffsets, RectOffsets, PolyOffsets
