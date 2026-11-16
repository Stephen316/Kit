from pathlib import Path as FilePath

from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile
from tests.Convert.Formats.FusionCodec.Corpus.MutateCatalog import MutateCatalog
from tests.Convert.Formats.FusionCodec.Corpus.ReadCorpusFile import ReadCorpusFile

# the native file cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KNativeFile = "re/Fusion/Study/projectionfamilies-d987c50c2d73/intersect_circle.f3d"


# the native guard contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("ChangeKind", ("class", "version", "base"))
def TestNativeGuard(TmpPath: FilePath, ChangeKind: str) -> None:
    Target = TmpPath / "Unqualified.f3d"
    _ = Target.write_bytes(MutateCatalog(KNativeFile, ChangeKind))
    Source = ReadCorpusFile(str(Target))
    with RaisesError(ValueError, match="Unqualified Fusion native"):
        _ = BuildProfile(Source.Metadata.Classes, Source.Targets)
