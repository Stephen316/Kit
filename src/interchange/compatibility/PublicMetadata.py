# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from inspect import Signature as FuncSig
from typing import Mapping as TypeMap


# relocated definitions retain historical module identities for reflection and pickle compatibility
def BindModules(TargetValues: tuple[object, ...], ModuleName: str) -> None:
    for TargetValue in TargetValues:
        setattr(TargetValue, "__module__", ModuleName)


# renamed public definitions retain historical names without constraining compliant implementation identifiers
def BindNameMut(
    TargetValue: object,
    ModuleName: str,
    LegacyName: str,
    ModuleScope: dict[str, object],
) -> None:
    setattr(TargetValue, "__name__", LegacyName)
    setattr(TargetValue, "__qualname__", LegacyName)
    setattr(TargetValue, "__module__", ModuleName)
    ModuleScope[LegacyName] = TargetValue


# relocated public functions retain their historical reflection contract and import surface
def BindFunctionMut(
    TargetFunc: object,
    ModuleName: str,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
    ModuleScope: dict[str, object],
) -> None:
    BindNameMut(TargetFunc, ModuleName, LegacyName, ModuleScope)
    setattr(TargetFunc, "__annotations__", dict(AnnotationMap))
    setattr(TargetFunc, "__signature__", SignatureInfo)
