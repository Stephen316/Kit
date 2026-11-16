# Pinned capture commits can retain vendor software

## Expectation

Removing vendor DLLs from the current tree can appear sufficient to make a research branch distributable.
A single source-equivalent squash can appear to preserve every research input.

## Actual behavior

The incoming-history policy inspects additions throughout the PR's commit range.
The [hosted path failure](https://github.com/TryUniCAD/Kit/actions/runs/43927281489/job/133509981266) therefore remains after the final tree removes the DLL paths.
The capture revision `466dcb172dfa3803463e07ccde963ba01671d200` itself contains these paths:

- `re/binaries/sldarchiveu.dll`
- `re/binaries/sldmfcu.dll`
- `re/binaries/sldmodu.dll`
- `re/binaries/swccu.dll`

The paired-capture intake reads pinned trees, capture introductions and preceding object inventories.
Other archive verifiers also read inputs through this capture revision.
A source-equivalent squash does not retain those Git ancestry and object dependencies in a fresh clone.
An unchanged current file is separate evidence from its original introduction history.

## Workaround

Use the [history input audit](../../Changes/Research/Controller/HistoryInputAudit.md) to identify literal pins and compare retained capture object IDs.
Preserve existing evidence and current checks while preparing a reviewed remediation.
Do not copy the vendor payloads into a replacement artifact.
Do not substitute a new provenance claim for the original without independent verification.
History rewriting requires separate authorization under the repository workflow.
The audit does not grant that authorization or clear the incoming-history gate.
