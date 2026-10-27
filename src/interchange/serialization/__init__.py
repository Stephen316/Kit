# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig

from interchange.compatibility.PublicMetadata import BindFunctionMut
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from interchange.serialization.MigrationRegistry import RegMigration
from interchange.serialization.TypeRegistry import KTypeRegistry as RegisteredTypes
from interchange.serialization.TypeRegistry import RegisterTypes

BindFunctionMut(
    DumpJson,
    __name__,
    "dumps",
    {
        "value": "object",
        "indent": "int | None",
        "return": "str",
    },
    FuncSig(
        (
            FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="object"),
            FuncParam(
                "indent",
                FuncParam.KEYWORD_ONLY,
                default=2,
                annotation="int | None",
            ),
        ),
        return_annotation="str",
    ),
    globals(),
)
BindFunctionMut(
    FromData,
    __name__,
    "from_data",
    {
        "value": "object",
        "return": "object",
    },
    FuncSig(
        (FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="object"),),
        return_annotation="object",
    ),
    globals(),
)
BindFunctionMut(
    LoadJson,
    __name__,
    "loads",
    {
        "source": "str",
        "return": "object",
    },
    FuncSig(
        (FuncParam("source", FuncParam.POSITIONAL_OR_KEYWORD, annotation="str"),),
        return_annotation="object",
    ),
    globals(),
)
BindFunctionMut(
    RegMigration,
    __name__,
    "register_migration",
    {
        "target": "type",
        "migration": "Callable[[Mapping[str, object]], Mapping[str, object]]",
        "return": "None",
    },
    FuncSig(
        (
            FuncParam("target", FuncParam.POSITIONAL_OR_KEYWORD, annotation="type"),
            FuncParam(
                "migration",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Callable[[Mapping[str, object]], Mapping[str, object]]",
            ),
        ),
        return_annotation="None",
    ),
    globals(),
)
BindFunctionMut(
    RegisterTypes,
    __name__,
    "register_types",
    {
        "types": "type",
        "return": "None",
    },
    FuncSig(
        (FuncParam("types", FuncParam.VAR_POSITIONAL, annotation="type"),),
        return_annotation="None",
    ),
    globals(),
)
BindFunctionMut(
    ToData,
    __name__,
    "to_data",
    {
        "value": "object",
        "return": "WireData",
    },
    FuncSig(
        (FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="object"),),
        return_annotation="WireData",
    ),
    globals(),
)

dumps = DumpJson
from_data = FromData
KTypeRegistry = RegisteredTypes
loads = LoadJson
register_migration = RegMigration
register_types = RegisterTypes
to_data = ToData


# serialization consumers need one intentional historical public contract
__all__ = (
    "dumps",
    "from_data",
    "loads",
    "register_migration",
    "register_types",
    "to_data",
)
