from dataclasses import replace as Replace
from io import BytesIO

import pytest as Pytest

from convert import (
    ApplicationUsabilityError,
    write_document as WriteDocument,
)
from convert.adapters.base.TransferContract import CarrierReason
from tests.convert.FusionRead import OpenResearch as OpenDocument
from interchange.enums.EnumDocument import Capability
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordParameter import Expression
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.interchange.document.BoundPlaneTests import PlaneDocument

# standalone controls come from the measured fusion origin plane captures
KDatumCases = KStudyPath / "planedefinitions-6cd0820a832e"


# native history receives strict credit only for the live datum writer route
@Pytest.mark.parametrize("Method", ("offset", "angle"))
def TestDatumMove(Method: str) -> None:
    Datum = PlaneDocument(Method)
    Scalar, Extra = Datum.parameters
    Literal = "90 deg" if Method == "angle" else "-25 mm"
    Source = Replace(
        Datum, parameters=(Replace(Scalar, expression=Expression(Literal)), Extra)
    )
    Target = BytesIO()
    Result = WriteDocument(
        Source, Target, destination_format="freecad.fcstd", allow_carrier=False
    )
    assert Result.application_usable and Result.vendor_loadable
    assert Capability.PARAMETRIC_HISTORY in Result.native_capabilities
    assert Capability.PARAMETRIC_HISTORY not in Result.carrier_capabilities
    assert OpenDocument(Target.getvalue(), SourceFormat="freecad.fcstd") == Source


# a dependent sketch cannot be silently detached by a standalone datum export
def TestDatumDeps() -> None:
    Datum = PlaneDocument("offset")
    Source = Replace(Datum, sketches=(Sketch("sketch", "Dependent", "datum", ()),))
    assert Source.validate() == ()
    Target = BytesIO()
    Result = WriteDocument(Source, Target, destination_format="freecad.fcstd")
    (History,) = tuple(
        Value
        for Value in Result.transfers
        if Value.capability == Capability.PARAMETRIC_HISTORY
    )
    assert History.carrier_reason is CarrierReason.WRITER_UNIMPLEMENTED
    Strict = BytesIO()
    with Pytest.raises(ApplicationUsabilityError) as Captured:
        _ = WriteDocument(
            Source, Strict, destination_format="freecad.fcstd", allow_carrier=False
        )
    assert "unimplemented_translation" in Captured.value.issues
    assert not Strict.getvalue()


# transferring an editable plane preserves the opaque archive gate on its fusion source
@KRequiresCodec
def TestFusionDatum() -> None:
    Document = OpenDocument(KDatumCases / "offset.f3d", StrictMode=False)
    LiveValue = BytesIO()
    Result = WriteDocument(Document, LiveValue, destination_format="freecad.fcstd")
    assert Capability.PARAMETRIC_HISTORY in Result.native_capabilities
    Strict = BytesIO()
    with Pytest.raises(ApplicationUsabilityError) as Captured:
        _ = WriteDocument(
            Document, Strict, destination_format="freecad.fcstd", allow_carrier=False
        )
    assert "opaque_source_data" in Captured.value.issues
    assert not Strict.getvalue()
