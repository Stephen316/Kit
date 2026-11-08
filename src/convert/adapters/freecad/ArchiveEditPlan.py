# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditableExt import EditExtrude, ReadEditExtrude
from interchange.document.models.DocumentModel import CadDocument


# only the final timeline step can take ownership of the document shape
def ReadArchiveEdit(DocValue: CadDocument | None) -> tuple[str, EditExtrude] | None:
    if DocValue is None or not DocValue.feature_timeline:
        return None
    FeatureValue = DocValue.feature_timeline[-1]
    PlanValue = ReadEditExtrude(DocValue, FeatureValue)
    return (FeatureValue.id, PlanValue) if PlanValue is not None else None
