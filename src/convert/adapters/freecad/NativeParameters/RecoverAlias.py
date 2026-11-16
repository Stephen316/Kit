from collections import Counter
from dataclasses import replace as Replace

from convert.adapters.freecad.NativeParameters.ReadSheet import ReadSheet
from convert.adapters.freecad.NativeParameters.ResolveAlias import ResolveAlias
from interchange.document.Models.DocumentCaps import InferCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordDiagnostic import Diagnostic


# native replay and public reads must recover the same complete bounded parameter observations
def RecoverAlias(Document: CadDocument) -> CadDocument:
    try:
        if len(Document.parameters) > 16384:
            raise OverflowError("parameter_limit")
        Aliases, Findings = ReadSheet(Document)
    except (ValueError, OverflowError) as Problem:
        return Replace(
            Document,
            diagnostics=(
                *Document.diagnostics,
                Diagnostic(
                    "freecad.sheet_alias.unresolved",
                    "Native spreadsheet alias recovery was bounded or unsupported",
                    attributes={"counts": {str(Problem): 1}},
                ),
            ),
        )
    Existing = {Param.id: Param for Param in Document.parameters}
    IdCounts = Counter(Param.id for Param in Aliases.values())
    Valid = {
        AliasKey: Param
        for AliasKey, Param in Aliases.items()
        if IdCounts[Param.id] == 1
        and (Param.id not in Existing or Existing[Param.id] == Param)
    }
    Issues = Counter(Findings)
    if len(Valid) != len(Aliases):
        Issues["parameter_identity_collision"] += len(Aliases) - len(Valid)
    Results = tuple(ResolveAlias(Param, Valid) for Param in Document.parameters)
    Issues.update(Reason for _, Reason in Results if Reason)
    Added = {Param.id: Param for Param in Valid.values() if Param.id not in Existing}
    Parameters = tuple(Param for Param, _ in Results) + tuple(
        Added[AliasKey] for AliasKey in sorted(Added)
    )
    Diagnostics = Document.diagnostics
    if Issues:
        Diagnostics += (
            Diagnostic(
                "freecad.sheet_alias.unresolved",
                "Some native spreadsheet references remain unresolved",
                attributes={"counts": dict(sorted(Issues.items()))},
            ),
        )
    Result = Replace(Document, parameters=Parameters, diagnostics=Diagnostics)
    Result = Replace(
        Result,
        capabilities=Result.capabilities | InferCaps(Result, roundtrip_metadata=True),
    )
    Result.assert_valid()
    return Result
