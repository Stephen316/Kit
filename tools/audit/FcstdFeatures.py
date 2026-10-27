# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, TypeGuard, cast


# feature records need only the stable fields used by unsupported grammar reporting
class FeaturePayload(Protocol):

    # audit metadata must remain readable across immutable feature implementations
    @property
    def attributes(self) -> Mapping[str, object]: ...  # lgtm[py/ineffectual-statement]

    # unsupported grammar reporting accepts every concrete feature kind representation
    @property
    def kind(self) -> object: ...  # lgtm[py/ineffectual-statement]


# documents expose this narrow timeline contract so audit code avoids parser implementation details
class DocumentPayload(Protocol):

    # read only sequencing permits concrete feature timelines through covariance
    @property
    def feature_timeline(
        self,
    ) -> Sequence[FeaturePayload]: ...  # lgtm[py/ineffectual-statement]


# decoded extension metadata needs validated keys before typed lookups can be trusted
def HasKeyedStrings(ValueData: object) -> TypeGuard[Mapping[str, object]]:
    if not isinstance(ValueData, Mapping):
        return False
    CandidateData = cast(Mapping[object, object], ValueData)
    return all(isinstance(KeyData, str) for KeyData in CandidateData)


# feature identity exposes unsupported grammar without relying on unstable source filenames
def FeatureTypes(DocumentData: DocumentPayload) -> tuple[str, ...]:
    TypeNames: set[str] = set()
    for FeatureData in DocumentData.feature_timeline:
        FreecadData: object = FeatureData.attributes.get("freecad")
        TypeName = (
            FreecadData.get("type_id", "") if HasKeyedStrings(FreecadData) else ""
        )
        TypeNames.add(str(TypeName or FeatureData.kind))
    return tuple(sorted(TypeNames))
