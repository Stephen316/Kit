# A controller success can fail during locale encoding

## Expectation

The controller returns a usable claim acknowledgement and exit code zero after committing a claim.
Unicode store paths, claim paths and worker reasons remain the same when the A03 adapter reads the response.

## Source-observed boundary

The controller leaves its `Ledger` context before publishing a successful response.
That context commits metadata, and the claim command has already written its claim file as UTF-8.
The old `print(canonical(response))` then used stdout's locale encoding.
A combining character in `claim_file` could cause an encoding exception after the running attempt and its lease were committed.
The caller could receive an error despite the claim file and committed attempt being present.
The adapter also used locale-dependent decoding for both captured streams, so incompatible decoding could reject or alter a Unicode response.

This finding comes from source inspection, not a local reproduction or a newly observed licensed run.
The earlier [history audit encoding failure](../../Ci/Commands/HistoryAuditOutputEncoding.md) records a separate observed Windows stdout failure with a combining character.

## Repair and remaining boundary

Use the [explicit controller UTF-8 transport](../../../Changes/Research/Controller/ControllerUtfEightTransport.md).
Successful responses retain canonical JSON bytes and one LF; stderr diagnostics use UTF-8 as well.
The actual adapter decodes both streams strictly as UTF-8.
No logical record, byte limit, hash definition, transaction or return code changes.

This removes locale encoding as the failure mechanism; it does not guarantee delivery after commit.
A broken pipe, interruption or other I/O failure can still lose the acknowledgement.
Inspect the original durable claim and controller state before inferring that a command failed to commit or issuing replacement work.
The [artifact publication gotcha](../ArtifactPublicationOutlivesRollback.md) records the separate boundary between immutable files and metadata rollback.

Real-process cases cover Unicode claim acknowledgements, exact UTF-8 output, genuine output-intake refusal, a usable lease and one completed attempt under ASCII stdout settings.
Local verification remains static; hosted execution is required.
