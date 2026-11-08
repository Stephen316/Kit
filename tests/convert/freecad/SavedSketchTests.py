# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterator
from contextlib import contextmanager as ContextManager
from pathlib import Path as FilePath
from xml.etree.ElementTree import Element, fromstring as ParseXml, tostring as XmlBytes
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.EditSketchPlan import KSketchEditBinding
from interchange.document.models.DocumentModel import CadDocument

# the native fusion radius capture supplies real sketch and parameter identities
KRadiusSource = (
    FilePath(__file__).parents[3] / "re/Fusion/Study/sketches-0ccea2ac0f9c/radius.f3d"
)


# each control starts from a marked archive emitted by the public writer
@Pytest.fixture
def BoundSketch(TmpPath: FilePath) -> tuple[CadDocument, FilePath]:
    Document = OpenDocument(KRadiusSource, strict=False)
    Output = TmpPath / "bound.FCStd"
    _ = WriteDocument(Document, Output)
    return Document, Output


# native save retains the xml manifest without the companion zip manifest
@ContextManager
def SavedXml(Original: FilePath, Target: FilePath) -> Iterator[Element]:
    with ZipFile(Original) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    yield RootValue
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Document.xml", XmlBytes(RootValue, encoding="utf-8"))


# the generated sketch scope preserves an unchanged source document exactly
def TestBoundSketch(BoundSketch: tuple[CadDocument, FilePath]) -> None:
    Document, Output = BoundSketch
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    Marker = RootValue.find(f".//Property[@name='{KSketchEditBinding}']/String")
    assert Marker is not None and Marker.get("value") == "Sketches"
    assert OpenDocument(Output) == Document


# coherent geometry must still have its saved shape while stale quantities fail earlier
@Pytest.mark.parametrize(
    ("ChangeMode", "Reason"),
    (
        ("stale", "disagrees with its parameter"),
        ("uncached", "has no saved shape"),
        ("missing rule", "constraint count"),
    ),
)
def TestSketchProof(
    BoundSketch: tuple[CadDocument, FilePath], ChangeMode: str, Reason: str
) -> None:
    _, Output = BoundSketch
    Target = Output.with_name("proof.FCStd")
    with SavedXml(Output, Target) as RootValue:
        Cell = RootValue.find(".//Cell[@alias='fusion_parameter_297']")
        Circle = RootValue.find(".//Geometry/Circle")
        Rules = RootValue.find(".//Property[@name='Constraints']/ConstraintList")
        assert Cell is not None and Circle is not None and Rules is not None
        Datum = Rules.find("./Constrain[@Type='11']")
        assert Datum is not None
        if ChangeMode == "missing rule":
            Rules.remove(Datum)
            Rules.set("count", str(len(Rules)))
        else:
            Cell.set("content", "=18 mm")
            if ChangeMode == "uncached":
                Circle.set("Radius", "18")
                Datum.set("Value", "18")
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        OpenDocument(Target)


# earlier unbound sketch archives retain their compatibility as source snapshots
def TestLegacySave(BoundSketch: tuple[CadDocument, FilePath]) -> None:
    Document, Output = BoundSketch
    Target = Output.with_name("legacy.FCStd")
    with SavedXml(Output, Target) as RootValue:
        Props = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
        assert Props is not None
        Marker = Props.find(f"./Property[@name='{KSketchEditBinding}']")
        assert Marker is not None
        Props.remove(Marker)
        Props.set("Count", str(int(Props.attrib["Count"]) - 1))
    assert OpenDocument(Target) == Document
