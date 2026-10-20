# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from collections import Counter
from collections.abc import Mapping
from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath
from typing import cast as CastValue
import pytest as PytestLib
from convert.adapters.solidworks import (
    SldprtArchive,
    build_sldprt as BuildSldprt,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.core.Adapter import SldprtAdapter
from convert.adapters.solidworks.core.Adapter import (
    Companion as CompanionPayloads,
    MateGroups,
    MateInstance as MateInstancePath,
    MatePayload,
    NeutralMateKinA as NeutralMateKind,
)
from convert.adapters.solidworks.assembly.Assembly import (
    MateEntities,
    decode_mate_list as DecodeMateList,
    decode_native_assembly as DecodeNativeAssembly,
)
from interchange import (
    CadDocument,
    Capability,
    ComponentKind,
    MateAlignment,
    MateKind,
    ValueKind,
)

# centralizes shared evidence so every related assertion uses one value
KRandom = FilePath(__file__).resolve().parents[4] / "examples" / "Random"

# centralizes shared evidence so every related assertion uses one value
KAssembly = KRandom / "V8_engine.SLDASM"

# centralizes shared evidence so every related assertion uses one value
KConrod = KRandom / "Pistons" / "Conrod.SLDASM"

# identifies the external acis companion whose exact bytes define the golden evidence
KAcisCompanion = KRandom / "ACIS" / "V8_engine.SAT"

# identifies the external parasolid companion whose exact bytes define the golden evidence
KParaCompanion = KRandom / "Parasolid" / "V8_engine.x_t"

# distinguishes the canonical external corpus from locally normalized variants
KCompanionSizes = ((KAcisCompanion, 61518735), (KParaCompanion, 8036848))


# prevents another local corpus from being compared with canonical byte goldens
def HasCompanions() -> bool:
    return all(
        (PathInfo.is_file() and PathInfo.stat().st_size == ExpectedSize)
        for PathInfo, ExpectedSize in KCompanionSizes
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.fixture(scope="module")
def Document() -> CadDocument:
    if not KAssembly.is_file():
        PytestLib.skip("random assembly corpus is unavailable")
    return SldprtAdapter().read(KAssembly, ReadOptions(include_brep=False))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARHDAH(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert Document.validate() == ()
    assert len(Assembly.definitions) == 68
    assert Counter((Definition.kind for Definition in Assembly.definitions)) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    assert len(Assembly.instances) == 288
    assert Assembly.attributes["flattened_occurrence_count"] == 358
    assert len(Assembly.documents) == 53
    assert Assembly.attributes["linked_part_document_count"] == 51
    assert Assembly.attributes["linked_assembly_document_count"] == 2
    assert Assembly.attributes["linked_sketch_count"] == 391
    assert Assembly.attributes["linked_feature_count"] == 2147
    assert len(Document.sketches) == 3
    assert len(Document.feature_timeline) == 327
    assert (
        sum(
            (
                Feature.attributes["xml_tag"] == "Reference"
                for Feature in Document.feature_timeline
            )
        )
        == 278
    )
    assert len(Document.support_planes) == 6


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACRTDD(Document: CadDocument) -> None:
    assert Document.capabilities == frozenset(
        {
            Capability.ASSEMBLIES,
            Capability.ASSEMBLY_MATES,
            Capability.BODY_STRUCTURE,
            Capability.COMPONENT_DOCUMENTS,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.EXPRESSIONS,
            Capability.EXTERNAL_REFERENCES,
            Capability.NATIVE_PAYLOADS,
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
            Capability.SELECTIONS,
            Capability.SUPPORT_PLANES,
            Capability.TESSELLATION,
        }
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARETAS(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    RingInfo = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:223"
        )
    )
    assert RingInfo.transform.values == (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        46.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    Piston = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:217"
        )
    )
    assert Piston.transform.values[3] == PytestLib.approx(-1.209188127289168e-15)
    assert Piston.transform.values[7] == PytestLib.approx(79.99530923564971)
    assert Piston.transform.values[11] == PytestLib.approx(-79.99530923564954)
    FeatureItem = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:211"
        )
    )
    assert FeatureItem.attributes["native_feature_id"] == 24
    assert not FeatureItem.fixed
    assert all((not Instance.suppressed for Instance in Assembly.instances))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARRANML(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert len(Assembly.mates) == 632
    assert len(Assembly.mate_entities) == 1261
    assert Counter((MateInfo.kind for MateInfo in Assembly.mates)) == {
        MateKind.CONCENTRIC: 301,
        MateKind.COINCIDENT: 280,
        MateKind.CAM: 32,
        MateKind.BELT: 14,
        MateKind.LOCK: 3,
        MateKind.GEAR: 1,
        MateKind.DISTANCE: 1,
    }
    assert len(Assembly.mate_groups) == 3
    assert [len(Group.mate_ids) for Group in Assembly.mate_groups] == [6, 2, 9]
    assert Assembly.attributes["flattened_mate_occurrence_count"] == 765
    Payloads = [
        Payload
        for Payload in Document.brep_payloads
        if Payload.format_id == "solidworks.mates"
    ]
    assert [len(Payload.data or b"") for Payload in Payloads] == [2202551, 18893, 43184]
    DeclaredCount = 0
    for Payload in Payloads:
        CountValue = Payload.attributes["declared_count"]
        assert isinstance(CountValue, int)
        DeclaredCount += CountValue
    assert DeclaredCount == 638
    assert all(
        (MateInfo.attributes["native_payload_id"] for MateInfo in Assembly.mates)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARDMVAA(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    Distance = next(
        (MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.DISTANCE)
    )
    assert Distance.name == "Distance1"
    assert Distance.value is not None
    assert Distance.value.value == PytestLib.approx(20.0)
    assert Distance.value.kind == ValueKind.LENGTH
    assert Distance.value.unit == "mm"
    assert Distance.alignment == MateAlignment.ANTI_ALIGNED
    assert not Distance.suppressed
    assert Distance.attributes["native_alignment_code"] == 2
    assert Distance.attributes["native_value_m"] == PytestLib.approx(0.02)
    assert Distance.attributes["native_value_offset"] == 1640514
    GearInfo = next(
        (MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.GEAR)
    )
    assert GearInfo.value is not None
    assert GearInfo.value.value == PytestLib.approx(1.0)
    assert GearInfo.value.kind == ValueKind.NUMBER
    NativeDimensionsValue = GearInfo.attributes["native_dimensions"]
    assert isinstance(NativeDimensionsValue, tuple)
    NativeDimensions = CastValue(tuple[object, ...], NativeDimensionsValue)
    DimensionNames: list[str] = []
    for DimensionInfo in NativeDimensions:
        assert isinstance(DimensionInfo, Mapping)
        DimensionMap = CastValue(Mapping[str, object], DimensionInfo)
        NameValue = DimensionMap.get("name")
        assert isinstance(NameValue, str)
        DimensionNames.append(NameValue)
    assert DimensionNames == ["D1", "D2"]
    assert GearInfo.alignment == MateAlignment.UNKNOWN
    Belts = [MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.BELT]
    assert all((MateInfo.alignment == MateAlignment.UNKNOWN for MateInfo in Belts))
    for MateInfo in Belts:
        MateValue = MateInfo.value
        assert MateValue is not None
        BeltDimensionsValue = MateInfo.attributes["native_dimensions"]
        assert isinstance(BeltDimensionsValue, tuple)
        BeltDimensions = CastValue(tuple[object, ...], BeltDimensionsValue)
        assert len(BeltDimensions) >= 2
        FirstDimension = BeltDimensions[0]
        SecondDimension = BeltDimensions[1]
        assert isinstance(FirstDimension, Mapping)
        assert isinstance(SecondDimension, Mapping)
        FirstMap = CastValue(Mapping[str, object], FirstDimension)
        SecondMap = CastValue(Mapping[str, object], SecondDimension)
        FirstValue = FirstMap.get("value")
        SecondValue = SecondMap.get("value")
        assert isinstance(FirstValue, (int, float))
        assert isinstance(SecondValue, (int, float))
        assert MateValue.value == PytestLib.approx(FirstValue / SecondValue)


# keeps rename recovery isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestMTRNM() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldName = "Concentric1".encode("utf-16le")
    NewName = "CustomMate1".encode("utf-16le")
    NameOffset = RecordInfo.data.index(OldName)
    Renamed = (
        RecordInfo.data[:NameOffset]
        + NewName
        + RecordInfo.data[NameOffset + len(OldName) :]
    )
    RenamedList = DecodeMateList(Renamed, RecordInfo.name, 7)
    assert RenamedList.mates[0].name == "CustomMate1"
    assert RenamedList.mates[0].kind == "concentric"
    assert RenamedList.mates[0].class_name == "moMateConcentric"


# keeps unknown class handling isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestMTUNKCLS() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldClass = b"moMateConcentric"
    NewClass = b"moMateVendorType"
    OriginalClassOffset = RecordInfo.data.index(OldClass)
    UnknownClass = (
        RecordInfo.data[:OriginalClassOffset]
        + NewClass
        + RecordInfo.data[OriginalClassOffset + len(OldClass) :]
    )
    UnknownClassList = DecodeMateList(UnknownClass, RecordInfo.name, 7)
    assert UnknownClassList.mates[0].name == "Concentric1"
    assert UnknownClassList.mates[0].kind == "native"


# keeps future class payloads isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestMTFUTPAY() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldName = "Concentric1".encode("utf-16le")
    NewName = "CustomMate1".encode("utf-16le")
    NameOffset = RecordInfo.data.index(OldName)
    Renamed = (
        RecordInfo.data[:NameOffset]
        + NewName
        + RecordInfo.data[NameOffset + len(OldName) :]
    )
    ClassOffset = Renamed.index(b"moMateConcentric")
    Future = Renamed[:ClassOffset] + b"moMateVendorType" + Renamed[ClassOffset + 16 :]
    FutureList = DecodeMateList(Future, RecordInfo.name, 7)
    MateInfo = FutureList.mates[0]
    assert MateInfo.name == "CustomMate1"
    assert MateInfo.kind == "native"
    assert MateInfo.class_name == "moMateVendorType"
    assert MateInfo.serialized_strings[0] == "CustomMate1"
    assert NeutralMateKind(MateInfo.kind) == MateKind.NATIVE
    Payload = MatePayload("future", RecordInfo.name, Future, FutureList, 7, "fixture")
    assert Payload.data == Future
    PayloadRecordsValue = Payload.attributes["records"]
    assert isinstance(PayloadRecordsValue, tuple)
    PayloadRecords = CastValue(tuple[object, ...], PayloadRecordsValue)
    assert PayloadRecords
    FirstRecord = PayloadRecords[0]
    assert isinstance(FirstRecord, Mapping)
    assert FirstRecord == {
        "name": "CustomMate1",
        "kind": "native",
        "class_name": "moMateVendorType",
        "class_token": None,
        "offset": MateInfo.record_offset,
        "length": MateInfo.record_length,
    }


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestRMCTSARI() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldName = "Coincident2".encode("utf-16le")
    NewName = "CustomMate2".encode("utf-16le")
    Offset = RecordInfo.data.index(OldName)
    Renamed = (
        RecordInfo.data[:Offset] + NewName + RecordInfo.data[Offset + len(OldName) :]
    )
    MateList = DecodeMateList(Renamed, RecordInfo.name, 7)
    MateInfo = MateList.mates[2]
    assert MateInfo.name == "CustomMate2"
    assert MateInfo.kind == "coincident"
    assert MateInfo.class_name == "moMateCoincident"
    assert MateInfo.class_token is not None


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KAssembly.is_file(), reason="random assembly corpus is unavailable"
)
def TestMGBAS() -> None:
    Archive = SldprtArchive.open(KAssembly)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    MateList = DecodeMateList(RecordInfo.data, RecordInfo.name, 7)
    MarkersA = [MateInfo for MateInfo in MateList.mates if MateInfo.kind == "group"]
    Renamed = ReplaceData(
        MateList,
        mates=tuple(
            (
                (
                    ReplaceData(MateInfo, name="Groupe sans suffixe")
                    if MateInfo.order == MarkersA[0].order
                    else (
                        ReplaceData(MateInfo, name="Terminaison locale")
                        if MateInfo.order == MarkersA[1].order
                        else MateInfo
                    )
                )
                for MateInfo in MateList.mates
            )
        ),
    )
    MateIds = {
        MateInfo.order: f"mate:{MateInfo.order}"
        for MateInfo in Renamed.mates
        if MateInfo.kind != "group"
    }
    Groups = MateGroups(Renamed, 7, MateIds, RecordInfo.name, "payload")
    assert Groups[0].name == "Groupe sans suffixe"
    assert Groups[0].mate_ids


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestCCPRWNS() -> None:
    Archive = SldprtArchive.open(KConrod)
    Native = DecodeNativeAssembly(Archive)
    Occurrence = next(
        (
            ItemValueA
            for ItemValueA in Native.occurrences
            if ItemValueA.owner_definition_id == Native.root_definition_id
        )
    )
    Owner = next(
        (
            ItemValueA
            for ItemValueA in Native.definitions
            if ItemValueA.object_id == Native.root_definition_id
        )
    )
    Identity = {
        ItemValueA.object_id: ItemValueA.object_id for ItemValueA in Native.occurrences
    }
    assert MateInstancePath(Native, Identity, f"{Occurrence.name}@{Owner.name}") == (
        Occurrence.object_id,
    )
    Entities = MateEntities(
        (
            "moFaceRef_c,1,2,3",
            f"{Occurrence.name}@{Owner.name}",
            Occurrence.name + ".SLDPRT",
        )
    )
    assert Entities[0].component_path == f"{Occurrence.name}@{Owner.name}"
    assert Entities[0].source_path == Occurrence.name + ".SLDPRT"


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KConrod.is_file(), reason="conrod assembly corpus is unavailable"
)
def TestMLDUSWTSIR() -> None:
    BlobInfo = KConrod.read_bytes()
    Archive = SldprtArchive.from_bytes(BlobInfo, KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    Streams = Archive.streams
    Streams["Relations/AssemblyConstraints"] = Streams.pop(RecordInfo.name)
    Renamed = SldprtArchive.from_bytes(
        BuildSldprt(
            Streams,
            file_id=Archive.file_id,
            format_version=Archive.format_version,
            template=BlobInfo,
        )
    )
    Native = DecodeNativeAssembly(Renamed)
    assert len(Native.mate_lists) == 1
    assert Native.mate_lists[0].stream == "Relations/AssemblyConstraints"
    assert len(Native.mate_lists[0].mates) == 13


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARERM(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert len(Document.meshes) == 65
    FaceCount = 0
    for MeshInfo in Document.meshes:
        FacesValue = MeshInfo.attributes["faces"]
        assert isinstance(FacesValue, tuple)
        FacesInfo = CastValue(tuple[object, ...], FacesValue)
        FaceCount += len(FacesInfo)
    assert FaceCount == 4391
    assert sum((len(MeshInfo.vertices) for MeshInfo in Document.meshes)) == 492148
    assert sum((len(MeshInfo.triangles) for MeshInfo in Document.meshes)) == 391218
    PartDefinitions = {
        Definition.id
        for Definition in Assembly.definitions
        if Definition.kind == ComponentKind.PART
    }
    MeshedDefinitions = {
        Definition.id for Definition in Assembly.definitions if Definition.mesh_ids
    }
    assert MeshedDefinitions == PartDefinitions


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNADPTOT(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    Nested = [
        Linked.document
        for Linked in Assembly.documents
        if Linked.document.source.format_id == "solidworks.sldasm"
    ]
    assert sorted((len(ItemValueA.feature_timeline) for ItemValueA in Nested)) == [
        27,
        29,
    ]
    MateCounts: list[int] = []
    for ItemValueA in Nested:
        NestedAssembly = ItemValueA.assembly
        assert NestedAssembly is not None
        MateCounts.append(len(NestedAssembly.mates))
        assert not NestedAssembly.documents
    assert sorted(MateCounts) == [6, 13]


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not HasCompanions(), reason="canonical assembly companion corpus unavailable"
)
def TestRACARE() -> None:
    Payloads = CompanionPayloads(str(KAssembly))
    assert [
        (Payload.format_id, len(Payload.data or b""), Payload.sha256)
        for Payload in Payloads
    ] == [
        (
            "acis.sat",
            61518735,
            "accecfe74a515d095c38b12b669546e54cc5d55308d6e1c8e0913dd6649e7017",
        ),
        (
            "parasolid.x_t",
            8036848,
            "00dc62be5c5adb9b9ff4c83ae3f674f5e1df07782c65f86b50987c8dde76dde3",
        ),
    ]
    assert Payloads[0].attributes["body_count"] == 391
