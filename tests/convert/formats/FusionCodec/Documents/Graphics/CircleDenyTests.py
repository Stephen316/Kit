from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile
from pytest import mark as MarkTests, raises as RaisesError
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

KRepoRoot = FilePath(__file__).resolve().parents[6]


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@MarkTests.parametrize(
    "ClassName", ("PrimitiveLODGeometryNode", "CircleArc<double>", "SimpleMesh")
)
def TestCircleDeny(TmpPath: FilePath, ClassName: str) -> None:
    Source = KRepoRoot / "re/Fusion/LocalOracle/PublicAdapter/vendor_circleEdited.f3d"
    Target = TmpPath / "UnknownGraphics.f3d"
    Changed = False
    with ZipFile(Source) as Before, ZipFile(Target, "w") as After:
        for Entry in Before.infolist():
            Payload = Before.read(Entry)
            if Entry.filename.endswith("/DefaultScene/world"):
                Token = ClassName.encode("utf-16le")
                Replacement = ("X" + ClassName[1:]).encode("utf-16le")
                assert Token in Payload
                Payload = Payload.replace(Token, Replacement, 1)
                Changed = True
            After.writestr(Entry.filename, Payload)
    assert Changed
    with RaisesError(ValueError):
        _ = ReadDocument(Target.read_bytes())
