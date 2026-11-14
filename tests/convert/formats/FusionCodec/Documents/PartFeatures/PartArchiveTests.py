from pathlib import Path as FilePath

from pytest import approx as ApproxValue, mark as MarkTests

from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SolidMass import (
    SolidMass,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Materials.MaterialFields import (
    MaterialFields,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KFamilyClasses,
    KPartCases,
    PartSpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)


@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestPartArchive(TmpPath: FilePath, NameValue: str) -> None:
    SpecValue = PartSpec(NameValue)
    Source = TmpPath / (NameValue + ".f3d")
    _ = Source.write_bytes(EmitDocument(SpecValue))
    Model = ReadDocument(Source.read_bytes())
    Timeline: list[tuple[int, str, str]] = []
    for ClassName in sorted(set(KFamilyClasses.values())):
        for Fields in PartRecords(Model, ClassName):
            Ending = Fields["endModelHS"]
            UserName = Fields["featureUserName"]
            assert isinstance(Ending, int) and isinstance(UserName, str)
            Timeline.append((Ending, ClassName, UserName))
    Ordered = [
        (Index + 5, KFamilyClasses[type(Feature)], Feature.FeatureName)
        for Index, Feature in enumerate(SpecValue.Features)
    ]
    assert sorted(Timeline) == Ordered
    _, Stages = SolvePart(SpecValue)
    Expected = SolidMass(Stages[-1].After)
    Cached = MaterialFields(PartRecords(Model, "Body")[0]["cache"])
    assert Cached["volume"] == ApproxValue(Expected["volume"], rel=1e-12)
    assert Cached["area"] == ApproxValue(Expected["area"], rel=1e-12)
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert sorted(State.StateId for State in History.States) == [
        2,
        4,
        *(Stage.StateId for Stage in Stages),
    ]
    Target = TmpPath / "Reemitted.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    Reopened = ReadDocument(Target.read_bytes())
    assert Reopened.Segments == Model.Segments
    assert Reopened.Bodies == Model.Bodies
