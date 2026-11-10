# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.AssemblyHistory import ReadAsmHistory
from convert.formats.Fusion.Assembly.AssemblyProject import ProjectAssembly
from convert.formats.Fusion.Assembly.NativeAssembly import ReadNativeAsm
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.document.models.DocumentModel import AssemblyData
from interchange.records.RecordDiagnostic import Diagnostic


# automatic assembly routing keeps explicit part history selection available for unsupported graphs
def ReadAsmProject(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], Parts: tuple[HistoryPart, ...]
) -> tuple[AssemblyData | None, HistoryPart | None, tuple[Diagnostic, ...]]:
    try:
        Native = ReadNativeAsm(BulkData, Spans)
        if Native is None:
            return None, None, ()
        Histories = ReadAsmHistory(BulkData, Spans, Native, Parts)
        return (
            ProjectAssembly(Native, Spans, Histories),
            Histories[Native.RootComponentId],
            (
                Diagnostic(
                    code="fusion.assembly.partial",
                    message="Fusion local definitions and occurrence placements are available. "
                    + "Additional component geometry and assembly editing semantics require further decoding.",
                ),
            ),
        )
    except ValueError as ErrorInfo:
        if len(Parts) != 1:
            raise ValueError(
                f"{ErrorInfo}. Select exactly one Fusion history. Available IDs: "
                + f"{tuple(PartValue.HistoryId for PartValue in Parts)}"
            ) from ErrorInfo
        return (
            None,
            None,
            (Diagnostic(code="fusion.assembly.unsupported", message=str(ErrorInfo)),),
        )
