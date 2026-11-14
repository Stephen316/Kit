from pathlib import Path as FilePath

from pytest import mark as TestMarks

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Adapter import FusionReader
from convert.formats.Fusion.ZipParameters import ReadZipParams
from tests.convert.formats.FusionCodec.Parameters.RebuildParams import RebuildParams

KOracleRoot = (
    FilePath(__file__).resolve().parents[5] / "re/Fusion/LocalOracle/Allocation"
)


@TestMarks.parametrize(
    ("FileName", "Indexes"),
    (
        ("two_parameters.f3d", (1, 2)),
        ("deleted_first.f3d", (2,)),
        ("added_third.f3d", (2, 3)),
    ),
)
def TestAllocations(FileName: str, Indexes: tuple[int, ...]) -> None:
    Source = KOracleRoot / FileName
    Rebuilt = RebuildParams(Source)
    Parameters, Diagnostics = ReadZipParams(Rebuilt)
    assert not Diagnostics
    assert (
        tuple(Value.attributes["fusion.parameter_index"] for Value in Parameters)
        == Indexes
    )
    Reader = FusionReader()
    Options = ReadOptions(strict=False)
    Before = Reader.Read(Source, Options)
    After = Reader.Read(Rebuilt, Options)
    assert Before.parameters == After.parameters
    assert Before.feature_timeline == After.feature_timeline
    assert Before.diagnostics == After.diagnostics
