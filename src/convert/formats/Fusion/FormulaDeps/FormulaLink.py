from dataclasses import replace as Replace

from convert.formats.Fusion.FormulaDeps.FormulaGraph import GetFormulaGraph
from convert.formats.Fusion.FormulaDeps.FormulaOrder import GetProvenLinks
from convert.formats.Fusion.FormulaDeps.ScopedParams import ReadPartNames
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.records.RecordParameter import Parameter


# unsupported scope or arithmetic leaves original formula text and values intact
def LinkFormulaDeps(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    Parameters: tuple[Parameter, ...],
) -> tuple[Parameter, ...]:
    if not any(Param.expression is not None for Param in Parameters):
        return Parameters
    try:
        Names = ReadPartNames(BulkData, Spans, History)
    except ValueError:
        return Parameters
    Registry = {
        f"fusion-parameter-{NativeId}": NameValue
        for NativeId, NameValue in Names.items()
    }
    if Registry != {Param.id: Param.name for Param in Parameters}:
        return Parameters
    Links = GetProvenLinks(GetFormulaGraph(Parameters))
    return tuple(
        (
            Replace(
                Param,
                expression=Replace(Param.expression, parameter_ids=Links[Param.id]),
            )
            if Param.id in Links and Param.expression is not None
            else Param
        )
        for Param in Parameters
    )
