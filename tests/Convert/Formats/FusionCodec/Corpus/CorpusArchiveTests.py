from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

from convert.Formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.Formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.Formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile
from convert.Formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.Convert.Formats.FusionCodec.Corpus.ReadCorpusData import ReadCorpusData
from tests.Convert.Formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile


# the corpus wire contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("FileName", tuple(sorted(ReadCorpusData()["Profiles"])))
def TestCorpusWire(FileName: str) -> None:
    Source = ReadCorpusFile(FileName)
    Expected = ReadCorpusData()["Profiles"][FileName]["MetadataHash"]
    assert HashBytes(Source.MetaData).hexdigest() == Expected
    Profile = BuildProfile(Source.Metadata.Classes, Source.Targets)
    Model = DecodeEntities(Source.Records, Source.Metadata.Classes, Profile)
    Emitted = EncodeEntities(Model, Source.Metadata.Classes, Profile)
    assert Emitted == Source.Records
    BulkData, MetaData = EmitSegment(Source.Metadata, Emitted)
    assert BulkData == Source.BulkData
    assert MetaData == Source.MetaData
