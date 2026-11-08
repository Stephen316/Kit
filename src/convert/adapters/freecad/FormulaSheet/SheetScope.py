# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectMap
from convert.adapters.freecad.FormulaSheet.FormulaPlans import ReadFusionRows
from interchange.records.RecordConfig import Configuration
from interchange.serialization.Deserialize import FromData

# no other modeled entities may depend on cells in the standalone workbook
KModelCollections = (
    "support_planes",
    "sketches",
    "selections",
    "feature_timeline",
    "bodies",
    "meshes",
)

# these alternate document fields may still be interpreted by the archive writer
KAlternateCollections = ("planes", "timeline", "native_payloads")


# projected parameters use canonical wire tuples rather than arbitrary native records
def ReadSheetItems(Value: object) -> tuple[object, ...] | None:
    if not IsObjectMap(Value) or set(Value) != {"$tuple"}:
        return None
    Records = Value["$tuple"]
    return (
        tuple(CastValue(list[object], Records)) if isinstance(Records, list) else None
    )


# an editable workbook can retain only the original fusion document carrier
def HasSheetPayload(Manifest: Mapping[str, object]) -> bool:
    Payloads = ReadSheetItems(Manifest.get("brep_payloads"))
    if Payloads is None or len(Payloads) > 1:
        return False
    return all(
        IsObjectMap(Value)
        and Value.get("$type") == "BrepPayload"
        and Value.get("format_id") == "fusion.f3d"
        and Value.get("kind") == "native_document"
        and Value.get("role") == {"$enum": "PayloadRole", "value": "document"}
        for Value in Payloads
    )


# the standard fusion history configuration carries no separate parameter values
def HasSheetConfig(Manifest: Mapping[str, object]) -> bool:
    Records = ReadSheetItems(Manifest.get("configurations"))
    if Records is None or len(Records) != 1:
        return False
    try:
        Config = FromData(Records[0])
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False
    return (
        isinstance(Config, Configuration)
        and Config.id == "fusion-projection"
        and Config.name == "History projection"
        and Config.active
        and not (
            Config.parent_id
            or Config.overrides
            or Config.suppressed_feature_ids
            or Config.attributes
        )
    )


# opaque modeling records cannot be inferred from an otherwise empty neutral timeline
def HasNoSheetModel(Manifest: Mapping[str, object]) -> bool:
    if (
        Manifest.get("assembly") is not None
        or Manifest.get("brep") is not None
        or any(
            ReadSheetItems(Manifest.get(KeyName)) != () for KeyName in KModelCollections
        )
        or any(KeyName in Manifest for KeyName in KAlternateCollections)
    ):
        return False
    Metadata = Manifest.get("metadata")
    if not IsObjectMap(Metadata) or Metadata.get("freecad"):
        return False
    if any(
        KeyName in Metadata and ReadSheetItems(Metadata[KeyName]) != ()
        for KeyName in ("fusion.history_entries", "fusion.history_groups")
    ):
        return False
    Inventory = Metadata.get("fusion.body_inventory")
    if Inventory is not None and (
        not IsObjectMap(Inventory) or ReadSheetItems(Inventory.get("members")) != ()
    ):
        return False
    Diagnostics = ReadSheetItems(Manifest.get("diagnostics"))
    return Diagnostics is not None and not any(
        IsObjectMap(Value)
        and Value.get("code")
        in ("fusion.parameter.unsupported", "fusion.parameter.binding")
        for Value in Diagnostics
    )


# the marker is only written when every source parameter has a complete native expression
def CanEditSheet(
    Manifest: Mapping[str, object],
    ParameterRows: list[dict[str, object]],
    NativeExpressions: Mapping[str, str],
) -> bool:
    Source = Manifest.get("source")
    if (
        Manifest.get("$type") != "CadDocument"
        or not IsObjectMap(Source)
        or Source.get("$type") != "CadSource"
        or Source.get("format_id") != "fusion.f3d"
        or Manifest.get("units") != {"$enum": "UnitSystem", "value": "mm"}
        or not HasNoSheetModel(Manifest)
        or not HasSheetPayload(Manifest)
        or not HasSheetConfig(Manifest)
        or ReadSheetItems(Manifest.get("parameters")) != tuple(ParameterRows)
        or len(ParameterRows) < 2
        or any(
            Value.get("owner_id") != ""
            or Value.get("role") != {"$enum": "ParameterRole", "value": "driving"}
            for Value in ParameterRows
        )
    ):
        return False
    TypedRows = ReadFusionRows(ParameterRows)
    return (
        len(TypedRows) == len(ParameterRows)
        and TypedRows.keys() == NativeExpressions.keys()
        and any(
            Value.expression is not None and Value.expression.parameter_ids
            for Value in TypedRows.values()
        )
    )
