from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory
from xml.etree.ElementTree import Element, fromstring as ParseXml
from zipfile import ZipFile

import pytest as Pytest

from convert import write_document as WriteDocument
from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import (
    PlaneRevPlan,
    ReadPlaneRev,
)
from convert.adapters.freecad.EditRead.PlaneRev.ReadPlaneRevFields import (
    ReadPlaneRevFields,
)
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# the generated two plane archive provides an independent native graph mutation baseline
def ReadPlaneSeed() -> tuple[Element, CadDocument, PlaneRevPlan]:
    Source = KStudyPath / "revolveto-b1d196f65c46" / "two_planes.f3d"
    DocValue = OpenDocument(Source, StrictMode=False)
    PlanValue = ReadPlaneRev(DocValue, DocValue.feature_timeline[-1])
    assert PlanValue is not None
    with TempDirectory() as Folder:
        Destination = FilePath(Folder) / "plane.FCStd"
        _ = WriteDocument(DocValue, Destination, allow_carrier=True)
        with ZipFile(Destination) as Archive:
            return ParseXml(Archive.read("Document.xml")), DocValue, PlanValue


# pristine saved controls retain exact parameter values without requiring a solved cache
@KRequiresCodec
def CheckPlaneSeed() -> None:
    RootValue, DocValue, PlanValue = ReadPlaneSeed()
    Fields = ReadPlaneRevFields(RootValue, DocValue, PlanValue)
    assert Fields.ProfileSketch is DocValue.sketches[0]
    assert Fields.SketchEntry == ""
    assert Fields.AngleEdits == {
        Target.AngleParamId: (
            Target.AngleRadians,
            "45 deg" if Index == 0 else "-35 deg",
        )
        for Index, Target in enumerate(PlanValue.Targets)
    }


# a stale live link or value cannot be treated as an authoritative neutral edit
@KRequiresCodec
@Pytest.mark.parametrize(
    ("ObjectName", "Field", "ChildPath", "Attribute", "Replacement", "Reason"),
    (
        (
            "Feature_2",
            "ConstructionPlane",
            "Link",
            "value",
            "ToPlane_35",
            "ConstructionPlane link",
        ),
        (
            "target_one",
            "Selection",
            "LinkSubList/Link",
            "obj",
            "ToPlane_35",
            "target selection",
        ),
        (
            "Parameters",
            "cells",
            "Cells/Cell[@alias='fusion_parameter_262']",
            "content",
            "=1 mm",
            "inactive control changed",
        ),
        (
            "ToPlane45",
            "Placement",
            "PropertyPlacement",
            "Py",
            "99",
            "placement changed",
        ),
        (
            "ToPlane45",
            "ExpressionEngine",
            "ExpressionEngine/Expression",
            "expression",
            "Parameters.fusion_parameter_274",
            "expression binding changed",
        ),
        ("ProbeRevolveTo", "Angle", "Float", "value", "135", "angle disagrees"),
        ("ProbeRevolveTo", "Axis", "PropertyVector", "valueY", "1", "Axis changed"),
    ),
)
def CheckPlaneGuard(
    ObjectName: str,
    Field: str,
    ChildPath: str,
    Attribute: str,
    Replacement: str,
    Reason: str,
) -> None:
    RootValue, DocValue, PlanValue = ReadPlaneSeed()
    NodeValue = RootValue.find(
        f"./ObjectData/Object[@name='{ObjectName}']/Properties/"
        + f"Property[@name='{Field}']/{ChildPath}"
    )
    assert NodeValue is not None
    NodeValue.set(Attribute, Replacement)
    with Pytest.raises(ValueError, match=Reason):
        _ = ReadPlaneRevFields(RootValue, DocValue, PlanValue)
