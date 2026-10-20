# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceData
from io import BytesIO
from pathlib import Path as FilePath
from convert import write_document as WriteDocument
from convert.adapters.solidworks.core.Adapter import (
    GeneratedB as GeneratedStreams,
    KAsmReaderRequiredStreams as Streams,
    Native as NativeAttestation,
    Replay as ReplayCompatibility,
    write_sldprt as WriteSldprt,
)
from convert.adapters.solidworks.assembly.Assembly import (
    KMateAdvisoryLossReasons as Reasons,
    KMateBlockingLossReasons as ReasonsA,
    KMateLossEntityFrame as Frame,
    KMateLossExpression as Expression,
    KMateLossValueMissing as Missing,
    NativeAssemblyEncoding,
    encode_native_assembly as EncodeNativeAssembly,
)
from convert.adapters.solidworks.container.Container import SldprtArchive
from interchange import (
    Capability,
    CadDocument,
    MateAlignment,
    MateKind,
    Matrix4 as MatrixFour,
    ParameterValue,
    frozen_mapping as FrozenMapping,
)
from tests.interchange.assembly.AssemblyTests import (
    assembly_document as AssemblyDocument,
)

# centralizes shared evidence so every related assertion uses one value
KStreams = (
    "Contents/CMgr",
    "Contents/CMgrHdr2",
    "Contents/CnfgObjs",
    "Contents/Config-0",
    "Contents/Config-0-Attachment",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/CusProps",
    "Contents/Definition",
    "Contents/OleItems",
    "Contents/View Orientation Data",
    "Contents/eModelLic",
    "Header2",
    "ModelStamps",
    "_MO_VERSION_18000/AssyVisualData",
    "_MO_VERSION_18000/Biography",
    "_MO_VERSION_18000/History",
    "docProps/Config-0-Cutlist-Properties.xml",
    "docProps/Config-0-Properties.xml",
    "docProps/OpenTime.xml",
    "swXmlContents/Tables",
)

# centralizes shared evidence so every related assertion uses one value
KMateInfo = "moPlaneSurfIdRep_c,1,2, "

# centralizes shared evidence so every related assertion uses one value
KMateInfoA = "moPlaneSurfIdRep_c,3,4, "


# keeps this focused behavior isolated so regressions remain immediately visible
def PersistentMD(
    *,
    KindValue: MateKind | str | None = None,
    ValueData: ParameterValue | None = None,
    ParamIds: tuple[str, ...] | None = None,
) -> CadDocument:
    SourceDoc = AssemblyDocument()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    RootEntity, ComponentEntity = Assembly.mate_entities
    RootEntity = ReplaceData(
        RootEntity,
        source_entity_id=KMateInfoA,
        attributes=FrozenMapping({"persistent_references": (KMateInfoA,)}),
    )
    ComponentEntity = ReplaceData(
        ComponentEntity,
        source_entity_id=KMateInfo,
        attributes=FrozenMapping({"persistent_references": (KMateInfo,)}),
    )
    MateInfo = ReplaceData(
        Assembly.mates[0],
        entity_ids=(ComponentEntity.EntityId, RootEntity.EntityId),
        alignment=MateAlignment.ALIGNED,
    )
    if KindValue is not None:
        MateInfo = ReplaceData(MateInfo, kind=KindValue)
    if ValueData is not None:
        MateInfo = ReplaceData(MateInfo, value=ValueData)
    if ParamIds is not None:
        MateInfo = ReplaceData(MateInfo, parameter_ids=ParamIds)
    return ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            mate_entities=(ComponentEntity, RootEntity),
            mates=(MateInfo,),
        ),
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def Encode(SourceDoc: CadDocument) -> NativeAssemblyEncoding:
    Assembly = SourceDoc.Assembly
    assert Assembly is not None
    return EncodeNativeAssembly(Assembly, SourceDoc.Configurations, "Engine")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAETFESG() -> None:
    Generated = GeneratedStreams(AssemblyDocument())
    for NameText in KStreams:
        assert NameText in Generated.streams
    assert "swXmlContents/COMPINSTANCETREE" in Generated.streams
    assert Generated.streams["Contents/OleItems"] == b"\x00\x00\x00\x00"
    assert Generated.streams["Contents/eModelLic"] == b"\x00\x00\x00\x00"
    assert Generated.streams["Contents/Config-0-Attachment"] == b"\x00\x00"
    assert Generated.streams["_MO_VERSION_18000/AssyVisualData"] == b"\x00\x00\x00\x00"
    assert Generated.streams["swXmlContents/Tables"] == b""
    assert b"moAssyFilePropContainer_c" in Generated.streams["Contents/CusProps"]
    assert (
        Generated.streams["docProps/Config-0-Cutlist-Properties.xml"]
        == b'<Configuration id="0" Name="Default"/>\r\n'
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAHITCNHH() -> None:
    Generated = GeneratedStreams(AssemblyDocument())
    assert (
        Generated.streams["Header2"]
        == Generated.streams["Contents/Config-0-ModelHeader"]
    )
    assert len(Generated.streams["Header2"]) > 2000
    assert "Engine".encode("utf-16le") in Generated.streams["Header2"]
    assert "Piston-1".encode("utf-16le") in Generated.streams["Header2"]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFCFC() -> None:
    SourceData = AssemblyDocument()
    AssemblyValue = SourceData.assembly
    assert AssemblyValue is not None
    FixedData = ReplaceData(
        SourceData,
        assembly=ReplaceData(
            AssemblyValue,
            instances=(
                ReplaceData(AssemblyValue.instances[0], fixed=True),
                *AssemblyValue.instances[1:],
            ),
        ),
    )
    GeneratedData = GeneratedStreams(FixedData)
    assert GeneratedData.vendor_loadable is False
    assert GeneratedData.application_usable is False
    assert GeneratedData.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in GeneratedData.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAIVLWNRG() -> None:
    Output = BytesIO()
    ResultInfo = WriteSldprt(AssemblyDocument(), Output)
    assert ResultInfo.IsVendorLoadable is True
    assert ResultInfo.IsAppUsable is False
    assert ResultInfo.MetadataMap["compatibility"] == "native-assembly-with-kit-neutral"
    assert ResultInfo.MetadataMap["native_assembly"] is True
    assert ResultInfo.MetadataMap["native_self_contained"] is False
    assert all(
        (
            ItemValueA.code != "sldasm.vendor_reader_rejects"
            for ItemValueA in ResultInfo.Diagnostics
        )
    )
    for NameText in Streams:
        assert NameText in SldprtArchive.from_bytes(Output.getvalue()).streams


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAARIOC() -> None:
    Output = BytesIO()
    _ = WriteSldprt(AssemblyDocument(), Output)
    DataValue = Output.getvalue()
    Attestation = NativeAttestation(DataValue)
    assert Attestation is not None
    assert Attestation["compatibility"] == "native-assembly-with-kit-neutral"
    assert Attestation["vendor_loadable"] is True
    assert Attestation["application_usable"] is False
    assert ReplayCompatibility(DataValue) == "native-assembly-with-kit-neutral"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPABHNSP(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "final" / "Engine.SLDASM"
    _ = WriteDocument(AssemblyDocument(), OutputPath)
    HeaderData = b"".join(
        (
            SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
            for PathValue in OutputPath.parent.iterdir()
            if PathValue.suffix.casefold() == ".sldasm"
        )
    )
    assert ".kit-".encode("utf-16le") not in HeaderData
    assert str(OutputPath.parent.resolve()).encode("utf-16le") in HeaderData
    MemberPath = next(
        (
            PathValue
            for PathValue in OutputPath.parent.iterdir()
            if PathValue != OutputPath
        )
    )
    _ = MemberPath.write_bytes(b"stale")
    _ = WriteDocument(AssemblyDocument(), OutputPath, overwrite=True)
    assert MemberPath.read_bytes() != b"stale"
    HeaderData = b"".join(
        (
            SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
            for PathValue in OutputPath.parent.iterdir()
            if PathValue.suffix.casefold() == ".sldasm"
        )
    )
    for MemberPath in OutputPath.parent.iterdir():
        if MemberPath == OutputPath:
            continue
        StampData = SldprtArchive.open(MemberPath).streams["ModelStamps"]
        assert StampData[:4] in HeaderData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestICSWVL() -> None:
    SourceDoc = AssemblyDocument()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    Broken = ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            definitions=(
                ReplaceData(Assembly.definitions[0]),
                ReplaceData(Assembly.definitions[1], kind="drawing"),
                Assembly.definitions[2],
            ),
        ),
    )
    Generated = GeneratedStreams(Broken)
    assert Generated.vendor_loadable is False
    assert Generated.application_usable is False
    assert Generated.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in Generated.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAMLDNVTNMR() -> None:
    SourceDoc = PersistentMD()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    Framed = ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            mate_entities=(
                ReplaceData(
                    Assembly.mate_entities[0],
                    frame=MatrixFour(
                        (
                            1.0,
                            0.0,
                            0.0,
                            5.0,
                            0.0,
                            1.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            1.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            1.0,
                        )
                    ),
                ),
                Assembly.mate_entities[1],
            ),
            mates=(
                ReplaceData(Assembly.mates[0], parameter_ids=("parameter:offset",)),
            ),
        ),
    )
    Encoding = Encode(Framed)
    ReasonsD = {
        Reason
        for ValueList in Encoding.generated_mate_losses.values()
        for Reason in ValueList
    }
    assert Frame in ReasonsD
    assert Expression in ReasonsD
    assert ReasonsD <= Reasons
    assert Encoding.mates_complete is True
    assert Encoding.unsupported_mate_ids == ()
    Generated = GeneratedStreams(Framed)
    assert Capability.ASSEMBLY_MATES in Generated.native_capabilities
    assert Generated.compatibility == "native-assembly-with-kit-neutral"
    assert "component_structure_incomplete:1" not in Generated.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBMVLVTNMR() -> None:
    Blocked = PersistentMD(KindValue=MateKind.DISTANCE, ValueData=None)
    Encoding = Encode(Blocked)
    ReasonsD = {
        Reason
        for ValueList in Encoding.generated_mate_losses.values()
        for Reason in ValueList
    }
    assert ReasonsD == {Missing}
    assert Missing in ReasonsA
    assert Encoding.mates_complete is False
    Generated = GeneratedStreams(Blocked)
    assert Capability.ASSEMBLY_MATES not in Generated.native_capabilities
    assert Generated.application_usable is False
