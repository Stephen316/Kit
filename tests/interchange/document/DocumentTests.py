# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange.payloads.PayloadRoles import PayloadRole
from dataclasses import is_dataclass as IsDataClass
from dataclasses import replace as ReplaceValue
from enum import Enum as EnumBase
import hashlib as HashCodec
from importlib import import_module as ImportModule
import os as OsSystem
from pathlib import Path as FilePath
import subprocess as Subprocess
import sys as System
import pytest as PytestLib
from interchange import (
    CadDocument,
    Capability,
    PayloadRole,
)
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.TypeRegistry import KTypeRegistry
from tests.interchange.fixtures.DocumentFixture import (
    BuildDocument as BuildFixtureDocument,
)

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
def BuildDocument() -> CadDocument:
    return BuildFixtureDocument()


# historical imports keep conversion suites independent from helper renaming
document = BuildDocument


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRoundtrip() -> None:
    SourceValue = BuildDocument()
    RestoredValue = CadDocument.from_json(SourceValue.to_json())
    assert RestoredValue == SourceValue
    assert isinstance(RestoredValue.capabilities, frozenset)
    assert isinstance(RestoredValue.feature_timeline, tuple)


# behavior coverage protects portable interchange semantics during structural refactors
def CheckStableJson() -> None:
    PayloadValue = BuildDocument().to_json(indent=None)
    SourceRoot = FilePath(__file__).parents[3] / "src"
    ScriptText = f"from interchange import CadDocument;print(CadDocument.from_json({PayloadValue!r}).to_json(indent=None))"
    OutputValues = {
        Subprocess.check_output(
            [System.executable, "-c", ScriptText],
            cwd=SourceRoot.parent,
            env={**OsSystem.environ, "PYTHONHASHSEED": str(SeedValue)},
            text=True,
        )
        for SeedValue in (1, 7, 31)
    }
    assert len(OutputValues) == 1


# behavior coverage protects portable interchange semantics during structural refactors
def CheckRegistry() -> None:
    ExpectedValues = {
        ItemValue
        for NameValue in KInterchangeApi.__all__
        for ItemValue in (getattr(KInterchangeApi, NameValue),)
        if isinstance(ItemValue, type)
        and (IsDataClass(ItemValue) or issubclass(ItemValue, EnumBase))
    }
    assert set(KTypeRegistry.values()) == ExpectedValues


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize("RoleValue", tuple(PayloadRole))
def CheckPayRole(RoleValue: PayloadRole) -> None:
    PayloadValue = BrepPayload(
        "geometry",
        "future.kernel",
        "custom",
        "v1",
        "0" * 64,
        data=b"geometry",
        role=RoleValue,
        file_extension=".geo",
    )
    RestoredValue = CadDocument.from_json(
        ReplaceValue(BuildDocument(), brep_payloads=(PayloadValue,)).to_json()
    )
    assert RestoredValue.brep_payloads == (PayloadValue,)


# behavior coverage protects portable interchange semantics during structural refactors
@PytestLib.mark.parametrize(
    (
        "FormatId",
        "KindValue",
        "SchemaText",
        "SourceStream",
        "RoleValue",
        "ExtensionText",
    ),
    (
        ("parasolid", "binary", "SCH_3500040", "Partition", PayloadRole.KBrep, ".x_b"),
        (
            "catia.cgr",
            "native_tessellation",
            "CATCGRCont",
            "3",
            PayloadRole.KTessellation,
            ".cgr",
        ),
        (
            "catia.v5.osmx",
            "native_feature_graph",
            "CATPrtCont",
            "1",
            PayloadRole.KFeatureHistory,
            ".osmx",
        ),
        (
            "solidworks.mates",
            "mate-list",
            "solidworks.serialized-object-stream",
            "Mates",
            PayloadRole.KAssemblyStructure,
            ".bin",
        ),
        (
            "freecad.fcstd",
            "native_document",
            "FreeCAD Schema 4",
            "Legacy.FCStd",
            PayloadRole.KDocument,
            ".FCStd",
        ),
        (
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            "V5_CFV2",
            PayloadRole.KVerification,
            ".sha256",
        ),
        ("future.cad", "opaque", "v9", "Data", PayloadRole.KAuxiliary, ".bin"),
    ),
)
def CheckOldPayload(
    FormatId: str,
    KindValue: str,
    SchemaText: str,
    SourceStream: str,
    RoleValue: PayloadRole,
    ExtensionText: str,
) -> None:
    RawValue = ToData(
        BrepPayload(
            "legacy",
            FormatId,
            KindValue,
            SchemaText,
            HashCodec.sha256(b"legacy payload").hexdigest(),
            data=b"legacy payload",
            source_stream=SourceStream,
        )
    )
    assert isinstance(RawValue, dict)
    _ = RawValue.pop("role")
    _ = RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == RoleValue
    assert RestoredPayload.FileExtension == ExtensionText
    assert RestoredPayload.PayloadData == b"legacy payload"
    assert (
        RestoredPayload.SourceDigest == HashCodec.sha256(b"legacy payload").hexdigest()
    )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckPartial() -> None:
    RawValue = ToData(
        BrepPayload(
            "legacy",
            "parasolid",
            "binary",
            "SCH_3500040",
            HashCodec.sha256(b"payload").hexdigest(),
            data=b"payload",
            role=PayloadRole.KAuxiliary,
            file_extension=".custom",
        )
    )
    assert isinstance(RawValue, dict)
    WithoutRole = dict(RawValue)
    _ = WithoutRole.pop("role")
    RestoredRole = FromData(WithoutRole)
    assert isinstance(RestoredRole, BrepPayload)
    RolePayload = RestoredRole
    assert RolePayload.ValueRole == PayloadRole.KBrep
    assert RolePayload.FileExtension == ".custom"
    WithoutExt = dict(RawValue)
    _ = WithoutExt.pop("file_extension")
    RestoredExt = FromData(WithoutExt)
    assert isinstance(RestoredExt, BrepPayload)
    ExtPayload = RestoredExt
    assert ExtPayload.ValueRole == PayloadRole.KAuxiliary
    assert ExtPayload.FileExtension == ".x_b"
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == PayloadRole.KAuxiliary
    assert RestoredPayload.FileExtension == ".custom"
    BindingValue = ToData(
        BrepPayload(
            "binding",
            "catia.v5.sha256",
            "native_document_binding",
            "sha256",
            HashCodec.sha256(b"binding").hexdigest(),
            data=b"binding",
            role=PayloadRole.KDocument,
            file_extension=".bin",
        )
    )
    assert isinstance(BindingValue, dict)
    _ = BindingValue.pop("file_extension")
    RestoredBinding = FromData(BindingValue)
    assert isinstance(RestoredBinding, BrepPayload)
    BindingPayload = RestoredBinding
    assert BindingPayload.ValueRole == PayloadRole.KDocument
    assert BindingPayload.FileExtension == ".sha256"


# behavior coverage protects portable interchange semantics during structural refactors
def CheckUnknown() -> None:
    RawValue = ToData(
        BrepPayload(
            "unknown",
            "future.cad",
            "opaque",
            "v9",
            HashCodec.sha256(b"unknown").hexdigest(),
            data=b"unknown",
            source_stream="Container/Opaque.future",
        )
    )
    assert isinstance(RawValue, dict)
    _ = RawValue.pop("role")
    _ = RawValue.pop("file_extension")
    RestoredValue = FromData(RawValue)
    assert isinstance(RestoredValue, BrepPayload)
    RestoredPayload = RestoredValue
    assert RestoredPayload.ValueRole == PayloadRole.KAuxiliary
    assert RestoredPayload.FileExtension == ".future"
    assert RestoredPayload.PayloadData == b"unknown"


# behavior coverage protects portable interchange semantics during structural refactors
def CheckAllCaps() -> None:
    Capabilities = frozenset(Capability)
    RestoredValue = CadDocument.from_json(
        ReplaceValue(BuildDocument(), capabilities=Capabilities).to_json()
    )
    assert RestoredValue.capabilities == Capabilities
