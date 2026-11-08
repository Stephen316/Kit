# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.AssemblyHistory import ResolveAssemblyHistories
from convert.formats.Fusion.Assembly.AssemblyProject import ProjectAssembly
from convert.formats.Fusion.Assembly.NativeAssembly import ReadNativeAssembly
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.document.models.DocumentModel import AssemblyData
from interchange.records.RecordDiagnostic import Diagnostic


# automatic assembly routing keeps explicit part history selection available for unsupported graphs
def ReadAssemblyProjection(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], Parts: tuple[HistoryPart, ...]
) -> tuple[AssemblyData | None, HistoryPart | None, tuple[Diagnostic, ...]]:
    try:
        Native = ReadNativeAssembly(BulkData, Spans)
        if Native is None:
            return None, None, ()
        Histories = ResolveAssemblyHistories(BulkData, Spans, Native, Parts)
        return (
            ProjectAssembly(Native, Spans, Histories),
            Histories[Native.RootComponentId],
            (
                Diagnostic(
                    code="fusion.assembly.partial",
                    message="Fusion local definitions and occurrence placements are available. "
                    "Additional component geometry and assembly editing semantics require further decoding.",
                ),
            ),
        )
    except ValueError as ErrorInfo:
        if len(Parts) != 1:
            raise ValueError(
                f"{ErrorInfo}. Select exactly one Fusion history from "
                f"{tuple(Part.HistoryId for Part in Parts)}"
            ) from ErrorInfo
        return (
            None,
            None,
            (Diagnostic(code="fusion.assembly.unsupported", message=str(ErrorInfo)),),
        )
