from dataclasses import replace as Replace
from pathlib import Path as FilePath

from pytest import mark as TestMarks

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.Fusion.Adapter import FusionReader
from convert.Formats.Fusion.NativeParam import NativeParam
from convert.Formats.Fusion.SourceProof.InspectSource import ReadSourceProof
from convert.Formats.Fusion.ZipParameters import ReadZipParams
from tests.Convert.Formats.FusionCodec.Parameters.RebuildParams import RebuildParams

# study root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KStudyRoot = FilePath(__file__).resolve().parents[5] / "re" / "Fusion" / "Study"

# the user group cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KUserGroup = "userparameters-e9c6959ff5fd/"

# the text group cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KTextGroup = "parametertexts-d16f951482fc/"

# the options cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KOptions = ReadOptions(strict=False)


# the parameter zip contract needs boundary coverage so stored document relationships remain consistent
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


# shared change comment setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ChangeComment(Value: NativeParam) -> NativeParam:
    return Replace(Value, Comment="Longer native comment\nsecond\tcolumn\r\nend")


# the comment edit contract needs boundary coverage so stored document relationships remain consistent
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


# shared change owner setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ChangeOwner(Value: NativeParam) -> NativeParam:
    return Replace(Value, CollectionId=(1 << 63) + 31)


# the owner proof contract needs boundary coverage so stored document relationships remain consistent
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
