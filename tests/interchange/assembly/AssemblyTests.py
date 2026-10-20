# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceValue
from interchange import (
    CadDocument,
    SpaceVector,
)
from interchange.mesh.SurfaceMesh import SurfaceMesh
from tests.interchange.document.DocumentTests import BuildDocument
from tests.interchange.fixtures.AssemblyFixture import (
    BuildAssembly as BuildFixtureAssembly,
)


# behavior coverage protects portable interchange semantics during structural refactors
def BuildAssembly() -> CadDocument:
    return BuildFixtureAssembly()


# historical imports keep conversion suites independent from helper renaming
assembly_document = BuildAssembly


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildAssembly()
    SourceValue.assert_valid()
    RestoredValue = CadDocument.from_json(SourceValue.to_json())
    assert RestoredValue == SourceValue
    assert RestoredValue.assembly is not None
    EmbeddedValue = RestoredValue.assembly.GetDocument("document:part")
    assert isinstance(EmbeddedValue, CadDocument)
    assert EmbeddedValue == BuildDocument()
    assert RestoredValue.assembly.GetChildren("definition:root") == (
        RestoredValue.assembly.instances[0],
    )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckMeshRound() -> None:
    SourceValue = BuildAssembly()
    AssemblyValue = SourceValue.assembly
    assert AssemblyValue is not None
    MeshValue = SurfaceMesh(
        "mesh:1",
        "Piston face",
        (
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
            SpaceVector(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
        normals=(SpaceVector(0.0, 0.0, 1.0),) * 3,
    )
    Definitions = tuple(
        (
            (
                ReplaceValue(DefinitionValue, mesh_ids=(MeshValue.id,))
                if DefinitionValue.id == "definition:part"
                else DefinitionValue
            )
            for DefinitionValue in AssemblyValue.definitions
        )
    )
    ExtendedValue = ReplaceValue(
        SourceValue,
        meshes=(MeshValue,),
        assembly=ReplaceValue(AssemblyValue, definitions=Definitions),
    )
    ExtendedValue.assert_valid()
    RestoredValue = CadDocument.from_json(ExtendedValue.to_json())
    assert RestoredValue == ExtendedValue
