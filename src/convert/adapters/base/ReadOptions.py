# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from typing import Mapping as TypeMap

from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase


# read policy stays immutable so adapters receive consistent filtering and validation intent
@DataClass(frozen=True, slots=True)
class ReadOptions(ContractBase):
    configuration: str | None = None
    include_brep: bool = True
    include_tessellation: bool = True
    strict: bool = True
    values: TypeMap[str, object] = DataField(default_factory=FreezeMapping)

    # historical configuration access remains typed because readers consume this public selection field
    @property
    def ConfigName(self) -> str | None:
        return self.configuration

    # historical brep access remains typed because readers consume this public filtering field
    @property
    def IncludeBrep(self) -> bool:
        return self.include_brep

    # historical tessellation access remains typed because readers consume this public filtering field
    @property
    def IncludeMesh(self) -> bool:
        return self.include_tessellation

    # historical strictness access remains typed because readers consume this public validation field
    @property
    def StrictMode(self) -> bool:
        return self.strict

    # historical option access remains typed because adapters consume this public extension field
    @property
    def OptionValues(self) -> TypeMap[str, object]:
        return self.values
