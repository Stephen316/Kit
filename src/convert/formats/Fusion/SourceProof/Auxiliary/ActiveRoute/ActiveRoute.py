# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.RecordSpan import RecordSpan


# each route keeps its act field extent separate from its design or act owner extent
@MakeDataClass(frozen=True, slots=True)
class ActiveRoute:
    Key: str
    Prefix: int
    FieldsSpan: RecordSpan
    OwnerSpan: RecordSpan | None
    Residual: int

    # unresolved fields and unknown namespaces cannot be reported as closed routes
    @property
    def IsResolved(self) -> bool:
        return self.OwnerSpan is not None and self.Residual == 0
