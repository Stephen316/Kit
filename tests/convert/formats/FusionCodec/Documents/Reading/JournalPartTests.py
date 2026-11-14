from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Prism.PrismArchive import StorePrism


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "FileName,RootCount,StateCount",
    (
        ("re/Fusion/Study/moretools-88a2cd6cad0b/Draft.f3d", 2, 3),
        ("re/Fusion/Study/faceedits-3f120cbee8d9/offset_cylinder.f3d", 2, 3),
        (
            "re/Fusion/Study/meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d",
            3,
            2,
        ),
        ("re/Fusion/Study/meshconverts-4b42d39fb1d5/faceted_open.f3d", 2, 2),
    ),
)
def TestJournalPart(
    TmpPath: FilePath, FileName: str, RootCount: int, StateCount: int
) -> None:
    Payload = NativeHistory(FileName)
    NameValue = "Breps.BlobParts/BREP.JournalIntegration.smbh"
    Parsed = ReadBodyPart(ContainerPart(NameValue, Payload))
    assert isinstance(Parsed.History, JournalModel)
    assert Parsed.History.Header.RootCount == RootCount
    assert len(Materialize(Parsed.History)) == StateCount
    Emitted = EmitBodyPart(Parsed)
    assert Emitted.Payload == Payload
    Stored = StorePrism(TmpPath / "FullJournal.zip", Emitted.Payload)
    assert ReadBodyPart(ContainerPart(NameValue, Stored)) == Parsed
