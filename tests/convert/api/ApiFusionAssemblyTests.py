# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as LoadJson
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

import pytest as Pytest

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability

# public tests use vendor saved inputs and independently captured placements
KStudyPath = FilePath(__file__).resolve().parents[3] / "re" / "Fusion" / "Study"

# native inputs require the standard library archive codec in the public reader
KRequiresCodec = Pytest.mark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)


# only translation values change when converting a native matrix to document units
def ConvertPlacement(Matrix: list[float]) -> tuple[float, ...]:
    return tuple(
        Value * 10.0 if Index in (3, 7, 11) else Value
        for Index, Value in enumerate(Matrix)
    )


# repeated subassemblies retain native topology and reproduce saved proxy placements
@KRequiresCodec
def CheckAssemblyRead() -> None:
    Folder = KStudyPath / "assembly-acc48a9dc05d"
    InputPath = Folder / "assembly.f3d"
    Oracle = LoadJson((Folder / "ground_truth.json").read_text(encoding="utf-8"))
    Document = OpenDocument(InputPath, strict=False, include_brep=False)
    Assembly = Document.assembly
    assert Assembly is not None and Capability.KAssemblies in Document.capabilities
    assert len(Assembly.definitions) == len(Assembly.instances) == 4
    assert {Definition.name for Definition in Assembly.definitions} == {
        "(Unsaved)",
        "ComponentA",
        "ComponentB",
        "ComponentC",
    }
    assert {
        Definition.attributes["fusion.history_id"]
        for Definition in Assembly.definitions
    } == {35, 233, 361, 502}
    assert Document.metadata["fusion.history_id"] == 35
    assert len(Document.feature_timeline) == len(Oracle["timeline"])
    Children = Assembly.children(Assembly.root_definition_id)
    assert [Item.name for Item in Children] == [
        "ComponentA:1",
        "ComponentC:1",
        "ComponentA:2",
    ]
    assert Children[0].definition_id == Children[2].definition_id
    assert len(Assembly.children(Children[0].definition_id)) == 1
    for Occurrence in Oracle["occurrences"]:
        NameParts = Occurrence["path"].split("+")
        Parent = next(Item for Item in Children if Item.name == NameParts[0])
        if len(NameParts) == 1:
            Local = Parent
            World = Parent.transform.values
        else:
            (Local,) = Assembly.children(Parent.definition_id)
            World = tuple(
                sum(
                    Parent.transform.values[Row * 4 + Index]
                    * Local.transform.values[Index * 4 + Column]
                    for Index in range(4)
                )
                for Row in range(4)
                for Column in range(4)
            )
        assert Local.name == Occurrence["name"]
        assert Local.transform.values == Pytest.approx(
            ConvertPlacement(Occurrence["native_transform2"])
        )
        assert World == Pytest.approx(ConvertPlacement(Occurrence["transform2"]))
    assert Document.validate() == ()
    assert CadDocument.from_json(Document.to_json()) == Document
    assert Document.brep_payloads[0].data == InputPath.read_bytes()
    ChildDoc = OpenDocument(InputPath, strict=False, configuration="233")
    assert ChildDoc.assembly is None and ChildDoc.feature_timeline == ()
    assert ChildDoc.metadata["fusion.history_id"] == 233


# joint cached transforms are not substituted for independently solved placements
@KRequiresCodec
def CheckJointPlacement() -> None:
    InputPath = KStudyPath / "jointmodes-20d3aef2a07d" / "slider.f3d"
    with Pytest.raises(ValueError, match="Select exactly one Fusion history"):
        OpenDocument(InputPath, strict=False)
    HistoryDoc = OpenDocument(InputPath, strict=False, configuration="35")
    assert HistoryDoc.assembly is None
