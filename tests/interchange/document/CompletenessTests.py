# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from dataclasses import replace as ReplaceValue
from enum import Enum as EnumBase
from importlib import import_module as ImportModule
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints
from typing import cast as CastValue
import pytest as PytestLib
from interchange import geometry as GeometryModule
from interchange import (
    AssemblyData,
    CadDocument,
    CadSource,
    Capability,
    ComponentKind,
    FeatureDefinition,
    FeatureStep,
    PayloadRole,
    Selection,
    SelectionPathElement,
)
from interchange.document.models.DocumentCaps import InferCaps
from interchange.document.models.DocumentIdentity import GetIdFields
from interchange.geometry import Geometry
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.Wire import GetWireField
from tests.interchange.document.DocumentTests import BuildDocument

# dynamic package loading lets reflection inspect the facade without mixed import forms
KInterchangeApi = ImportModule("interchange")


# behavior coverage protects portable interchange semantics during structural refactors
@DataClass(frozen=True, slots=True)
class FutureFeature(FeatureDefinition):
    ItemValue: str


# behavior coverage protects portable interchange semantics during structural refactors
def GetExpectedIds(ValueType: type[CadDocument] | type[AssemblyData]) -> set[str]:
    TypeHints = GetTypeHints(ValueType)
    ResultValue: set[str] = set()
    for FieldName, FieldHint in TypeHints.items():
        TypeArgs = GetTypeArgs(FieldHint)
        if (
            GetTypeOrigin(FieldHint) is tuple
            and len(TypeArgs) == 2
            and (TypeArgs[1] is Ellipsis)
            and isinstance(TypeArgs[0], type)
            and IsDataClass(TypeArgs[0])
            and any(
                (
                    GetWireField(MemberField.name, TypeArgs[0]) == "id"
                    for MemberField in GetFields(TypeArgs[0])
                )
            )
        ):
            ResultValue.add(FieldName)
    return ResultValue


# behavior coverage protects portable interchange semantics during structural refactors
def CheckIdFields() -> None:
    for ValueType in (CadDocument, AssemblyData):
        assert {NameValue for NameValue, _ in GetIdFields(ValueType)} == GetExpectedIds(
            ValueType
        )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckGeometry() -> None:
    ExpectedValues = {
        ItemValue
        for NameValue, ItemValue in vars(GeometryModule).items()
        if NameValue.endswith(("Geometry", "Geom"))
        and isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
    }
    assert set(GetTypeArgs(Geometry)) == ExpectedValues


# behavior coverage protects portable interchange semantics during structural refactors
def CheckFeatures() -> None:
    DefinitionHint = GetTypeHints(FeatureStep)["definition"]
    assert set(GetTypeArgs(DefinitionHint)) == {FeatureDefinition, type(None)}
    Definitions = {
        ItemValue
        for ItemValue in vars(KInterchangeApi).values()
        if isinstance(ItemValue, type)
        and IsDataClass(ItemValue)
        and issubclass(ItemValue, FeatureDefinition)
    }
    assert Definitions
    StepValue = ReplaceValue(
        BuildDocument().feature_timeline[0], definition=FutureFeature("future")
    )
    assert isinstance(StepValue.definition, FeatureDefinition)
    with PytestLib.raises(TypeError, match="feature definition"):
        _ = ReplaceValue(
            StepValue,
            definition=CastValue(FeatureDefinition, {"type": "unregistered"}),
        )


# behavior coverage protects portable interchange semantics during structural refactors
def CheckEnums() -> None:
    EnumTypes = {
        ItemValue
        for NameValue, ItemValue in vars(KInterchangeApi).items()
        if not NameValue.startswith("_")
        and isinstance(ItemValue, type)
        and issubclass(ItemValue, EnumBase)
    }
    assert EnumTypes
    for EnumType in EnumTypes:
        assert tuple(EnumType.__members__.values()) == tuple(EnumType)
        assert len({MemberField.value for MemberField in EnumType}) == len(EnumType)


# historical constructors must remain usable while adapters migrate independently
def CheckLegacyKeys() -> None:
    PathValue = SelectionPathElement(
        entity_kind="feature",
        entity_id="feature:one",
        subelement="Face1",
    )
    SelectionValue = Selection(
        id="selection:one",
        name="Selection",
        path=(PathValue,),
    )
    SourceValue = CadSource(
        format_id="test",
        path="source.FCStd",
        sha256="1" * 64,
    )
    assert SelectionValue.SelectionPath == (PathValue,)
    assert SourceValue.FilePath == "source.FCStd"
    assert SelectionValue.path == (PathValue,)
    assert SourceValue.path == "source.FCStd"
    ReplacedSource = ReplaceValue(SourceValue, path="updated.FCStd")
    assert ReplacedSource.FilePath == "updated.FCStd"
    ReplacedDoc = ReplaceValue(BuildDocument(), metadata={"compatibility": "preserved"})
    assert ReplacedDoc.metadata == {"compatibility": "preserved"}


# serialization keys stay byte compatible so stored interchange documents remain readable
def CheckWireFields() -> None:
    PathValue = SelectionPathElement("feature", "feature:one", "Face1")
    SelectionValue = Selection("selection:one", "Selection", (PathValue,))
    RawValue = ToData(SelectionValue)
    assert isinstance(RawValue, dict)
    assert "path" in RawValue
    assert "selection_path" not in RawValue
    PathTuple = RawValue["path"]
    assert isinstance(PathTuple, dict)
    PathItems = PathTuple["$tuple"]
    assert isinstance(PathItems, list)
    PathData = PathItems[0]
    assert isinstance(PathData, dict)
    assert PathData["entity_kind"] == "feature"
    assert PathData["entity_id"] == "feature:one"
    assert FromData(RawValue) == SelectionValue


# old capability keywords remain supported because converter modules upgrade independently
def CheckLegacyCaps() -> None:
    SourceValue = BuildDocument()
    assert InferCaps(SourceValue, roundtrip_metadata=True) == InferCaps(
        SourceValue,
        RoundtripMeta=True,
    )


# historical enum attributes stay available without becoming duplicate enum members
def CheckOldEnums() -> None:
    LegacyCapability: object = Capability.KRoundtripMeta
    LegacyComponent: object = ComponentKind.KAssembly
    LegacyPayload: object = PayloadRole.KBrep
    assert Capability.ROUNDTRIP_METADATA is LegacyCapability
    assert ComponentKind.ASSEMBLY is LegacyComponent
    assert PayloadRole.BREP is LegacyPayload


# historical json options remain accepted because document consumers upgrade independently
def CheckLegacyJson() -> None:
    SourceValue = BuildDocument()
    LegacyJson = SourceValue.to_json
    assert callable(LegacyJson)
    assert LegacyJson(indent=None) == SourceValue.to_json(indent=None)


# historical field access takes precedence over similarly named document lookup methods
def CheckFieldAlias() -> None:
    SourceValue = BuildDocument()
    FeatureValue = SourceValue.feature_timeline[0]
    assert FeatureValue.definition is FeatureValue.Definition
