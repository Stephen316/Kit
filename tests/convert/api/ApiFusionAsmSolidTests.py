# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pytest as Pytest

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureDistExt import DistanceExtrude
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# repeated and nested occurrences instantiate one solid per reusable definition
@KRequiresCodec
def CheckAsmSolids() -> None:
    Archive = KStudyPath / "assembly-acc48a9dc05d" / "assembly.f3d"
    Document = OpenDocument(Archive, strict=False)
    Assembly = Document.assembly
    assert Assembly is not None and len(Assembly.documents) == 3
    assert Document.brep is None and Document.bodies == ()
    assert {
        Capability.KBodyStructure,
        Capability.KBrep,
        Capability.KComponentDocs,
    } <= Document.capabilities
    for Identity, NativeBodyId, Volume in (
        (202, "323", 603.185789489241),
        (330, "450", 226.1946710584652),
        (471, "591", 785.3981633974483),
    ):
        Definition = Assembly.definition(f"fusion-component-{Identity}")
        Child = Assembly.document(Definition.document_id)
        assert Child.brep is not None and Child.brep_payloads == ()
        (BodyValue,) = Child.bodies
        assert Definition.body_ids == (BodyValue.id,)
        assert (
            BodyValue.provenance is not None
            and BodyValue.provenance.native_id == NativeBodyId
        )
        assert BodyValue.topology.volume == Pytest.approx(Volume)
        assert Child.feature_timeline[-1].id == BodyValue.final_feature_id
    Steps = {
        int(Step.provenance.native_id): Step
        for Step in Document.feature_timeline
        if Step.provenance
    }
    assert isinstance(Steps[424].definition, DistanceExtrude)
    assert isinstance(Steps[565].definition, DistanceExtrude)
    assert Steps[424].attributes["fusion.extrude.authoring_occurrences"] == (253, 381)
    assert Steps[565].attributes["fusion.extrude.authoring_occurrences"] == (522,)
    Roots = Assembly.children(Assembly.root_definition_id)
    assert Roots[0].definition_id == Roots[2].definition_id
    assert len(Assembly.children(Roots[0].definition_id)) == 1
    assert Document.validate() == ()
    assert CadDocument.from_json(Document.to_json()) == Document


# geometry filtering preserves nested identities and excludes all analytic models
@KRequiresCodec
def CheckAsmFilter() -> None:
    Archive = KStudyPath / "assembly-acc48a9dc05d" / "assembly.f3d"
    Document = OpenDocument(Archive, strict=False, include_brep=False)
    assert Document.assembly is not None and len(Document.assembly.documents) == 3
    assert Capability.KBrep not in Document.capabilities
    assert all(
        Child.document.brep is None and Child.document.bodies
        for Child in Document.assembly.documents
    )
    assert Document.validate() == ()


# an unsupported active mirror keeps the occurrence graph without reconstructing stale seed geometry
@KRequiresCodec
def CheckAsmGuard() -> None:
    Archive = (
        KStudyPath / "mirrorassemblydatum-700af16e9fc6" / "nested_occurrence_yz.f3d"
    )
    Document = OpenDocument(Archive, strict=False)
    assert Document.assembly is not None and Document.assembly.instances
    assert (
        not Document.assembly.documents
        and not Document.bodies
        and Document.brep is None
    )
    assert any(
        Issue.code == "fusion.assembly.body_unsupported"
        for Issue in Document.diagnostics
    )
