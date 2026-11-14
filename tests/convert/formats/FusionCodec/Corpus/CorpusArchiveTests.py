from hashlib import sha256 as HashBytes

from pytest import mark as MarkTests

from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusData import ReadCorpusData
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile


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
