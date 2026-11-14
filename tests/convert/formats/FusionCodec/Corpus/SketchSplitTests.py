from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile
from tests.convert.formats.FusionCodec.Corpus.MutateSplit import MutateSplit
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile

KSplitFile = (
    "re/Fusion/Study/linetrimholdouts-456e1d19906d/reverse_rectangle_creation.f3d"
)


@MarkTests.parametrize(("Sequence", "TotalCount"), ((0, 2), (3, 2), (1, 0)))
def TestSplitRange(TmpPath: FilePath, Sequence: int, TotalCount: int) -> None:
    Target = TmpPath / "InvalidSplit.f3d"
    _ = Target.write_bytes(MutateSplit(KSplitFile, Sequence, TotalCount))
    Source = ReadCorpusFile(str(Target))
    Profile = BuildProfile(Source.Metadata.Classes, Source.Targets)
    with RaisesError(ValueError, match="one-based split ordinal"):
        _ = DecodeEntities(Source.Records, Source.Metadata.Classes, Profile)
