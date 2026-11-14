from dataclasses import replace as Replace
from pathlib import Path as FilePath

from pytest import mark as TestMarks

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Adapter import FusionReader
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.SourceProof.InspectSource import ReadSourceProof
from convert.formats.Fusion.ZipParameters import ReadZipParams
from tests.convert.formats.FusionCodec.Parameters.RebuildParams import RebuildParams

KStudyRoot = FilePath(__file__).resolve().parents[5] / "re" / "Fusion" / "Study"
KUserGroup = "userparameters-e9c6959ff5fd/"
KTextGroup = "parametertexts-d16f951482fc/"
KOptions = ReadOptions(strict=False)


@TestMarks.parametrize(
    "RelativePath",
    (
        KUserGroup + "length_mm.f3d",
        KUserGroup + "length_in.f3d",
        KUserGroup + "angle.f3d",
        KUserGroup + "unitless.f3d",
        KUserGroup + "comment.f3d",
        KUserGroup + "favorite.f3d",
        KUserGroup + "dependency_chain.f3d",
        KTextGroup + "user_multiline_comment.f3d",
        KTextGroup + "model_multiline_comment.f3d",
        KTextGroup + "model_favorite_false.f3d",
        KTextGroup + "model_favorite_true.f3d",
        "holdouts-f8c508a73323/expression_depth.f3d",
        "revolveto-b1d196f65c46/two_planes.f3d",
    ),
)
def TestParamZip(RelativePath: str) -> None:
    Source = KStudyRoot / RelativePath
    Reader = FusionReader()
    Before = Reader.Read(Source, KOptions)
    Rebuilt = RebuildParams(Source)
    After = Reader.Read(Rebuilt, KOptions)
    assert After.parameters == Before.parameters
    assert After.feature_timeline == Before.feature_timeline
    assert After.sketches == Before.sketches
    assert After.bodies == Before.bodies
    assert After.brep == Before.brep
    assert After.diagnostics == Before.diagnostics
    assert ReadZipParams(Rebuilt) == ReadZipParams(Source.read_bytes())


def ChangeComment(Value: NativeParam) -> NativeParam:
    return Replace(Value, Comment="Longer native comment\nsecond\tcolumn\r\nend")


def TestCommentEdit() -> None:
    Source = KStudyRoot / KUserGroup / "length_mm.f3d"
    Rebuilt = RebuildParams(Source, ChangeComment)
    Document = FusionReader().Read(Rebuilt, KOptions)
    (Parameter,) = Document.parameters
    assert Parameter.name == "probeWidth"
    assert Parameter.value.value == 0.73
    assert Parameter.value.unit == "cm"
    assert Parameter.expression is not None
    assert Parameter.expression.source == "7.3 mm"
    assert (
        Parameter.attributes["fusion.comment"]
        == "Longer native comment\nsecond\tcolumn\r\nend"
    )
    assert Parameter.attributes["fusion.collection_id"] == 16


def ChangeOwner(Value: NativeParam) -> NativeParam:
    return Replace(Value, CollectionId=(1 << 63) + 31)


def TestOwnerProof() -> None:
    Source = KStudyRoot / KUserGroup / "length_mm.f3d"
    Rebuilt = RebuildParams(Source, ChangeOwner)
    (Parameter,), Diagnostics = ReadZipParams(Rebuilt)
    assert not Diagnostics
    assert Parameter.attributes["fusion.collection_id"] == (1 << 63) + 31
    Proof = ReadSourceProof(Rebuilt)
    assert not Proof.IsComplete
    assert not any(
        Claim.Evidence == "scoped numeric parameter and formula"
        for Claim in Proof.Claims
    )
