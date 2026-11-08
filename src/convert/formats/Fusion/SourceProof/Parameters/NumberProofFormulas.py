# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.FormulaDeps.FormulaGraph import GetFormulaGraph
from convert.formats.Fusion.FormulaDeps.FormulaOrder import GetProvenLinks
from convert.formats.Fusion.SourceProof.Parameters.NumberProofRow import NumberProofRow
from convert.geometry.Formula.FormulaUnits import GetQuantity


# exact linked names and a verified dependency closure protect against cached formula coincidences
def ReadProvenNumbers(Rows: tuple[NumberProofRow, ...]) -> tuple[NumberProofRow, ...]:
    Graph = GetFormulaGraph(tuple(Row.Raw for Row in Rows))
    Edges = {}
    for Row in Rows:
        Expression = Row.Actual.expression
        Identity = Row.Raw.id
        if Expression is None and GetQuantity(Row.Raw.value) is not None:
            Edges[Identity] = ()
        elif Expression is not None and Graph.get(Identity) == Expression.parameter_ids:
            Edges[Identity] = Expression.parameter_ids
    Proven = GetProvenLinks(Edges)
    return tuple(
        Row for Row in Rows if Edges.get(Row.Raw.id) == () or Row.Raw.id in Proven
    )
