# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections import Counter
from typing import TypedDict

from tools.audit.FcstdResult import AuditRecord


# report consumers need a stable aggregate shape independent from individual audit records
class AuditSummary(TypedDict):
    files: int
    application_usable: int
    vendor_loadable: int
    vendor_only: int
    near_lossless: int
    errors: int
    unsupported_feature_types: dict[str, int]
    vendor_only_feature_types: dict[str, int]


# aggregate verdicts retain unsupported families so research can prioritize measured gaps
def BuildSummary(ResultsData: tuple[AuditRecord, ...]) -> AuditSummary:
    UnsupportedTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if not ResultData["vendor_loadable"]
        for TypeName in ResultData["feature_types"]
    )
    VendorOnlyTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if ResultData["vendor_loadable"] and not ResultData["application_usable"]
        for TypeName in ResultData["feature_types"]
    )
    return {
        "files": len(ResultsData),
        "application_usable": sum(
            bool(ResultData["application_usable"]) for ResultData in ResultsData
        ),
        "vendor_loadable": sum(
            bool(ResultData["vendor_loadable"]) for ResultData in ResultsData
        ),
        "vendor_only": sum(
            bool(ResultData["vendor_loadable"])
            and not bool(ResultData["application_usable"])
            for ResultData in ResultsData
        ),
        "near_lossless": sum(
            bool(ResultData["near_lossless"]) for ResultData in ResultsData
        ),
        "errors": sum(bool(ResultData["error"]) for ResultData in ResultsData),
        "unsupported_feature_types": dict(sorted(UnsupportedTypes.items())),
        "vendor_only_feature_types": dict(sorted(VendorOnlyTypes.items())),
    }
