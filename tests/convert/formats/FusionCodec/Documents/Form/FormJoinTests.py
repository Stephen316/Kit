from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Form.BreakBodyLink import (
    BreakBodyLink,
)
from tests.convert.formats.FusionCodec.Documents.Form.FormArchives import (
    KFormArchives,
)
from tests.convert.formats.FusionCodec.Documents.Form.ReadFormFile import (
    ReadFormFile,
)


def ReadPlaneDoc() -> DocumentModel:
    CaseValue = next(
        Value for Value in KFormArchives if Value[0].endswith("vendor_PlaneControl.f3d")
    )
    return ReadDocument(ReadFormFile(*CaseValue))


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Form archive requires ZIP Zstandard"
)
@MarkTests.parametrize("Fault", ("name", "program", "missing", "body"))
def TestFormJoins(Fault: str) -> None:
    Model = ReadPlaneDoc()
    FormValue = Model.Forms[0]
    if Fault == "name":
        Changed = ReplaceValue(
            FormValue,
            Name="TSplines.BlobParts/TSpline.00000000-0000-4000-8000-000000000000.tsm",
        )
        Model = ReplaceValue(Model, Forms=(Changed,))
    elif Fault == "program":
        Grips = list(FormValue.Surface.Grips)
        Grips[0] = ReplaceValue(Grips[0], CoordZ=Grips[0].CoordZ + 0.25)
        Surface = ReplaceValue(FormValue.Surface, Grips=tuple(Grips))
        Model = ReplaceValue(Model, Forms=(ReplaceValue(FormValue, Surface=Surface),))
    elif Fault == "missing":
        Model = ReplaceValue(Model, Forms=())
    else:
        Model = BreakBodyLink(Model)
    with RaisesError(ValueError):
        _ = EmitParsed(Model)
