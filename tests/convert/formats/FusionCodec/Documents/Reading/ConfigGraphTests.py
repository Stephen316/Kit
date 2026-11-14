from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckConfigRefs,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ReadConfigPart import (
    ReadConfigPart,
)
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from tests.convert.formats.FusionCodec.Documents.Reading.AuxPartSource import (
    NativeAuxParts,
)
from tests.convert.formats.FusionCodec.Documents.Reading.NativeDocSource import (
    ReadNativeCore,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestConfigGraph() -> None:
    Streams, Metadata = ReadNativeCore()
    Design = Streams[0]
    Profile = MakeDocProfile(ReadDocSchemas(), Metadata, Design.SegmentId)
    Segment = ReadDocSegment(Design, Metadata[0], Profile)
    Parts = tuple(
        ReadConfigPart(Value)
        for Value in NativeAuxParts(0)
        if not Value.Name.endswith(".smb")
    )
    CheckConfigRefs((Segment,), Parts)
    with Raises(ValueError, match="disagree with Design triggers"):
        CheckConfigRefs((Segment,), Parts[:1])
    with Raises(ValueError, match="disagree with Design triggers"):
        CheckConfigRefs((Segment,), (Parts[0], Parts[0]))
