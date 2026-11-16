from pathlib import Path as FilePath
from typing import Mapping, cast as CastValue

from pytest import mark as TestMark

from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks import build_sldprt as BuildSldprt
from convert.adapters.solidworks import read_sldprt as ReadSldprt
from convert.adapters.solidworks.Container.Container import (
    container_signatures as ContainerSignatures,
)
from convert.adapters.solidworks.Core.EquationTarget import KUnresolvedEqTargets

# a measured cut provides two equation targets with verified ownership
KEquationPart = (
    FilePath(__file__).parents[4]
    / "re/automation/PairedCaptures/P04/solidworks-c1986308375a"
    / "P04-solidworks-baseline-a.SLDPRT"
)

# equation fixture edits need the native stream that owns relation records
KConfigStream = "Contents/Config-0"

# dimension fixture edits need the native stream that owns feature parameter names
KKeywordStream = "swXmlContents/KeyWords"

# target mutations need a stable qualified name to isolate one authored dimension
KTargetName = "cut_left_mm@CutSketch"

# the missing target fixture must exercise unresolved names independently of operand links
KMissingName = "bad_left_mm@CutSketch"


# target variants preserve the original part structure while changing binding evidence
def TargetFixture(ModeValue: str) -> bytes:
    PartBytes = KEquationPart.read_bytes()
    Archive = SldprtArchive.from_bytes(PartBytes)
    Streams = Archive.streams
    if ModeValue == "missing":
        Before = f'"{KTargetName}" ='.encode("utf-16le")
        After = f'"{KMissingName}" ='.encode("utf-16le")
        assert len(Before) == len(After) and Streams[KConfigStream].count(Before) == 1
        Streams[KConfigStream] = Streams[KConfigStream].replace(Before, After, 1)
    else:
        Dimension = b'<Dimension Name="cut_left_mm">15</Dimension>'
        assert Streams[KKeywordStream].count(Dimension) == 1
        Streams[KKeywordStream] = Streams[KKeywordStream].replace(
            Dimension, Dimension + Dimension, 1
        )
    return BuildSldprt(
        Streams,
        file_id=Archive.file_id,
        format_version=Archive.format_version,
        signatures=ContainerSignatures(PartBytes),
    )


# public inspection must distinguish missing targets from duplicate owned dimensions
@TestMark.parametrize(
    ("ModeValue", "ExpectedName", "ExpectedReason", "ExpectedCount"),
    (
        ("missing", KMissingName, "unresolved_target", 1),
        ("duplicate", KTargetName, "ambiguous_target", 2),
    ),
)
def TestEquationLhs(
    ModeValue: str, ExpectedName: str, ExpectedReason: str, ExpectedCount: int
) -> None:
    Document = ReadSldprt(TargetFixture(ModeValue))
    Targets = Document.metadata[KUnresolvedEqTargets]
    assert isinstance(Targets, tuple)
    TargetRows = CastValue(tuple[Mapping[str, object], ...], Targets)
    assert len(TargetRows) == 1
    Target = TargetRows[0]
    assert Target["lhs"] == ExpectedName
    assert Target["reason"] == ExpectedReason
    assert Target["native_stream"] == KConfigStream
    Source = Target["equation_source"]
    assert isinstance(Source, str) and Source.startswith(f'"{ExpectedName}" =')
    Dimensions = [Param for Param in Document.parameters if Param.name == "cut_left_mm"]
    assert len(Dimensions) == ExpectedCount
    assert all(Param.expression is None for Param in Dimensions)
    assert any(
        Param.name == "cut_bottom_mm" and Param.expression is not None
        for Param in Document.parameters
    )
