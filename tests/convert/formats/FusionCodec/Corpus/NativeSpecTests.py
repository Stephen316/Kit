from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile
from tests.convert.formats.FusionCodec.Corpus.MutateCatalog import MutateCatalog
from tests.convert.formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile

KNativeFile = "re/Fusion/Study/projectionfamilies-d987c50c2d73/intersect_circle.f3d"


@MarkTests.parametrize("ChangeKind", ("class", "version", "base"))
def TestNativeGuard(TmpPath: FilePath, ChangeKind: str) -> None:
    Target = TmpPath / "Unqualified.f3d"
    _ = Target.write_bytes(MutateCatalog(KNativeFile, ChangeKind))
    Source = ReadCorpusFile(str(Target))
    with RaisesError(ValueError, match="Unqualified Fusion native"):
        _ = BuildProfile(Source.Metadata.Classes, Source.Targets)
