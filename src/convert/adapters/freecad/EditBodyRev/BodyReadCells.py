# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import BodyRevPlan
from convert.adapters.freecad.EditRead.EditSheet import ReadCellText
from convert.adapters.freecad.EditRead.Revolve.RevSheet import (
    ReadRevCells,
    ReadRevLiteral,
)
from convert.adapters.freecad.Native import NativeObject
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import Parameter
from interchange.serialization.EncodeData import ToData


# only the authored signed depth and angle may differ while the unused taper stays zero
def ReadBodyCells(
    Sheet: NativeObject, Params: tuple[Parameter, ...], Plan: BodyRevPlan, Depth: float
) -> tuple[tuple[float, str], tuple[float, str], str]:
    Aliases = ParamCatalog(Items(ToData(Params))).Aliases
    Cells = ReadRevCells(Sheet, Params, Aliases)
    DepthId, AlongId = Plan.Extrude.ParameterId, Plan.Revolve.AngleParamId
    DepthAlias = Aliases[DepthId]
    DepthText = ReadCellText(Cells, DepthAlias, ValueKind.KLength, Depth, "mm")
    AlongText = Cells[Aliases[AlongId]].get("content", "")
    ById = {Value.id: Value for Value in Params}
    Along = ReadRevLiteral(AlongText, ById[AlongId])
    for Identity in ById.keys() - {DepthId, AlongId}:
        Taper, _ = ReadRevLiteral(
            Cells[Aliases[Identity]].get("content", ""), ById[Identity]
        )
        if Taper != 0.0:
            raise ValueError("FreeCAD editable body axis source taper changed")
    return (Depth, DepthText), Along, f"Parameters.{DepthAlias}"
